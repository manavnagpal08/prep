import streamlit as st
from firebase import read, write, update, push
from datetime import datetime, timedelta, date
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# -----------------------------
# PAGE CONFIG
# -----------------------------
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

# -----------------------------
# LOGIN PAGE
# -----------------------------
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
# NAVIGATION BAR
# -----------------------------
def navbar():
    st.markdown("---")
    cols = st.columns(10)
    pages = [
        "Dashboard", "Daily Work", "Projects", "Learning", "Weekly Goals",
        "Habits", "Calendar", "Graphs", "Suggestions", "Compare"
    ]

    for idx, pg in enumerate(pages):
        if cols[idx].button(pg):
            st.session_state["page"] = pg

    st.markdown("---")


# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard():
    st.title(f"Welcome, {st.session_state['user'].title()}")

    work = read(f"daily/{st.session_state['user']}") or {}
    proj = read(f"projects/{st.session_state['user']}") or {}
    learn = read(f"learning/{st.session_state['user']}") or {}
    habits = read(f"habits/{st.session_state['user']}") or {}

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Work Logs", len(work))
    col2.metric("Projects", len(proj))
    col3.metric("Learnings", len(learn))
    col4.metric("Habit Days", len(habits))


# -----------------------------
# DAILY WORK PAGE
# -----------------------------
def daily_work():
    st.title("Daily Work Log")

    task = st.text_area("Describe what you did today")
    hours = st.number_input("Hours Worked", 0.0, 24.0, 0.0)

    mood = st.slider("Mood", 1, 5, 3)
    productivity = st.slider("Productivity", 1, 5, 3)
    energy = st.slider("Energy", 1, 5, 3)

    if st.button("Save Log"):
        entry = {
            "task": task,
            "hours": hours,
            "mood": mood,
            "productivity": productivity,
            "energy": energy,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        push(f"daily/{st.session_state['user']}", entry)
        st.success("Daily work saved")

    st.subheader("History")
    data = read(f"daily/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame(data.values())
        st.table(df)


# -----------------------------
# PROJECT TRACKER
# -----------------------------
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
            "updated": datetime.now().strftime("%Y-%m-%d")
        }
        push(f"projects/{st.session_state['user']}", entry)
        st.success("Project added")

    st.subheader("All Projects")
    data = read(f"projects/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame(data.values())
        st.table(df)


# -----------------------------
# LEARNING TRACKER
# -----------------------------
def learning():
    st.title("Learning Log")

    topic = st.text_input("What did you learn?")
    source = st.text_input("Source (YouTube, Course)")
    link = st.text_input("Link (optional)")

    if st.button("Save Learning"):
        entry = {
            "topic": topic,
            "source": source,
            "link": link,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        push(f"learning/{st.session_state['user']}", entry)
        st.success("Learning saved")

    st.subheader("Learning History")
    data = read(f"learning/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame(data.values())
        st.table(df)


# -----------------------------
# WEEKLY GOALS
# -----------------------------
def weekly_goals():
    st.title("Weekly Goals")

    goal = st.text_input("Goal Title")
    target = st.text_area("Target Description")

    if st.button("Add Goal"):
        entry = {
            "goal": goal,
            "target": target,
            "week": datetime.now().isocalendar().week
        }
        push(f"goals/{st.session_state['user']}", entry)
        st.success("Goal added")

    st.subheader("Your Weekly Goals")
    data = read(f"goals/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame(data.values())
        st.table(df)


# -----------------------------
# HABIT TRACKER
# -----------------------------
HABITS = [
    "DSA Practice",
    "Python / AI Skill Practice",
    "Review Semester Subjects",
    "Notes / Revision",
    "Learning Videos",
    "Mini Project Work",
    "Health Habit",
    "No Phone 1 Hour Study",
    "Wake Up on Time"
]

def habits():
    st.title("Daily Habit Tracker")

    today = datetime.now().strftime("%Y-%m-%d")

    st.write("Check the habits you completed today:")
    checked = {}

    for habit in HABITS:
        checked[habit] = st.checkbox(habit)

    if st.button("Save Habits"):
        push(f"habits/{st.session_state['user']}", {
            "date": today,
            "habits": checked
        })
        st.success("Habit log saved")

    st.subheader("Habit History")
    data = read(f"habits/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame(data.values())
    st.table(df)


# -----------------------------
# CALENDAR VIEW
# -----------------------------
def calendar():
    st.title("Calendar View")

    data = read(f"daily/{st.session_state['user']}") or {}
    dates = [i["date"] for i in data.values()]

    st.write("Days you logged work:")

    st.code("\n".join(dates))


# -----------------------------
# GRAPH VIEW
# -----------------------------
def graphs():
    st.title("Performance Graphs")

    data = read(f"daily/{st.session_state['user']}") or {}

    if not data:
        st.info("No data to graph yet.")
        return

    df = pd.DataFrame(data.values())

    if "hours" in df:
        fig = px.line(df, x="date", y="hours", title="Hours Worked Over Time")
        st.plotly_chart(fig)


# -----------------------------
# AI STYLE SUGGESTIONS
# -----------------------------
def suggestions():
    st.title("Improvement Suggestions (Based on Your Logs)")

    work = read(f"daily/{st.session_state['user']}") or {}
    habits = read(f"habits/{st.session_state['user']}") or {}

    if not work:
        st.info("Add some logs to generate suggestions.")
        return

    suggestions = []

    avg_productivity = sum([int(w["productivity"]) for w in work.values()]) / len(work)
    avg_energy = sum([int(w["energy"]) for w in work.values()]) / len(work)

    if avg_productivity < 3:
        suggestions.append("Try fixing time blocks for study to increase productivity.")

    if avg_energy < 3:
        suggestions.append("Sleep earlier and drink more water to increase energy.")

    if habits:
        last = list(habits.values())[-1]
        done = sum(last["habits"].values())

        if done < 5:
            suggestions.append("Complete at least 5 habits daily for consistency.")

    st.write("### Suggestions:")
    for s in suggestions:
        st.write("- " + s)


# -----------------------------
# COMPARE USERS
# -----------------------------
def compare():
    st.title("Compare Performance (Manav vs Kaaysha)")

    users = ["manav", "kaaysha"]

    stats = {}
    for user in users:
        stats[user] = len(read(f"daily/{user}") or {})

    df = pd.DataFrame({
        "User": users,
        "Work Logs": [stats["manav"], stats["kaaysha"]]
    })

    st.table(df)


# -----------------------------
# MAIN ROUTER
# -----------------------------
if "user" not in st.session_state:
    login_page()
else:
    navbar()

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        dashboard()
    elif page == "Daily Work":
        daily_work()
    elif page == "Projects":
        projects()
    elif page == "Learning":
        learning()
    elif page == "Weekly Goals":
        weekly_goals()
    elif page == "Habits":
        habits()
    elif page == "Calendar":
        calendar()
    elif page == "Graphs":
        graphs()
    elif page == "Suggestions":
        suggestions()
    elif page == "Compare":
        compare()
