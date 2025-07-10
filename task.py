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