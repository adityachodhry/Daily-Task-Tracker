import streamlit as st
import mysql.connector
from login import login_page

db_config = {
    'user': 'isa_user',
    'password': '4-]8sd51D£A6',
    'host': 'tp-vendor-db.ch6c0kme2q7u.ap-south-1.rds.amazonaws.com',
    'database': 'isa_logistics',
    'port': 3306
}

def connect_db():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None
    
def get_all_normal_users():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM daily_tracker_users WHERE role = 'user'")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
    return []

st.set_page_config(page_title="Dashboard")

if 'logged_in_user' not in st.session_state or 'user_role' not in st.session_state:
    st.error("⛔ Unauthorized access. Please log in.")
    st.stop()

username = st.session_state.logged_in_user
role = st.session_state.user_role

st.title(f"📋 {role.capitalize()} Dashboard")

if role in ['admin', 'master']:
    st.success(f"👑 Welcome, {username} (Admin)")
    
    normal_users = get_all_normal_users()
    if normal_users:
        selected_user = st.selectbox("🔽 Select a user to view details", normal_users)
        st.info(f"🧍 Selected User: {selected_user}")
    else:
        st.warning("No normal users found in the system.")
    

elif role == 'user':
    st.success(f"👤 Welcome, {username}")
    st.info("This is your personal task dashboard.")
    

else:
    st.warning("Role not recognized.")

