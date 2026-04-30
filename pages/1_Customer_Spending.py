import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine

st.set_page_config(layout="wide")
st.title("Customer Spending Dashboard")

@st.cache_resource
def get_engine():
    return create_engine(
        "postgresql://postgres:12345@localhost:5432/dvdrental_analytics"
    )

engine = get_engine()

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Filter")

top_option = st.sidebar.selectbox(
    "Top Customer",
    ["All", 5, 10, 30, 50, 100],
    index=0
)

cities = pd.read_sql(
    "SELECT city FROM city ORDER BY city", engine
)["city"].tolist()

selected_city = st.sidebar.selectbox("City", ["All"] + cities)

search = st.sidebar.text_input("Search Customer (Name / ID)")

# =========================
# QUERY
# =========================
query = """
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS name,
    ci.city,
    SUM(p.amount) AS total_spent
FROM customer c
JOIN payment p ON c.customer_id = p.customer_id
JOIN address a ON c.address_id = a.address_id
JOIN city ci ON a.city_id = ci.city_id
"""

conditions = []

if selected_city != "All":
    conditions.append(f"ci.city = '{selected_city}'")

if conditions:
    query += " WHERE " + " AND ".join(conditions)

query += """
GROUP BY c.customer_id, name, ci.city
ORDER BY total_spent DESC
"""

df = pd.read_sql(query, engine)

# =========================
# FILTER PYTHON
# =========================
if search:
    df = df[
        df["name"].str.contains(search, case=False, na=False) |
        df["customer_id"].astype(str).str.contains(search)
    ]

if top_option != "All":
    df = df.head(int(top_option))

if df.empty:
    st.warning("⚠️ Tidak ada data ditemukan")
    st.stop()

# =========================
# PROCESSING
# =========================
df["Rank"] = range(1, len(df)+1)

def segment(x):
    if x > 150:
        return "High Value"
    elif x > 100:
        return "Medium Value"
    else:
        return "Low Value"

df["Segment"] = df["total_spent"].apply(segment)

# =========================
# METRICS
# =========================
top_customer = df.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric("Top Customer", top_customer["name"])
col2.metric("Highest Spending", f"${top_customer['total_spent']:.2f}")
col3.metric("Total Revenue", f"${df['total_spent'].sum():,.2f}")

st.divider()

# =========================
# CHART
# =========================
st.subheader("Top 10 Customer Spending")

top10 = df.head(10)

col1, col2 = st.columns(2)

with col1:
    st.write("Top Spenders")

    top10 = df.head(10).sort_values("total_spent", ascending=False)

    chart = alt.Chart(top10).mark_bar().encode(
        x="total_spent",
        y=alt.Y("name", sort="-x"),  
        tooltip=["name", "total_spent"]
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

with col2:
    st.write("Customer Segmentation Based on Spending")

    segment_data = df["Segment"].value_counts().reset_index()
    segment_data.columns = ["Segment", "Count"]

    chart = alt.Chart(segment_data).mark_arc(innerRadius=60).encode(
        theta="Count",
        color=alt.Color(
            "Segment",
            scale=alt.Scale(
                domain=["High Value", "Medium Value", "Low Value"],
                range=["#FFD700", "#00C49F", "#8884d8"]  # emas, hijau, ungu
            ),
            legend=alt.Legend(title="Segment")
        ),
        tooltip=["Segment", "Count"]
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

st.divider()

# =========================
# TABLE
# =========================
st.subheader(f"Customer Detail ({top_option})")

st.dataframe(
    df[
        [
            "Rank",
            "customer_id",
            "name",
            "city",
            "total_spent",
            "Segment",
        ]
    ],
    use_container_width=True,
)