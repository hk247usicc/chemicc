import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ---------------- CONFIG ----------------
ADMIN_PASSWORD = "admin123"

# ---------------- DATABASE ----------------
conn = sqlite3.connect('chemdept.db', check_same_thread=False)
cursor = conn.cursor()

# Inventory table
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    item_code TEXT PRIMARY KEY,
    item_name TEXT,
    total_qty INTEGER,
    issued_qty INTEGER DEFAULT 0
)
''')

# Issue log table
cursor.execute('''
CREATE TABLE IF NOT EXISTS issue_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    item_name TEXT,
    issue_qty INTEGER,
    issued_to TEXT,
    issue_date TEXT
)
''')

conn.commit()

# ---------------- UI ----------------
st.title("📦 Inventory Management System")

menu = st.sidebar.selectbox("Menu", [
    "Show Records",
    "Insert Item",
    "Issue Item",
    "Issue Report",
    "Update Item (Admin)",
    "Delete Item (Admin)"
])

# ---------------- SHOW RECORDS ----------------
if menu == "Show Records":
    st.subheader("📋 Inventory Status")

    cursor.execute("SELECT * FROM inventory")
    rows = cursor.fetchall()

    data = []
    for r in rows:
        code, name, total, issued = r
        balance = total - issued
        data.append([code, name, total, issued, balance])

    df = pd.DataFrame(data, columns=[
        "Item Code", "Item Name", "Total Qty",
        "Issued Qty", "Available (Balance)"
    ])
    st.dataframe(df, use_container_width=True)

# ---------------- INSERT ITEM ----------------
elif menu == "Insert Item":
    st.subheader("➕ Add Item")

    code = st.text_input("Item Code")
    name = st.text_input("Item Name")
    qty = st.number_input("Total Quantity", min_value=1, step=1)

    if st.button("Insert"):
        try:
            cursor.execute(
                "INSERT INTO inventory (item_code, item_name, total_qty) VALUES (?, ?, ?)",
                (code, name, qty)
            )
            conn.commit()
            st.success("✅ Item Inserted")
        except:
            st.error("❌ Item Code already exists")

# ---------------- ISSUE ITEM ----------------
elif menu == "Issue Item":
    st.subheader("📤 Issue Item")

    code = st.text_input("Item Code")
    issued_to = st.text_input("Issued To")
    issue_qty = st.number_input("Issue Quantity", min_value=1)
    issue_date = st.date_input("Issue Date", value=date.today())

    # Auto show item name
    if code:
        cursor.execute("SELECT item_name FROM inventory WHERE item_code=?", (code,))
        res = cursor.fetchone()
        if res:
            st.info(f"Item Name: {res[0]}")
        else:
            st.warning("⚠️ Item not found")

    if st.button("Issue"):
        cursor.execute("SELECT item_name, total_qty, issued_qty FROM inventory WHERE item_code=?", (code,))
        row = cursor.fetchone()

        if row:
            name, total, issued = row
            available = total - issued

            if issue_qty <= available:
                # Update stock
                cursor.execute('''
                    UPDATE inventory
                    SET issued_qty = issued_qty + ?
                    WHERE item_code = ?
                ''', (issue_qty, code))

                # Insert log
                cursor.execute('''
                    INSERT INTO issue_log (item_code, item_name, issue_qty, issued_to, issue_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (code, name, issue_qty, issued_to, str(issue_date)))

                conn.commit()
                st.success("✅ Item Issued")
            else:
                st.error(f"❌ Not enough stock! Available: {available}")
        else:
            st.error("❌ Invalid Item Code")

# ---------------- ISSUE REPORT ----------------
elif menu == "Issue Report":
    st.subheader("📊 Issue Report (Filter by Date)")

    col1, col2 = st.columns(2)
    start_date = col1.date_input("From Date", value=date.today())
    end_date = col2.date_input("To Date", value=date.today())

    if st.button("Generate Report"):
        cursor.execute('''
            SELECT item_code, item_name, issue_qty, issued_to, issue_date
            FROM issue_log
            WHERE issue_date BETWEEN ? AND ?
            ORDER BY issue_date DESC
        ''', (str(start_date), str(end_date)))

        rows = cursor.fetchall()

        df = pd.DataFrame(rows, columns=[
            "Item Code", "Item Name", "Issue Qty",
            "Issued To", "Date"
        ])

        st.dataframe(df, use_container_width=True)

# ---------------- UPDATE ----------------
elif menu == "Update Item (Admin)":
    st.subheader("✏️ Update Item")

    password = st.text_input("Enter Password", type="password")

    if password == ADMIN_PASSWORD:
        code = st.text_input("Item Code")
        name = st.text_input("New Name")
        qty = st.number_input("New Total Quantity", min_value=0)

        if st.button("Update"):
            cursor.execute(
                "UPDATE inventory SET item_name=?, total_qty=? WHERE item_code=?",
                (name, qty, code)
            )
            conn.commit()
            st.success("✅ Updated")
    else:
        st.warning("🔒 Wrong Password")

# ---------------- DELETE ----------------
elif menu == "Delete Item (Admin)":
    st.subheader("❌ Delete Item")

    password = st.text_input("Enter Password", type="password")

    if password == ADMIN_PASSWORD:
        code = st.text_input("Item Code")

        if st.button("Delete"):
            cursor.execute("DELETE FROM inventory WHERE item_code=?", (code,))
            conn.commit()
            st.success("✅ Deleted")
    else:
        st.warning("🔒 Wrong Password")
