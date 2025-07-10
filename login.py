import streamlit as st
import mysql.connector

# ----- MySQL Connection Configuration -----
db_config = {
    'user': 'isa_user',
    'password': '4-]8sd51D£A6',
    'host': 'tp-vendor-db.ch6c0kme2q7u.ap-south-1.rds.amazonaws.com',
    'database': 'isa_logistics',
    'port': 3306
}

# DB Connect
def connect_db():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

# Login
def login_user(username, password):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM daily_tracker_users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    return False

# Register
def register_user(username, password, email):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM daily_tracker_users WHERE username = %s", (username,))
        if cursor.fetchone():
            st.warning("Username already exists.")
            conn.close()
            return False
        cursor.execute(
            "INSERT INTO daily_tracker_users (username, password, email_id) VALUES (%s, %s, %s)",
            (username, password, email)
        )
        conn.commit()
        conn.close()
        return True
    return False

# Setup session state
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

# Button click handlers
def go_to_register():
    st.session_state.show_register = True

def go_to_login():
    st.session_state.show_register = False

# Page UI
st.set_page_config(page_title="Daily Task Tracker", layout="centered")
st.title("📝 Daily Task Tracker")

# Login Page
if not st.session_state.show_register:
    st.subheader("Login")

    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Login"):
            if login_user(username, password):
                st.success(f"✅ Welcome {username}! You are now logged in.")
            else:
                st.error("❌ Invalid username or password.")

    with col2:
        st.button("Don't have an account? Register here", on_click=go_to_register)

# Register Page
else:
    st.subheader("Create a New Account")

    new_username = st.text_input("New Username", key="reg_user")
    new_password = st.text_input("New Password", type="password", key="reg_pass")
    new_email = st.text_input("Email ID", key="reg_email")

    if st.button("Register"):
        if new_username and new_password and new_email:
            if register_user(new_username, new_password, new_email):
                st.success("✅ Registered successfully! Please login.")
                st.session_state.show_register = False
        else:
            st.warning("Please fill all fields.")

    st.markdown("---")
    st.button("Back to Login", on_click=go_to_login)