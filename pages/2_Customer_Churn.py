import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import create_engine

st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")

st.title("Customer Churn & Retention Analysis")
st.markdown("Identify which customers are active, at risk of leaving, or have already churned based on their recent rental behavior.")

# =========================
# DATABASE CONNECTION
# =========================
@st.cache_resource
def get_engine():
    # UPDATE THIS with your actual password if needed!
    return create_engine("postgresql://postgres:12345@localhost:5432/dvdrental_analytics")

engine = get_engine()

# =========================
# QUERY
# =========================
@st.cache_data
def load_data():
    query = """
    WITH global_latest AS (
        SELECT MAX(rental_date) AS db_now FROM rental
    ),
    customer_latest AS (
        SELECT 
            customer_id, 
            MAX(rental_date) AS last_rental
        FROM rental
        GROUP BY customer_id
    )
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS name,
        c.email,
        cl.last_rental,
        DATE_PART('day', gl.db_now - cl.last_rental) AS days_since_last_rental,
        SUM(p.amount) as lifetime_value
    FROM customer c
    JOIN customer_latest cl ON c.customer_id = cl.customer_id
    CROSS JOIN global_latest gl
    JOIN payment p ON c.customer_id = p.customer_id
    GROUP BY c.customer_id, name, c.email, cl.last_rental, gl.db_now
    ORDER BY days_since_last_rental DESC;
    """
    return pd.read_sql(query, engine)

df = load_data()

# =========================
# PROCESSING (CHURN LOGIC)
# =========================
def determine_status(days):
    if days <= 30:
        return "Active (<= 30 days)"
    elif days <= 60:
        return "At Risk (31-60 days)"
    else:
        return "Churned (> 60 days)"

df["Status"] = df["days_since_last_rental"].apply(determine_status)

# =========================
# SIDEBAR: FILTERS & INFO
# =========================
st.sidebar.header("🔍 Dashboard Filters")

# 1. Filter by Status
status_options = [
    "Active (<= 30 days)", 
    "At Risk (31-60 days)", 
    "Churned (> 60 days)"
]
selected_statuses = st.sidebar.multiselect(
    "Filter by Status:",
    options=status_options,
    default=status_options
)

# 2. Filter by Minimum Lifetime Value
max_ltv = float(df["lifetime_value"].max()) if not df.empty else 200.0
min_ltv = st.sidebar.slider(
    "Minimum Lifetime Value ($):",
    min_value=0.0,
    max_value=max_ltv,
    value=0.0,
    step=10.0
)

# 3. Filter by Days Since Last Rental (Range Slider)
max_days = int(df["days_since_last_rental"].max()) if not df.empty else 100
min_days = int(df["days_since_last_rental"].min()) if not df.empty else 0
selected_days_range = st.sidebar.slider(
    "Days Since Last Rental:",
    min_value=min_days,
    max_value=max_days,
    value=(min_days, max_days), 
    step=1
)

# =========================
# APPLY FILTERS TO DATAFRAME
# =========================
filtered_df = df.copy()

# Apply Status Filter
if selected_statuses:
    filtered_df = filtered_df[filtered_df["Status"].isin(selected_statuses)]

# Apply LTV Filter
filtered_df = filtered_df[filtered_df["lifetime_value"] >= min_ltv]

# Apply Days Range Filter
filtered_df = filtered_df[
    (filtered_df["days_since_last_rental"] >= selected_days_range[0]) & 
    (filtered_df["days_since_last_rental"] <= selected_days_range[1])
]

# Handle empty dataframe state safely
if filtered_df.empty:
    st.warning("No customers found matching the current filters.")
    st.stop()
# =========================
# METRICS FOR STORE OWNER
# =========================
total_customers = len(filtered_df)
churned_customers = len(filtered_df[filtered_df["Status"] == "Churned (> 60 days)"])
risk_customers = len(filtered_df[filtered_df["Status"] == "At Risk (31-60 days)"])
churn_rate = (churned_customers / total_customers) * 100 if total_customers > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Customer Base", f"{total_customers:,}")
col2.metric("Customers At Risk", risk_customers, delta="Needs Attention", delta_color="off")
col3.metric("Overall Churn Rate", f"{churn_rate:.1f}%", delta="- Lost Revenue", delta_color="inverse")

st.divider()

# =========================
# VISUALIZATIONS
# =========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Customer Health Distribution")
    st.write("Percentage of our user base by active status.")
    
    status_counts = filtered_df["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    
    base = alt.Chart(status_counts).encode(
        theta=alt.Theta("Count:Q", stack=True),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(
                domain=["Active (<= 30 days)", "At Risk (31-60 days)", "Churned (> 60 days)"],
                range=["#00C49F", "#FFD700", "#FF4B4B"]
            ),
            legend=alt.Legend(title="Health Status")
        ),
        tooltip=["Status", "Count"]
    )
    
    donut = base.mark_arc(innerRadius=60).properties(height=350)
    st.altair_chart(donut, use_container_width=True)

with col2:
    st.subheader("Recency Distribution")
    st.write("How many days has it been since customers last visited?")
    
    hist = alt.Chart(filtered_df).mark_bar(color="#8884d8").encode(
        x=alt.X("days_since_last_rental:Q", bin=alt.Bin(maxbins=20), title="Days Since Last Rental"),
        y=alt.Y("count():Q", title="Number of Customers"),
        tooltip=["count()", "days_since_last_rental"]
    ).properties(height=350)
    
    st.altair_chart(hist, use_container_width=True)


# =========================
# ACTIONABLE INSIGHTS TABLE
# =========================
st.subheader("Customer Details Table")
st.markdown("")

# We remove the hardcoded "Active" filter and simply use the dataframe 
# that is already being controlled by your sidebar filters!
table_df = filtered_df.sort_values(by="lifetime_value", ascending=False)

st.dataframe(
    table_df[["customer_id", "name", "email", "lifetime_value", "days_since_last_rental", "Status"]].style.format({
        "lifetime_value": "${:.2f}",
        "days_since_last_rental": "{:.0f} days"
    }),
    use_container_width=True,
    hide_index=True
)