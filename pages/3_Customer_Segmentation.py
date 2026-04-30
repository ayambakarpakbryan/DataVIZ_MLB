"""
=============================================================================
DVD Rental Analysis Dashboard
Market & Geographic Performance
=============================================================================
Author: [Your Name]
Course: Data Visualization
Dataset: PostgreSQL dvdrental
=============================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import warnings

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0d0f14; color: #e8e8e8; }

    section[data-testid="stSidebar"] {
        background: #13161e !important;
        border-right: 1px solid #1f2333;
    }
    section[data-testid="stSidebar"] * { color: #c9cdd8 !important; }

    div[data-testid="metric-container"] {
        background: #181b26;
        border: 1px solid #252a3a;
        border-radius: 12px;
        padding: 20px 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }
    div[data-testid="metric-container"] label {
        color: #7c8299 !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f0c040 !important;
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.2rem;
    }
    .section-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.6rem;
        color: #f0c040;
        letter-spacing: 0.05em;
        margin-bottom: 0.2rem;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #1f2333;
        margin: 0.4rem 0 1.2rem 0;
    }
    .insight-box {
        background: #181b26;
        border-left: 3px solid #f0c040;
        border-radius: 0 8px 8px 0;
        padding: 12px 18px;
        margin: 10px 0 20px 0;
        font-size: 0.85rem;
        color: #b0b5c8;
        line-height: 1.65;
    }
    .insight-box strong { color: #f0c040; }
    .header-banner {
        background: linear-gradient(135deg, #0d0f14 0%, #1a1e2e 50%, #0d0f14 100%);
        border: 1px solid #252a3a;
        border-radius: 16px;
        padding: 32px 40px;
        margin-bottom: 32px;
        text-align: center;
    }
    .header-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3rem;
        color: #f0c040;
        letter-spacing: 0.06em;
        line-height: 1;
        margin: 0;
    }
    .header-sub {
        color: #7c8299;
        font-size: 0.9rem;
        margin-top: 8px;
        letter-spacing: 0.04em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# PLOTLY CONSTANTS
# ATURAN: Semua warna harus 6-digit hex (#rrggbb) atau rgba().
# Plotly TIDAK mendukung 8-digit hex (#rrggbbaa) — gunakan rgba() untuk transparansi.
# ─────────────────────────────────────────────
PLOTLY_TEMPLATE  = "plotly_dark"
PLOT_BG          = "#181b26"
PAPER_BG         = "#181b26"
ACCENT           = "#f0c040"
GRID_COLOR       = "#252a3a"
TREND_COLOR      = "rgba(255,255,255,0.13)"  # ✅ was '#ffffff22' — 8-digit hex tidak valid
MARKER_BORDER    = "rgba(255,255,255,0.13)"  # ✅ was '#ffffff20' — 8-digit hex tidak valid


def style_fig(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family="Inter", color="#c9cdd8"),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


@st.cache_resource(show_spinner="🔌 Connecting to database…")
def get_engine():
    # Make sure to put your actual postgres password here!
    return create_engine("postgresql://postgres:12345@localhost:5432/dvdrental_analytics")


# ─────────────────────────────────────────────
# QUERY HELPERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_all_countries() -> list:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT DISTINCT country FROM country ORDER BY country;")
        )
        return [row[0] for row in result]


@st.cache_data(ttl=600, show_spinner=False)
def fetch_date_range() -> tuple:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT MIN(rental_date)::date, MAX(rental_date)::date FROM rental;")
        ).fetchone()
        return row[0], row[1]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_geo_data(countries: tuple, date_start: str, date_end: str) -> pd.DataFrame:
    engine = get_engine()
    country_clause = ""
    params: dict = {"date_start": date_start, "date_end": date_end}
    if countries:
        country_clause = "AND co.country IN :countries"
        params["countries"] = countries

    query = text(f"""
        SELECT
            co.country,
            COUNT(DISTINCT cu.customer_id)   AS total_customers,
            COALESCE(SUM(p.amount), 0)       AS total_revenue
        FROM country co
        JOIN city     ci ON ci.country_id = co.country_id
        JOIN address  a  ON a.city_id     = ci.city_id
        JOIN customer cu ON cu.address_id = a.address_id
        LEFT JOIN rental  r ON r.customer_id = cu.customer_id
            AND r.rental_date::date BETWEEN :date_start AND :date_end
        LEFT JOIN payment p ON p.rental_id  = r.rental_id
        WHERE 1=1 {country_clause}
        GROUP BY co.country
        ORDER BY total_revenue DESC;
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=params)

    df["avg_revenue_per_customer"] = df.apply(
        lambda row: row["total_revenue"] / row["total_customers"]
        if row["total_customers"] > 0 else 0,
        axis=1,
    )
    return df


@st.cache_data(ttl=300, show_spinner=False)
def fetch_genre_data(countries: tuple, date_start: str, date_end: str) -> pd.DataFrame:
    engine = get_engine()
    country_clause = ""
    params: dict = {"date_start": date_start, "date_end": date_end}
    if countries:
        country_clause = "AND co.country IN :countries"
        params["countries"] = countries

    query = text(f"""
        SELECT
            ca.name            AS genre,
            co.country,
            COUNT(r.rental_id) AS rental_count
        FROM rental r
        JOIN inventory    i  ON i.inventory_id = r.inventory_id
        JOIN film         f  ON f.film_id       = i.film_id
        JOIN film_category fc ON fc.film_id     = f.film_id
        JOIN category     ca ON ca.category_id = fc.category_id
        JOIN customer     cu ON cu.customer_id = r.customer_id
        JOIN address      a  ON a.address_id   = cu.address_id
        JOIN city         ci ON ci.city_id     = a.city_id
        JOIN country      co ON co.country_id  = ci.country_id
        WHERE r.rental_date::date BETWEEN :date_start AND :date_end
          {country_clause}
        GROUP BY ca.name, co.country
        ORDER BY rental_count DESC;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params=params)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_rental_duration(countries: tuple, date_start: str, date_end: str) -> pd.DataFrame:
    engine = get_engine()
    country_clause = ""
    params: dict = {"date_start": date_start, "date_end": date_end}
    if countries:
        country_clause = "AND co.country IN :countries"
        params["countries"] = countries

    query = text(f"""
        SELECT
            EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 86400.0 AS duration_days
        FROM rental r
        JOIN customer cu ON cu.customer_id = r.customer_id
        JOIN address  a  ON a.address_id   = cu.address_id
        JOIN city     ci ON ci.city_id     = a.city_id
        JOIN country  co ON co.country_id  = ci.country_id
        WHERE r.return_date IS NOT NULL
          AND r.rental_date::date BETWEEN :date_start AND :date_end
          {country_clause};
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params=params)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 DVD Rental")
    st.markdown("### Filters")
    st.markdown("---")

    all_countries = fetch_all_countries()
    selected_countries = st.multiselect(
        "🌍 Country",
        options=all_countries,
        default=[],
        placeholder="All countries…",
    )

    min_date, max_date = fetch_date_range()
    date_range = st.date_input(
        "📅 Rental Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("---")
    st.markdown(
        "<small style='color:#4a5068'>Data: PostgreSQL dvdrental<br>"
        "Dashboard: Market & Geographic Performance</small>",
        unsafe_allow_html=True,
    )

# Resolve date range
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    d_start, d_end = date_range
else:
    d_start = d_end = date_range[0] if date_range else min_date

# ── BUG FIX: list → tuple untuk SQL IN clause ──
country_tuple = tuple(selected_countries) if selected_countries else ()

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
with st.spinner("Loading data…"):
    geo_df   = fetch_geo_data(country_tuple, str(d_start), str(d_end))
    genre_df = fetch_genre_data(country_tuple, str(d_start), str(d_end))
    dur_df   = fetch_rental_duration(country_tuple, str(d_start), str(d_end))

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown(
    """
    <div class="header-banner">
        <p class="header-title">Market & Geographic Performance</p>
        <p class="header-sub">DVD Rental · Business Intelligence Dashboard · Data Visualization</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────
st.markdown('<p class="section-title">📊 Key Performance Indicators</p>', unsafe_allow_html=True)
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

total_customers = int(geo_df["total_customers"].sum())
total_revenue   = float(geo_df["total_revenue"].sum())
avg_rev_user    = total_revenue / total_customers if total_customers > 0 else 0
genre_summary   = genre_df.groupby("genre")["rental_count"].sum()
top_genre       = genre_summary.idxmax() if not genre_summary.empty else "N/A"

k1, k2, k3, k4 = st.columns(4)
k1.metric("👥 Total Customers",    f"{total_customers:,}")
k2.metric("💰 Total Revenue",      f"${total_revenue:,.2f}")
k3.metric("💵 Avg Revenue / User", f"${avg_rev_user:,.2f}")
k4.metric("🎭 Most Popular Genre", top_genre)

st.markdown(
    """
    <div class="insight-box">
    💡 <strong>Stakeholder Insight:</strong>
    KPIs above provide an overview of overall business health.
    Compare <em>Total Revenue</em> with <em>Total Customers</em> — if revenue grows
    faster, it means upselling strategy is working.
    <strong>Most Popular Genre</strong> is the main signal for next film stock procurement.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# ─────────────────────────────────────────────
# CHOROPLETH MAP
# ─────────────────────────────────────────────
st.markdown('<p class="section-title">🗺️ Global Customer Distribution</p>', unsafe_allow_html=True)
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

if geo_df.empty:
    st.warning("No geographic data for selected filter.")
else:
    fig_map = px.choropleth(
        geo_df,
        locations="country",
        locationmode="country names",
        color="total_customers",
        hover_name="country",
        hover_data={
            "total_customers": True,
            "total_revenue": ":.2f",
            "avg_revenue_per_customer": ":.2f",
        },
        color_continuous_scale=[
            [0.0,  "#1a1e2e"],
            [0.25, "#2a3a5e"],
            [0.5,  "#1e6091"],
            [0.75, "#c98a00"],
            [1.0,  "#f0c040"],
        ],
        title="Customers per Country",
    )
    fig_map.update_layout(
        paper_bgcolor=PAPER_BG,
        geo=dict(
            bgcolor=PLOT_BG,
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#252a3a",
            showland=True,
            landcolor="#1a1e2e",
            showocean=True,
            oceancolor="#0d0f14",
            showlakes=True,
            lakecolor="#0d0f14",
        ),
        coloraxis_colorbar=dict(
            title=dict(
                text="Customers",
                font=dict(color="#c9cdd8"),   # ✅ fixed: was deprecated titlefont=
            ),
            tickfont=dict(color="#c9cdd8"),
        ),
        font=dict(family="Inter", color="#c9cdd8"),
        margin=dict(l=0, r=0, t=50, b=0),
        height=480,
    )
    st.plotly_chart(fig_map, use_container_width=True)

st.markdown(
    """
    <div class="insight-box">
    💡 <strong>Stakeholder Insight:</strong>
    This map answers: <strong>Where is our customer base located?</strong>
    Yellow color = high concentration (priority market). Dark color = <em>untapped market</em>
    that can be developed with local campaigns.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# ─────────────────────────────────────────────
# ROW 2 — Treemap & Scatter Plot
# ─────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="large")

# ── TREEMAP ──────────────────────────────────
with col_left:
    st.markdown('<p class="section-title">🎭 Film Genre Popularity</p>', unsafe_allow_html=True)
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if genre_df.empty:
        st.warning("No genre data.")
    else:
        genre_agg = genre_df.groupby("genre", as_index=False)["rental_count"].sum()
        genre_agg = genre_agg.sort_values("rental_count", ascending=False)

        fig_tree = px.treemap(
            genre_agg,
            path=["genre"],
            values="rental_count",
            color="rental_count",
            color_continuous_scale=[
                [0.0, "#1a1e2e"],
                [0.5, "#1e6091"],
                [1.0, "#f0c040"],
            ],
            title="Rentals per Genre",
        )
        fig_tree = style_fig(fig_tree)
        fig_tree.update_traces(
            textfont=dict(family="Inter", size=13),
            hovertemplate="<b>%{label}</b><br>Rentals: %{value:,}<extra></extra>",
        )
        fig_tree.update_layout(height=420, coloraxis_showscale=False)
        st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown(
        """
        <div class="insight-box">
        💡 <strong>Insight untuk Stakeholder:</strong>
        <strong>Which genre sells the most?</strong> Larger area = more rentals.
        Use it for <em>inventory planning</em> stock of dominant genres must always be available.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── SCATTER PLOT ─────────────────────────────
with col_right:
    st.markdown('<p class="section-title">📈 Market Efficiency per Country</p>', unsafe_allow_html=True)
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if geo_df.empty or len(geo_df) < 2:
        st.warning("Data tidak cukup untuk scatter plot.")
    else:
        fig_scatter = px.scatter(
            geo_df,
            x="total_customers",
            y="total_revenue",
            size="avg_revenue_per_customer",
            color="avg_revenue_per_customer",
            hover_name="country",
            text="country",
            color_continuous_scale=[
                [0.0, "#1e6091"],
                [0.5, "#c98a00"],
                [1.0, "#f0c040"],
            ],
            labels={
                "total_customers":          "Total Customers",
                "total_revenue":            "Total Revenue ($)",
                "avg_revenue_per_customer": "Avg Rev/User ($)",
            },
            title="Total Customers vs. Total Revenue",
        )

        # Trend line — warna rgba() bukan 8-digit hex
        x_sorted = geo_df["total_customers"].sort_values()
        ratio    = geo_df["total_revenue"].mean() / geo_df["total_customers"].mean()
        y_sorted = ratio * x_sorted

        fig_scatter.add_trace(
            go.Scatter(
                x=x_sorted,
                y=y_sorted,
                mode="lines",
                name="Trend (avg)",
                line=dict(
                    color=TREND_COLOR,   # ✅ rgba(255,255,255,0.13)
                    dash="dot",
                    width=1.5,
                ),
            )
        )

        fig_scatter = style_fig(fig_scatter)
        fig_scatter.update_traces(
            selector=dict(mode="markers+text"),
            textposition="top center",
            textfont=dict(size=9, color="#9aa0b8"),
            marker=dict(
                line=dict(
                    width=1,
                    color=MARKER_BORDER,  # ✅ rgba(255,255,255,0.13)
                )
            ),
        )
        fig_scatter.update_layout(
            height=420,
            xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
            yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
            coloraxis_colorbar=dict(
                title=dict(
                    text="Avg Rev/User",
                    font=dict(color="#c9cdd8"),  # ✅ fixed: was deprecated titlefont=
                ),
                tickfont=dict(color="#c9cdd8"),
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown(
        """
        <div class="insight-box">
        💡 <strong>Insight for Stakeholder:</strong>
        <strong>Is the number of customers directly proportional to profit?</strong>
        Countries <em>above</em> the trend line = efficient market. 
        Countries <em>below</em> = potential increase in average spending via loyalty programs.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─────────────────────────────────────────────# ─────────────────────────────────────────────
# BONUS — Top 10 Countries Table
# ─────────────────────────────────────────────
with st.expander("📋 See Table Data: Top 10 Countries by Revenue"):
    top10 = geo_df.nlargest(10, "total_revenue").copy()
    top10["total_revenue"]            = top10["total_revenue"].map("${:,.2f}".format)
    top10["avg_revenue_per_customer"] = top10["avg_revenue_per_customer"].map("${:,.2f}".format)
    top10 = top10.rename(columns={
        "country":                  "Country",
        "total_customers":          "Total Customers",
        "total_revenue":            "Total Revenue",
        "avg_revenue_per_customer": "Avg Rev / Customer",
    })
    st.dataframe(top10.reset_index(drop=True), use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;color:#3a3f55;font-size:0.78rem;margin-top:40px;padding:20px 0;">
        DVD Rental Analysis · Customer Segmentation & Geographic Performance<br>
        Built with Streamlit + Plotly · Data: PostgreSQL dvdrental
    </div>
    """,
    unsafe_allow_html=True,
)
