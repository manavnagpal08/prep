import streamlit as st
from firebase import read, write, push, update
from datetime import datetime, timedelta
import pandas as pd

# PAGE CONFIG
st.set_page_config(page_title="Performance Tracker", layout="wide")

# Load CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# -----------------------------
# FIXED LOGIN CREDENTIALS
# -----------------------------
USERS = {
    "manav": "1234",
    "kaaysha": "1234"
}

def login_page():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("Invalid credentials")

# -----------------------------
# NAVIGATION
# -----------------------------      
PAGES = ["Dashboard", "Daily Work", "Projects", "Learning", "Weekly Report"]

def navbar():
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    if col1.button("Dashboard"): st.session_state["page"] = "Dashboard"
    if col2.button("Daily Work"): st.session_state["page"] = "Daily Work"
    if col3.button("Projects"): st.session_state["page"] = "Projects"
    if col4.button("Learning"): st.session_state["page"] = "Learning"
    if col5.button("Report"): st.session_state["page"] = "Weekly Report"
    st.markdown("---")

# -----------------------------
# PAGE FUNCTIONS
# -----------------------------

# 1. DASHBOARD
def dashboard():
    st.title(f"Welcome, {st.session_state['user'].title()}")

    work = read(f"daily/{st.session_state['user']}")
    projects = read(f"projects/{st.session_state['user']}")
    learning = read(f"learning/{st.session_state['user']}")

    col1, col2, col3 = st.columns(3)

    col1.metric("Days Logged", len(work) if work else 0)
    col2.metric("Projects", len(projects) if projects else 0)
    col3.metric("Learnings", len(learning) if learning else 0)

# 2. DAILY WORK
def daily_work():
    st.title("Daily Work Tracker")

    task = st.text_area("What did you do today?")
    hours = st.number_input("Hours spent", 0.0, 24.0, 0.0)

    if st.button("Save"):
        entry = {
            "task": task,
            "hours": hours,
            "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M")
        }
        push(f"daily/{st.session_state['user']}", entry)
        st.success("Saved!")

    st.subheader("History")
    data = read(f"daily/{st.session_state['user']}")
    if data:
        df = pd.DataFrame(data.values())
        st.table(df)

# 3. PROJECT TRACKING
def projects():
    st.title("Project Tracker")

    name = st.text_input("Project Name")
    progress = st.slider("Progress (%)", 0, 100, 0)
    notes = st.text_area("Notes")

    if st.button("Add Project"):
        entry = {
            "name": name,
            "progress": progress,
            "notes": notes,
            "updated": datetime.now().strftime("%d-%m-%Y")
        }
        push(f"projects/{st.session_state['user']}", entry)
        st.success("Project added!")

    data = read(f"projects/{st.session_state['user']}")
    if data:
        df = pd.DataFrame(data.values())
        st.table(df)

# 4. LEARNING LOG
def learning():
    st.title("Learning Log")

    topic = st.text_input("What did you learn?")
    source = st.text_input("Source (YouTube, Course, etc.)")
    link = st.text_input("Link (optional)")

    if st.button("Save Learning"):
        entry = {
            "topic": topic,
            "source": source,
            "link": link,
            "date": datetime.now().strftime("%d-%m-%Y")
        }
        push(f"learning/{st.session_state['user']}", entry)
        st.success("Saved!")

    data = read(f"learning/{st.session_state['user']}")
    if data:
        df = pd.DataFrame(data.values())
        st.table(df)

# 5. WEEKLY REPORT
def weekly_report():
    st.title("Weekly Performance Report")

    work = read(f"daily/{st.session_state['user']}")
    learn = read(f"learning/{st.session_state['user']}")
    projects = read(f"projects/{st.session_state['user']}")

    st.subheader("Summary")
    st.write(f"• Total work logs: {len(work) if work else 0}")
    st.write(f"• Learnings added: {len(learn) if learn else 0}")
    st.write(f"• Projects active: {len(projects) if projects else 0}")

# -----------------------------
# APP ROUTER
# -----------------------------

if "user" not in st.session_state:
    login_page()
else:
    navbar()

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard": dashboard()
    elif page == "Daily Work": daily_work()
    elif page == "Projects": projects()
    elif page == "Learning": learning()
    elif page == "Weekly Report": weekly_report()
