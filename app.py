
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date

# PAGE SETTINGS
st.set_page_config(
    page_title="SpendWise",
    page_icon="💸",
    layout="wide"
)

# DATABASE
conn = sqlite3.connect(
    "expenses.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
)
""")

conn.commit()


# ADD EXPENSE
def add_expense(d, c, a, desc):
    cursor.execute("""
    INSERT INTO expenses (date, category, amount, description)
    VALUES (?, ?, ?, ?)
    """, (str(d), c, a, desc))
    conn.commit()


# GET EXPENSES
def get_expenses():
    return pd.read_sql_query(
        "SELECT * FROM expenses ORDER BY date DESC, id DESC",
        conn
    )


# DELETE EXPENSE
def delete_expense(expense_id):
    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (int(expense_id),)
    )
    conn.commit()


# CUSTOM DESIGN
st.markdown("""
<style>
.stApp {
    background-color: #0B1120;
    color: white;
}
section[data-testid="stSidebar"] {
    background-color: #111827;
}
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1E293B, #312E81);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #374151;
}
div[data-testid="stMetric"] label {
    color: #CBD5E1 !important;
}
div[data-testid="stMetricValue"] {
    color: white;
}
</style>
""", unsafe_allow_html=True)


# SIDEBAR
st.sidebar.title("💸 SpendWise")
st.sidebar.caption("Personal Expense Tracker")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Expense", "Manage Expenses"]
)

st.sidebar.divider()
st.sidebar.info("Track your money. Save smarter.")

categories = [
    "Food", "Transport", "Shopping",
    "Bills", "Entertainment", "Health",
    "Education", "Travel", "Other"
]

df = get_expenses()


# =========================
# DASHBOARD
# =========================

if page == "Dashboard":

    st.title("📊 SpendWise Dashboard")
    st.write("Welcome! Here's your financial overview.")

    total = df["amount"].sum() if not df.empty else 0
    count = len(df)
    average = total / count if count else 0

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Spending", f"₹{total:,.2f}")
    c2.metric("Transactions", count)
    c3.metric("Average Expense", f"₹{average:,.2f}")

    st.divider()

    if df.empty:
        st.info("No expenses yet. Add your first expense!")
    else:

        st.subheader("📈 Spending Analytics")

        col1, col2 = st.columns(2)

        with col1:
            category_data = df.groupby(
                "category", as_index=False
            )["amount"].sum()

            fig = px.pie(
                category_data,
                names="category",
                values="amount",
                hole=0.5,
                title="Expenses by Category"
            )

            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            monthly = df.copy()
            monthly["date"] = pd.to_datetime(monthly["date"])
            monthly["month"] = monthly["date"].dt.to_period("M").astype(str)

            monthly_data = monthly.groupby(
                "month", as_index=False
            )["amount"].sum().sort_values("month")

            fig2 = px.bar(
                monthly_data,
                x="month",
                y="amount",
                title="Monthly Spending",
                color_discrete_sequence=["#8B5CF6"]
            )

            fig2.update_layout(template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("🧾 Recent Transactions")
        st.dataframe(
            df.head(5),
            use_container_width=True,
            hide_index=True
        )


# =========================
# ADD EXPENSE
# =========================

elif page == "Add Expense":

    st.title("➕ Add New Expense")
    st.write("Enter your expense details.")

    with st.form("expense_form"):

        amount = st.number_input(
            "Amount (₹)",
            min_value=1.0,
            value=100.0
        )

        category = st.selectbox(
            "Category",
            categories
        )

        expense_date = st.date_input(
            "Date",
            value=date.today(),
            max_value=date.today()
        )

        description = st.text_input(
            "Description",
            placeholder="Example: Lunch with friends"
        )

        submit = st.form_submit_button(
            "Save Expense",
            use_container_width=True
        )

        if submit:
            if not description.strip():
                st.error("Enter a description.")
            else:
                add_expense(
                    expense_date,
                    category,
                    amount,
                    description
                )
                st.success("Expense saved successfully!")
                st.rerun()


# =========================
# MANAGE EXPENSES
# =========================

elif page == "Manage Expenses":

    st.title("🧾 Manage Expenses")

    if df.empty:
        st.info("No expenses available.")

    else:

        selected_category = st.multiselect(
            "Filter by Category",
            categories
        )

        filtered = df.copy()

        if selected_category:
            filtered = filtered[
                filtered["category"].isin(selected_category)
            ]

        st.write(f"Showing {len(filtered)} expenses")

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        # DOWNLOAD CSV
        csv = filtered.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download CSV",
            csv,
            "spendwise_expenses.csv",
            "text/csv"
        )

        st.divider()

        # DELETE
        st.subheader("Delete Expense")

        expense_id = st.selectbox(
            "Select Expense ID",
            filtered["id"].tolist()
        )

        confirm = st.checkbox("Confirm deletion")

        if st.button("Delete Expense", disabled=not confirm):
            delete_expense(expense_id)
            st.success("Expense deleted!")
            st.rerun()


# FOOTER
st.divider()
st.caption(
    "SpendWise | Python + Streamlit + SQLite + Pandas + Plotly"
)
