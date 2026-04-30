# 🎬 Customer Spending Dashboard (DVDRental)

## 📌 Overview

This project is a data visualization dashboard built using Streamlit and PostgreSQL, based on the DVDRental dataset. The dashboard focuses on analyzing customer spending behavior, identifying top customers, and segmenting them based on their contribution to total revenue.

## 🎯 Objectives

* Analyze customer spending patterns
* Identify top spending customers
* Segment customers based on their value
* Provide insights to support business decision-making

---

## ⚙️ Tech Stack

* Python
* Streamlit
* PostgreSQL
* SQLAlchemy
* Pandas
* Altair

---

## 📊 Features

### 🔍 Filtering

* Filter by Top N Customers (All, Top 5, Top 10, etc.)
* Filter by City
* Search customer by Name or ID

### 📈 Metrics

* Top Customer
* Highest Spending
* Total Revenue

### 📊 Visualizations

* **Top 10 Customer Spending (Horizontal Bar Chart)**
* **Customer Segmentation (Donut Chart)**

### 📋 Data Table

* Customer Ranking
* Customer ID & Name
* City
* Total Spending
* Customer Segment

---

## 🧠 Customer Segmentation

Customers are grouped into three segments based on their total spending:

* **Very Royal** → High-value customers (main revenue contributors)
* **Royal** → Mid-level customers with growth potential
* **Average** → Lower-value customers who can be further engaged

This segmentation helps businesses apply different strategies for each group, such as retention, upselling, and customer activation.

---

## 🚀 How to Run

1. Clone this repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app

```bash
streamlit run app.py
```

4. Open in browser

```
http://localhost:8501
```

---

## 🗄️ Database Setup

Make sure PostgreSQL is running and the DVDRental database is available.

Update your connection string in `app.py`:

```python
postgresql://username:password@localhost:5432/dvdrental
```

---

## 💡 Key Insight

This dashboard highlights that not all customers contribute equally to revenue. By identifying high-value customers and segmenting them accordingly, businesses can make more effective and targeted decisions.

---

## 👥 Team Project

This project is part of a group assignment, where each member focuses on different aspects of customer analysis.

---

## 📌 Notes

* The dataset used is DVDRental (sample PostgreSQL database)
* Customer segmentation labels are customized for this project

---

## ⭐ Future Improvements

* Add churn analysis
* Add time-based trends
* Implement RFM segmentation
* Improve UI/UX

---

## 📎 License

This project is for educational purposes.
