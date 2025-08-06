import streamlit as st
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

# ---------------- Gmail Sender ----------------
SENDER_EMAIL = "aditya.choudhary@isalogistics.in"
SENDER_PASSWORD = "ldpq yrck kgyz hdxc"

# ---------------- MySQL Config ----------------
db_config = {
    'user': 'isa_user',
    'password': '4-]8sd51D£A6',
    'host': 'tp-vendor-db.ch6c0kme2q7u.ap-south-1.rds.amazonaws.com',
    'database': 'isa_logistics',
    'port': 3306
}
# ---------------- DB Connection ----------------
def connect_db():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        st.error(f"Database connection error: {err}")
        return None

# ---------------- User Functions ----------------
def login_user(username, password):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role, email_id, name FROM daily_tracker_users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result  # (role, email, full_name)
    return None

def register_user(username, password, email, name):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM daily_tracker_users WHERE username = %s", (username,))
        if cursor.fetchone():
            st.warning("Username already exists.")
            conn.close()
            return False
        cursor.execute(
            "INSERT INTO daily_tracker_users (username, password, email_id, name, role) VALUES (%s, %s, %s, %s, %s)",
            (username, password, email, name, 'user')
        )
        conn.commit()
        conn.close()
        return True
    return False

def get_all_users():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, name FROM daily_tracker_users")
        users = cursor.fetchall()
        conn.close()
        return {u: n for u, n in users}
    return {}

def get_email_by_username(username):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email_id FROM daily_tracker_users WHERE username = %s", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    return None

def submit_task_to_db(assigned_to, task, priority, deadline, status, closing_date, remarks, created_by):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_tracker_tasks 
            (assigned_to, task, priority, deadline, status, closing_date, remarks, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (assigned_to, task, priority, deadline, status, closing_date, remarks, created_by))
        conn.commit()
        conn.close()
        return True
    return False

# def get_active_tasks(username=None):
#     conn = connect_db()
#     if conn:
#         cursor = conn.cursor(dictionary=True)
#         if username:
#             cursor.execute("""
#                 SELECT task, priority, deadline, status 
#                 FROM daily_tracker_tasks 
#                 WHERE status IN ('Active', 'Pending', 'In Progress') 
#                 AND assigned_to = %s
#                 ORDER BY deadline ASC
#             """, (username,))
#         else:
#             cursor.execute("""
#                 SELECT task, priority, deadline, status, assigned_to 
#                 FROM daily_tracker_tasks 
#                 WHERE status IN ('Active', 'Pending', 'In Progress')
#                 ORDER BY deadline ASC
#             """)
#         tasks = cursor.fetchall()
#         conn.close()
#         return tasks
#     return []

def send_email(recipient_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email sending failed: {e}")
        return False

# ---------------- Session State Setup ----------------
if 'show_register' not in st.session_state:
    st.session_state.show_register = False
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'full_name' not in st.session_state:
    st.session_state.full_name = None

# ---------------- UI Handlers ----------------
def go_to_register():
    st.session_state.show_register = True

def go_to_login():
    st.session_state.show_register = False

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Daily Task Tracker", layout="centered")
st.title("📝 Daily Task Tracker")

# ---------------- Login Page ----------------
if not st.session_state.logged_in_user and not st.session_state.show_register:
    st.subheader("Login")

    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Login"):
            result = login_user(username, password)
            if result:
                role, email, full_name = result
                st.session_state.logged_in_user = username
                st.session_state.user_role = role
                st.session_state.user_email = email
                st.session_state.full_name = full_name
                st.success(f"✅ Welcome {full_name} ({role})")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    with col2:
        st.button("Don't have an account? Register here", on_click=go_to_register)

# ---------------- Register Page ----------------
elif st.session_state.show_register:
    st.subheader("Create a New Account")

    new_username = st.text_input("New Username", key="reg_user")
    new_password = st.text_input("New Password", type="password", key="reg_pass")
    new_email = st.text_input("Email ID", key="reg_email")
    new_name = st.text_input("Full Name", key="reg_name")

    if st.button("Register"):
        if new_username and new_password and new_email and new_name:
            if register_user(new_username, new_password, new_email, new_name):
                st.success("✅ Registered successfully! Please login.")
                st.session_state.show_register = False
        else:
            st.warning("Please fill all fields.")

    st.markdown("---")
    st.button("Back to Login", on_click=go_to_login)

# # ---------------- Sidebar: Active Tasks ----------------
# if st.session_state.logged_in_user:
#     st.sidebar.title("📋 Active Tasks")

#     active_tasks = get_active_tasks(st.session_state.logged_in_user)

#     if active_tasks:
#         for task in active_tasks:
#             st.sidebar.markdown(f"""
#             🔸 **Task:** {task['task'][:30]}...
#             - ⏳ *Priority:* {task['priority']}
#             - 📅 *Deadline:* {task['deadline']}
#             - 📌 *Status:* {task['status']}
#             """)
#             st.sidebar.markdown("---")
#     else:
#         st.sidebar.info("No active tasks.")

# ---------------- Task Assignment Page ----------------
elif st.session_state.logged_in_user:
    st.subheader("🔥 FireAI Task Assessment Home")

    user_map = get_all_users()
    assignable_users = {u: n for u, n in user_map.items() if u != st.session_state.logged_in_user}

    if not assignable_users:
        st.info("No other users found to assign tasks.")
    else:
        with st.form("task_form"):
            assigned_to_name = st.selectbox("Assign Task To", list(assignable_users.values()))
            assigned_to_username = [u for u, n in assignable_users.items() if n == assigned_to_name][0]
            task = st.text_area("Task Description")
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            deadline = st.date_input("Deadline", min_value=date.today())
            status = st.selectbox("Status", ["Active", "Pending", "In Progress", "Completed"])
            closing_date = st.date_input("Expected Closing Date", min_value=date.today())
            remarks = st.text_area("Remarks")

            submitted = st.form_submit_button("Submit Task")

        if submitted:
            recipient_email = get_email_by_username(assigned_to_username)

            if submit_task_to_db(
                assigned_to_username,
                task, priority, deadline, status,
                closing_date, remarks,
                st.session_state.logged_in_user
            ):
                st.success(f"✅ Task assigned to {assigned_to_name}")

                email_body = f"""
                <h3>🔔 You have been assigned a new task</h3>
                <p><b>Assigned By:</b> {st.session_state.full_name}</p>
                <p><b>Task:</b> {task}</p>
                <p><b>Priority:</b> {priority}</p>
                <p><b>Deadline:</b> {deadline}</p>
                <p><b>Status:</b> {status}</p>
                <p><b>Closing Date:</b> {closing_date}</p>
                <p><b>Remarks:</b> {remarks}</p>
                <br>
                <p>Best regards,<br><b>{st.session_state.full_name}</b></p>
                """

                if send_email(recipient_email, f"📝 New Task: {task[:100]}", email_body):
                    st.info(f"📧 Email sent to {assigned_to_name}")
                else:
                    st.warning("⚠️ Email not sent.")
            else:
                st.error("❌ Failed to assign task.")