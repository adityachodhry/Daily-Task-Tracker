import streamlit as st
st.set_page_config(page_title="Daily Task Tracker", layout="wide")  # ✅ FIRST Streamlit command

import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime
import json

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

def get_active_tasks(username=None):
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        if username:
            cursor.execute("""
                SELECT id, task, priority, deadline, status, assigned_to 
                FROM daily_tracker_tasks 
                WHERE status IN ('Active', 'Pending', 'In Progress') 
                AND assigned_to = %s
                ORDER BY deadline ASC
            """, (username,))
        else:
            cursor.execute("""
                SELECT id, task, priority, deadline, status, assigned_to 
                FROM daily_tracker_tasks 
                WHERE status IN ('Active', 'Pending', 'In Progress')
                ORDER BY deadline ASC
            """)
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    return []

def get_task_by_id(task_id):
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM daily_tracker_tasks WHERE id = %s", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return row
    return None

def update_task_status(task_id, new_status):
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE daily_tracker_tasks SET status = %s WHERE id = %s", (new_status, task_id))
        conn.commit()
        conn.close()
        return True
    return False

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

def append_message_to_task(task_id, sender, message_text):
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT messages FROM daily_tracker_tasks WHERE id = %s", (task_id,))
        row = cursor.fetchone()
        messages = []
        if row and row['messages']:
            try:
                messages = json.loads(row['messages'])
            except json.JSONDecodeError:
                pass
        messages.append({
            "sender": sender,
            "timestamp": datetime.now().isoformat(),
            "message": message_text
        })
        cursor = conn.cursor()
        cursor.execute("UPDATE daily_tracker_tasks SET messages = %s WHERE id = %s", (json.dumps(messages), task_id))
        conn.commit()
        conn.close()
        return True
    return False

def get_task_messages(task_id):
    conn = connect_db()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT messages FROM daily_tracker_tasks WHERE id = %s", (task_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row['messages']:
            try:
                return json.loads(row['messages'])
            except json.JSONDecodeError:
                return []
    return []

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
if 'selected_task_id' not in st.session_state:
    st.session_state.selected_task_id = None

# ✅ Auto-login using query param
query_params = st.query_params
if 'user' in query_params and not st.session_state.logged_in_user:
    saved_user = query_params['user'][0]
    result = login_user(saved_user, "")
    if result:
        role, email, full_name = result
        st.session_state.logged_in_user = saved_user
        st.session_state.user_role = role
        st.session_state.user_email = email
        st.session_state.full_name = full_name
        st.rerun()

# ---------------- UI Handlers ----------------
def go_to_register():
    st.session_state.show_register = True

def go_to_login():
    st.session_state.show_register = False

# ---------------- Login Page ----------------
if not st.session_state.logged_in_user and not st.session_state.show_register:
    st.title("📝 Daily Task Tracker")
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
                st.query_params = {"user": username}
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

# ---------------- Sidebar ----------------
if st.session_state.logged_in_user:
    # ---------- Sidebar: Task Status Summary ----------
    st.sidebar.subheader("📊 Task Status Summary")

    # ✅ Create a connection and cursor safely
    conn = connect_db()
    if conn:
        cursor = conn.cursor()

        # ✅ Use correct table name and column names
        cursor.execute("""
            SELECT status, COUNT(*) AS count 
            FROM daily_tracker_tasks 
            GROUP BY status
        """)
        status_counts = cursor.fetchall()

        # Optional: Map emojis to status types
        status_emoji_map = {
            "Active": "🟢",
            "Completed": "✅",
            "Pending": "🕒",
            "In Progress": "🔄",
            "Hold": "⏸️",
            "Cancelled": "❌"
        }

        # ✅ Show each status and count in the sidebar
        for status, count in status_counts:
            emoji = status_emoji_map.get(status, "🔹")
            st.sidebar.markdown(f"{emoji} **{status}:** {count}")

        cursor.close()
        conn.close()
    else:
        st.sidebar.error("Failed to connect to database.")

    # ✅ LOGOUT BUTTON
    if st.sidebar.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.query_params = {}
        st.rerun()

    # Admin filtering
    if st.session_state.user_role == 'admin':
        user_map = get_all_users()
        selected_user_name = st.sidebar.selectbox("👤 View Tasks of User", list(user_map.values()))
        selected_username = [u for u, n in user_map.items() if n == selected_user_name][0]
    else:
        selected_username = st.session_state.logged_in_user

    active_tasks = get_active_tasks(selected_username)

    if active_tasks:
        st.sidebar.markdown("### 🔽 Tasks:")
        for task in active_tasks:
            if st.sidebar.button(f"🔸 {task['task'][:30]}...", key=f"task_{task['id']}"):
                st.session_state.selected_task_id = task['id']
    else:
        st.sidebar.info("No active tasks found.")

# ---------------- Main Panel ----------------
if st.session_state.logged_in_user:
    if st.session_state.selected_task_id:
        task = get_task_by_id(st.session_state.selected_task_id)
        st.subheader("📌 Task Details")
        st.markdown(f"""
        ### 📝 {task['task']}
        - ⏳ **Priority:** {task['priority']}
        - 📅 **Deadline:** {task['deadline']}
        - 🧑 **Assigned To:** {task['assigned_to']}
        - 🗒️ **Remarks:** {task['remarks'] or 'None'}
        """)

        if task['assigned_to'] == st.session_state.logged_in_user:
            st.markdown("### ✏️ Update Status")
            new_status = st.selectbox("Change Status", ["Active", "Pending", "In Progress", "Completed"], index=["Active", "Pending", "In Progress", "Completed"].index(task["status"]))
            if st.button("Update Status"):
                if update_task_status(task['id'], new_status):
                    st.success("✅ Status updated.")
                    st.rerun()
                else:
                    st.error("❌ Failed to update status.")
        else:
            st.markdown(f"- 📌 **Status:** {task['status']}")

        st.markdown("### 💬 Conversation")
        messages = get_task_messages(task['id'])
        for msg in messages:
            st.markdown(f"**{msg['sender']}** [{msg['timestamp']}]: {msg['message']}")

        st.markdown("### ✉️ Send a Message")
        message_text = st.text_area("Type your message...", key="new_msg")

        if st.button("Send Message"):
            if append_message_to_task(task['id'], st.session_state.full_name, message_text):
                recipient_email = get_email_by_username(task['assigned_to'])
                email_body = f"""
                <h3>📝 Task Update</h3>
                <p><b>Task:</b> {task['task']}</p>
                <p><b>Message:</b> {message_text}</p>
                <br><p>Sent by <b>{st.session_state.full_name}</b></p>
                """
                send_email(recipient_email, f"Task Update: {task['task'][:80]}", email_body)
                st.success("Message sent and added.")
                st.rerun()

        if st.button("🔙 Back to Assignment Page"):
            st.session_state.selected_task_id = None
            st.rerun()

    else:
        st.subheader("🔥 FireAI Task Assignment")

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
                # closing_date = st.date_input("Expected Closing Date", min_value=date.today())
                remarks = st.text_area("Remarks")
                submitted = st.form_submit_button("Submit Task")

            if submitted:
                recipient_email = get_email_by_username(assigned_to_username)
                if submit_task_to_db(assigned_to_username, task, priority, deadline, status, remarks, st.session_state.logged_in_user):
                    st.success(f"✅ Task assigned to {assigned_to_name}")
                    email_body = f"""
                    <h3>🔔 New Task Assigned</h3>
                    <p><b>Assigned By:</b> {st.session_state.full_name}</p>
                    <p><b>Task:</b> {task}</p>
                    <p><b>Priority:</b> {priority}</p>
                    <p><b>Deadline:</b> {deadline}</p>
                    <p><b>Status:</b> {status}</p>
                    <p><b>Remarks:</b> {remarks}</p>
                    """
                    send_email(recipient_email, f"📝 New Task: {task[:100]}", email_body)
                    st.rerun()
                else:
                    st.error("❌ Failed to assign task.")
