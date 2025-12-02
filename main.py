import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import random
import uuid
from collections import defaultdict

# ==========================================================
# 1. MOCKING FIREBASE FUNCTIONS & DUMMY DATA SETUP
# ==========================================================

HABITS = [
    "1 LeetCode/DSA Problem",
    "Review AI/ML Notes",
    "Dedicated Project Coding Session",
    "Notes/Revision (Non-coding)",
    "Learning Videos/Tutorials",
    "Health Habit (Exercise/Walk)",
    "No Phone 1 Hour Study",
    "Wake Up on Time"
]

# FIXED LOGIN CREDENTIALS (Only 3 users allowed)
USERS = {
    "manav": "1234",
    "kaaysha": "1234",
    "pranav": "1234"
}

def generate_user_data(user, is_high_performer=True):
    """Generates consistent dummy data based on performance profile."""
    
    daily_data = {}
    habits_data = {}
    
    today = datetime.now().date()
    
    # Define performance profile
    if user == "manav" or user == "pranav":
        # High Performer Profile (Manav/Pranav)
        hour_range = (4.0, 7.5)  
        prod_min = 4
        habit_success_rate = 0.85
    else:
        # Average Performer Profile (Kaaysha)
        hour_range = (2.5, 5.5)  
        prod_min = 3
        habit_success_rate = 0.65

    for i in range(14):
        date_i = today - timedelta(days=i)
        date_str = date_i.strftime("%Y-%m-%d")
        
        # Daily Work Log
        hours = round(random.uniform(*hour_range), 1)
        productivity = random.randint(prod_min, 5)
        mood = random.randint(prod_min, 5)
        
        task_list = [
            f"Completed LeetCode {random.choice(['Medium', 'Hard'])} and reviewed the optimal solution.",
            f"Dedicated {hours} hours to focused deep work on project feature.",
            f"Revised core concepts from previous week's lecture and made flashcards.",
            f"Finished 1/3 of the assigned reading and documented key takeaways.",
        ]
        
        log_key = str(uuid.uuid4())
        daily_data[log_key] = {
            "task": random.choice(task_list),
            "hours": hours,
            "mood": mood,
            "productivity": productivity,
            "energy": random.randint(prod_min, 5),
            "date": date_str
        }

        # Habit Log
        habits_key = str(uuid.uuid4())
        habits_done = {h: (random.random() < habit_success_rate) for h in HABITS}
        
        habits_data[habits_key] = {
            "date": date_str,
            "habits": habits_done
        }
    
    # Static Data for Project/Learning/Goals
    is_high_performer = (user == "manav" or user == "pranav")
    projects_data = {
        "p1": {"name": "Semester Project (AI/ML Model)", "progress": 75 if is_high_performer else 50, "notes": "Need to integrate final testing dataset.", "updated": "2025-11-28"},
        "p2": {"name": "Personal Portfolio Website", "progress": 90 if is_high_performer else 70, "notes": "Final CSS styling and deployment pending.", "updated": "2025-12-01"},
    }

    learning_data = {
        "l1": {"topic": "Transformer Architecture (Attention Mechanism)", "source": "Deep Learning Book Chapter 5", "link": "", "keywords": ["NLP", "AI", "DL"], "date": "2025-12-01"},
        "l2": {"topic": "Advanced Pandas Vectorization", "source": "YouTube - Data Science Channel", "link": "link_to_video", "keywords": ["Data Science", "Python"], "date": "2025-11-28"},
    }

    goals_data = {
        "g1": {"goal": "Complete 10 LeetCode Mediums", "target": "Must include 3 DP problems.", "week": datetime.now().isocalendar().week, "status": "In Progress"},
        "g2": {"goal": "Finish 2 chapters of DL book review", "target": "100% conceptual clarity.", "week": datetime.now().isocalendar().week, "status": "To Do"},
        "g3": {"goal": "Fixed Project Bug", "target": "Authentication bug resolved.", "week": (datetime.now() - timedelta(days=7)).isocalendar().week, "status": "Completed"},
    }
    
    # Assemble all data into the path-based mock structure
    user_data = {
        f"daily/{user}": daily_data,
        f"habits/{user}": habits_data,
        f"projects/{user}": projects_data,
        f"learning/{user}": learning_data,
        f"goals/{user}": goals_data,
        f"planner/{user}/{today.strftime('%Y-%m-%d')}": {"p1": "Solve today's LeetCode problem", "est_hours": 4.5, "focus_area": "DSA/AI"}
    }
    
    return user_data

# Initialize Mock Database with data for the three users
MOCK_DB = {}
MOCK_DB.update(generate_user_data("manav", is_high_performer=True))
MOCK_DB.update(generate_user_data("kaaysha", is_high_performer=False))
MOCK_DB.update(generate_user_data("pranav", is_high_performer=True))

# --- Mock Firebase Functions ---
def read(path):
    """Mocks the read function using the MOCK_DB store."""
    return MOCK_DB.get(path)

def write(path, data):
    """Mocks the write function (overwrites)."""
    MOCK_DB[path] = data
    return True

def update(path, data):
    """Mocks the update function (merges)."""
    if path in MOCK_DB and isinstance(MOCK_DB[path], dict):
        MOCK_DB[path].update(data)
    else:
        MOCK_DB[path] = data 
    return True

def push(path, data):
    """Mocks the push function (adds a unique key)."""
    if path not in MOCK_DB:
        MOCK_DB[path] = {}
    
    key = str(uuid.uuid4())
    MOCK_DB[path][key] = data
    return key


# ==========================================================
# 2. STREAMLIT APP CODE
# ==========================================================

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Student Progress Tracker", layout="wide", initial_sidebar_state="collapsed")

# Load CSS
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Could not find 'styles.css'. Using basic formatting.")

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
@st.cache_data(ttl=600)
def get_daily_logs(user):
    data = read(f"daily/{user}") or {}
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()])
        df['date'] = pd.to_datetime(df['date'])
        df['productivity'] = pd.to_numeric(df['productivity'], errors='coerce')
        df['hours'] = pd.to_numeric(df['hours'], errors='coerce')
        df = df.sort_values(by='date', ascending=False).reset_index(drop=True)
        return df
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_habit_logs(user):
    data = read(f"habits/{user}") or {}
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False).reset_index(drop=True)
        return df
    return pd.DataFrame()


# -----------------------------
# LOGIN PAGE
# -----------------------------
def login_page():
    st.title("🔑 AI/DS Student Progress Tracker")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if username in USERS and USERS[username] == password:
            st.session_state["user"] = username
            st.session_state["page"] = "Dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials")
    
    st.info("Demo users: **manav** / **kaaysha** / **pranav**. Password: **1234**")


# -----------------------------
# NAVIGATION BAR
# -----------------------------
def navbar():
    st.markdown("---")
    pages = [
        "Dashboard", "Daily Planner", "Daily Log", "Projects", "Learning", 
        "Weekly Goals", "Habits", "Peer Review", "Graphs & Insights" 
    ]
    
    # Use 10 columns for pages and 1 for logout/spacer
    cols = st.columns([0.1]*9 + [0.1])
    
    for idx, pg in enumerate(pages):
        button_type = "primary" if st.session_state.get("page") == pg else "secondary"
        # Only use the first 9 columns for navigation buttons
        if idx < 9 and cols[idx].button(pg, type=button_type, key=f"nav_{pg}"):
            st.session_state["page"] = pg
            st.rerun()
            
    if cols[-1].button("Logout 🚪", key="nav_logout"):
        st.session_state.clear()
        st.rerun()
        
    st.markdown("---")


# -----------------------------
# DASHBOARD (Simplified for brevity, see prior code for full details)
# -----------------------------
def dashboard():
    st.header(f"🚀 Welcome Back, **{st.session_state['user'].title()}**!", divider='blue')

    df_work = get_daily_logs(st.session_state['user'])
    df_proj = pd.DataFrame((read(f"projects/{st.session_state['user']}") or {}).values())
    
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Deep Work Logs", len(df_work))
    col2.metric("Active Projects", len(df_proj[df_proj['progress'] < 100]) if not df_proj.empty else 0)
    col3.metric("Avg Productivity (All Time)", f"{df_work['productivity'].mean().round(2) if not df_work.empty else 0.0}/5")
    
    st.markdown("---")
    
    # 2. Daily Log Snapshot (Last 7 Days)
    st.subheader("🗓️ Recent Performance Summary")
    
    if not df_work.empty:
        one_week_ago = datetime.now() - timedelta(days=7)
        df_work_recent = df_work[df_work['date'] >= one_week_ago.strftime('%Y-%m-%d')]
        
        if not df_work_recent.empty:
            
            avg_hours = df_work_recent['hours'].mean().round(1)
            avg_prod = df_work_recent['productivity'].mean().round(2)

            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Hours/Day (7D)", f"{avg_hours}h")
            c2.metric("Avg Productivity (7D)", f"{avg_prod}/5")
            c3.metric("Total Tasks Logged (7D)", len(df_work_recent))
            
            fig = px.bar(df_work_recent.sort_values(by='date'), 
                         x='date', y='hours', 
                         title='Deep Work Hours Logged in the Last Week', 
                         template='plotly_white',
                         color_discrete_sequence=['#4CAF50'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No work logs in the last 7 days.")
    else:
        st.info("Start logging your daily work to see a summary here!")

# -----------------------------
# PEER REVIEW PAGE (NEW)
# -----------------------------
def peer_review():
    st.header("🤝 Peer Review and Accountability", divider='violet')
    st.write("View the current status, today's plan, and recent activity of your group members.")

    current_user = st.session_state['user']
    other_users = [u for u in USERS.keys() if u != current_user]
    today = datetime.now().strftime("%Y-%m-%d")

    st.subheader(f"Status as of **{today}**")

    for peer in other_users:
        st.markdown(f"### 🧑‍💻 {peer.title()}'s Activity")
        
        col_plan, col_log = st.columns(2)

        # 1. Today's Plan
        with col_plan:
            plan_key = f"planner/{peer}/{today}"
            peer_plan = read(plan_key) or {}
            
            st.markdown("#### 🎯 Today's Focus (Planned)")
            if peer_plan:
                st.info(f"**Focus Area:** {peer_plan['focus_area']}")
                st.markdown(f"**Est. Hours:** `{peer_plan['est_hours']} hrs`")
                st.markdown(f"**P1 (Deep Work):** {peer_plan.get('p1', 'N/A')}")
                if peer_plan.get('p2'): st.markdown(f"**P2:** {peer_plan['p2']}")
            else:
                st.warning("No daily plan logged yet.")

        # 2. Recent Work Log
        with col_log:
            df_peer_log = get_daily_logs(peer)
            st.markdown("#### 📝 Latest Logged Work (Completed)")
            if not df_peer_log.empty:
                latest_log = df_peer_log.iloc[0]
                st.success(f"**Logged Date:** {latest_log['date'].strftime('%Y-%m-%d')}")
                st.markdown(f"**Hours:** `{latest_log['hours']}h`")
                st.markdown(f"**Productivity:** `{latest_log['productivity']}/5`")
                st.markdown(f"**Task:** *{latest_log['task'][:70]}...*")
            else:
                st.warning("No recent work log found.")
        
        st.markdown("---")
        
        # 3. Project Status & Habits (Side by Side)
        col_proj, col_habits = st.columns(2)

        with col_proj:
            peer_projects = read(f"projects/{peer}") or {}
            st.markdown("##### ⚙️ Current Project Status")
            if peer_projects:
                df_proj = pd.DataFrame(peer_projects.values())
                active_proj = df_proj[df_proj['progress'] < 100].sort_values(by='progress', ascending=False)
                
                if not active_proj.empty:
                    top_proj = active_proj.iloc[0]
                    st.metric(label=f"Top Project: {top_proj['name']}", 
                              value=f"{top_proj['progress']}%", 
                              delta=f"Pending: {top_proj['notes'][:40]}...")
                else:
                    st.success("All major projects are completed!")
            else:
                st.info("No projects added.")

        with col_habits:
            df_peer_habits = get_habit_logs(peer)
            st.markdown("##### ✅ Habit Consistency (Last 7 Days)")
            if not df_peer_habits.empty:
                one_week_ago = datetime.now() - timedelta(days=7)
                df_recent_habits = df_peer_habits[df_peer_habits['date'] >= one_week_ago.strftime('%Y-%m-%d')]
                
                if not df_recent_habits.empty:
                    df_recent_habits['total_done'] = df_recent_habits['habits'].apply(lambda x: sum(x.values()))
                    avg_habits = df_recent_habits['total_done'].mean().round(1)
                    st.metric(label="Avg Habits Completed (7D)", value=f"{avg_habits}/{len(HABITS)}", delta=None)
                else:
                    st.info("Need more habit logs in the last week.")
            else:
                st.info("No habit history found.")
        
        st.markdown("---") # Visual separator between peers

# --- Rest of the functions (Daily Planner, Daily Work, Projects, Learning, Weekly Goals, Habits, Graphs & Insights) ---
# NOTE: These functions remain the same as the previous full code, 
# but are omitted here for brevity. Please ensure you keep them in your final app.py file. 
# The implementations are assumed to be complete from the previous step.

def daily_planner(): 
    st.warning("Daily Planner function placeholder. See the full code from the previous step.")
    pass
def daily_work():
    st.warning("Daily Work Log function placeholder. See the full code from the previous step.")
    pass
def projects():
    st.warning("Project Tracker function placeholder. See the full code from the previous step.")
    pass
def learning():
    st.warning("Learning Log function placeholder. See the full code from the previous step.")
    pass
def weekly_goals():
    st.warning("Weekly Goals function placeholder. See the full code from the previous step.")
    pass
def habits():
    st.warning("Habit Tracker function placeholder. See the full code from the previous step.")
    pass
def graphs_and_insights():
    st.warning("Graphs & Insights function placeholder. See the full code from the previous step.")
    pass


# -----------------------------
# MAIN ROUTER
# -----------------------------
if "user" not in st.session_state:
    login_page()
else:
    navbar()

    page = st.session_state.get("page", "Dashboard") 

    page_functions = {
        "Dashboard": dashboard,
        "Daily Planner": daily_planner,
        "Daily Log": daily_work,
        "Projects": projects,
        "Learning": learning,
        "Weekly Goals": weekly_goals,
        "Habits": habits,
        "Peer Review": peer_review,  # <-- NEW PAGE
        "Graphs & Insights": graphs_and_insights
    }
    
    if page in page_functions:
        # NOTE: Using a simple placeholder for functions not fully provided here. 
        # In your final code, replace the 'pass' functions above with the full code.
        if page == "Daily Planner": daily_planner()
        elif page == "Daily Log": daily_work()
        elif page == "Projects": projects()
        elif page == "Learning": learning()
        elif page == "Weekly Goals": weekly_goals()
        elif page == "Habits": habits()
        elif page == "Graphs & Insights": graphs_and_insights()
        elif page == "Peer Review": peer_review()
        else: dashboard()
    else:
        st.error("Page not found!")
