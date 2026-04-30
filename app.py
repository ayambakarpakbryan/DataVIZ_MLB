import streamlit as st

st.set_page_config(
    page_title="DVD Rental Analytics",
    page_icon="📀",
    layout="wide"
)

st.title("📀 DVD Rental Analytics Dashboard")
st.sidebar.success("Select a page above to start exploring.")

st.markdown("""
### Midterm Exam Presentation: Customer Focus

Welcome to our group's interactive dashboard. For this analysis, we have chosen to focus entirely on **Customer Behavior and Performance**. 

By analyzing the `dvdrental` database, this dashboard aims to answer key questions:
* **Who are our most valuable customers?** (See *Customer Spending*)
* **What are their viewing preferences?** *(Coming Next)*
* **How frequently do they rent?** *(Coming Next)*

**Group Members:**
* Member 1
* Member 2
* Member 3
* Member 4

👈 **Please select a dashboard from the sidebar to begin.**
""")