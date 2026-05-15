import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ---------------- CONFIG ----------------
ADMIN_PASSWORD = "admin123"   # change this password

# ---------------- DATABASE ----------------
conn = sqlite3.connect('chedept.db', check_same_thread=False)
cursor = conn.cursor()

# Create inventory table
cursor.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    item_code TEXT PRIMARY KEY,
    item_name TEXT,
    total_qty INTEGER,
    issued_qty INTEGER DEFAULT 0,
    last_issued_to TEXT,
    last_issue_date TEXT
)
''')
conn.commit()

# ---------------- UI ----------------
st.title("Chemistry Department Stock Register")

menu = st.sidebar.selectbox("Menu", [
    "Show Records",
    "Insert Item",
    "Issue Item",
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
        item_code, name, total, issued, person, d = r
        available = total - issued
        data.append([item_code, name, total, issued, available, person, d])

    df = pd.DataFrame(data, columns=[
        "Item Code", "Item Name", "Total Qty",
        "Issued", "Available (Balance)",
        "Last Issued To", "Last Issue Date"
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
            st.success("✅ Item Added")
        except:
            st.error("❌ Item Code already exists")

# ---------------- ISSUE ITEM ----------------
elif menu == "Issue Item":
    st.subheader("📤 Issue Item")

    code = st.text_input("Item Code")
    issued_to = st.text_input("Issued To")
    issue_date = st.date_input("Issue Date", value=date.today())

    if st.button("Issue"):
        cursor.execute("SELECT total_qty, issued_qty FROM inventory WHERE item_code=?", (code,))
        row = cursor.fetchone()

        if row:
            total, issued = row
            if total - issued > 0:
                cursor.execute('''
                    UPDATE inventory
                    SET issued_qty = issued_qty + 1,
                        last_issued_to = ?,
                        last_issue_date = ?
                    WHERE item_code = ?
                ''', (issued_to, str(issue_date), code))
                conn.commit()
                st.success("✅ Item Issued")
            else:
                st.error("❌ No stock available")
        else:
            st.error("❌ Invalid Item Code")

# ---------------- UPDATE ITEM ----------------
elif menu == "Update Item (Admin)":
    st.subheader("✏️ Update Item")

    password = st.text_input("Enter Admin Password", type="password")

    if password == ADMIN_PASSWORD:
        code = st.text_input("Item Code")
        new_name = st.text_input("New Name")
        new_qty = st.number_input("New Total Quantity", min_value=0)

        if st.button("Update"):
            cursor.execute(
                "UPDATE inventory SET item_name=?, total_qty=? WHERE item_code=?",
                (new_name, new_qty, code)
            )
            conn.commit()
            st.success("✅ Item Updated")
    else:
        st.warning("🔒 Enter correct password")

# ---------------- DELETE ITEM ----------------
elif menu == "Delete Item (Admin)":
    st.subheader("❌ Delete Item")

    password = st.text_input("Enter Admin Password", type="password")

    if password == ADMIN_PASSWORD:
        code = st.text_input("Item Code to Delete")

        if st.button("Delete"):
            cursor.execute("DELETE FROM inventory WHERE item_code=?", (code,))
            conn.commit()
            st.success("✅ Item Deleted")
    else:
        st.warning("🔒 Enter correct password")