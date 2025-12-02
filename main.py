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

def generate_user_data(user, is_high_performer=True):
    """Generates consistent dummy data based on performance profile."""
    
    daily_data = {}
    habits_data = {}
    
    today = datetime.now().date()
    
    # Define performance profile
    if is_high_performer:
        # High Performer Profile (Manav/Peer 1)
        hour_range = (4.0, 7.5)  
        prod_min = 4
        habit_success_rate = 0.85
    else:
        # Average Performer Profile (Kaaysha/Peer 2)
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
MOCK_DB.update(generate_user_data("pranav", is_high_performer=True)) # Third user

# --- Mock Firebase Functions ---
# NOTE: These functions mock real-time database operations and must be replaced 
# with your actual Firebase calls when you implement the backend.

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
# FIXED LOGIN CREDENTIALS (Only 3 users allowed)
# -----------------------------
USERS = {
    "manav": "1234",
    "kaaysha": "1234",
    "pranav": "1234"
}

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
        "Weekly Goals", "Habits", "Graphs & Insights"
    ]
    
    # Use 9 columns for pages and 1 for logout/spacer
    cols = st.columns([0.1]*8 + [0.2]*2)
    
    for idx, pg in enumerate(pages):
        button_type = "primary" if st.session_state.get("page") == pg else "secondary"
        # Only use the first 8 columns for navigation buttons
        if cols[idx].button(pg, type=button_type, key=f"nav_{pg}"):
            st.session_state["page"] = pg
            st.rerun()
            
    if cols[-1].button("Logout 🚪", key="nav_logout"):
        st.session_state.clear()
        st.rerun()
        
    st.markdown("---")


# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard():
    st.header(f"🚀 Welcome Back, **{st.session_state['user'].title()}**!", divider='blue')

    df_work = get_daily_logs(st.session_state['user'])
    df_proj = pd.DataFrame((read(f"projects/{st.session_state['user']}") or {}).values())
    df_learn = pd.DataFrame((read(f"learning/{st.session_state['user']}") or {}).values())
    df_habits = get_habit_logs(st.session_state['user'])

    col1, col2, col3, col4 = st.columns(4)

    # 1. Key Metrics
    col1.metric("Total Deep Work Logs", len(df_work))
    col2.metric("Active Projects", len(df_proj[df_proj['progress'] < 100]) if not df_proj.empty else 0)
    col3.metric("Concepts Learned", len(df_learn))
    col4.metric("Average Productivity (All Time)", f"{df_work['productivity'].mean().round(2) if not df_work.empty else 0.0}/5")
    
    st.markdown("---")
    
    # 2. Daily Log Snapshot (Last 7 Days)
    st.subheader("🗓️ Recent Performance Summary")
    
    if not df_work.empty:
        one_week_ago = datetime.now() - timedelta(days=7)
        df_work_recent = df_work[df_work['date'] >= one_week_ago.strftime('%Y-%m-%d')]
        
        if not df_work_recent.empty:
            
            avg_hours = df_work_recent['hours'].mean().round(1)
            avg_prod = df_work_recent['productivity'].mean().round(2)
            avg_energy = df_work_recent['energy'].mean().round(2)

            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Hours/Day (7D)", f"{avg_hours}h")
            c2.metric("Avg Productivity (7D)", f"{avg_prod}/5")
            c3.metric("Avg Energy (7D)", f"{avg_energy}/5")
            
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
# DAILY PLANNER
# -----------------------------
def daily_planner():
    st.header("📝 Daily Pre-Work Planner", divider='orange')
    st.write("Plan your main tasks, focus areas, and estimated deep work time.")
    
    today = datetime.now().strftime("%Y-%m-%d")
    planner_key = f"planner/{st.session_state['user']}/{today}"
    current_plan = read(planner_key) or {}

    with st.form("planner_form"):
        st.subheader(f"Plan for Today: **{today}**")
        
        p1 = st.text_input("🎯 P1 (Most Important/Deep Work Task)", value=current_plan.get('p1', ''))
        p2 = st.text_input("🔹 P2 (Secondary Task/Review)", value=current_plan.get('p2', ''))
        p3 = st.text_input("🔸 P3 (Minor Task/Skill Practice)", value=current_plan.get('p3', ''))
        
        est_hours = st.number_input("Est. Total Hours of Deep Work", 0.0, 12.0, value=current_plan.get('est_hours', 4.0), step=0.5)

        focus_options = ["DSA/Algorithms", "AI/ML Project", "Semester Subject Review", "Skill Development (e.g., DevOps)", "Other"]
        focus_area = st.selectbox(
            "Main Focus Area Today",
            focus_options,
            index=focus_options.index(current_plan.get('focus_area', 'DSA/Algorithms')) if current_plan.get('focus_area') in focus_options else 0
        )
        
        submitted = st.form_submit_button("Save Today's Plan", type="primary")

        if submitted:
            plan = {
                "date": today,
                "p1": p1,
                "p2": p2,
                "p3": p3,
                "est_hours": est_hours,
                "focus_area": focus_area
            }
            write(planner_key, plan)
            st.success("Daily Plan Saved! Ready for execution.")
            st.experimental_rerun()
            
    if current_plan:
        st.markdown("---")
        st.subheader("Current Plan Summary")
        st.markdown(f"**Focus Area:** **{current_plan['focus_area']}**")
        st.markdown(f"**Estimated Hours:** `{current_plan['est_hours']} hrs`")
        
        st.write("### Today's Priorities:")
        st.markdown(f"1. **{current_plan.get('p1', 'N/A')}**")
        if current_plan.get('p2'): st.markdown(f"2. {current_plan['p2']}")
        if current_plan.get('p3'): st.markdown(f"3. {current_plan['p3']}")


# -----------------------------
# DAILY WORK LOG
# -----------------------------
def daily_work():
    st.header("✍️ Daily Work Log", divider='blue')

    with st.form("daily_log_form"):
        st.subheader("Log Your Accomplishments")
        
        task = st.text_area("Describe **what specific task you completed** and **from where** (e.g., 'Finished 2.5 hours of K-Means implementation for Project X', 'Revised DP patterns from LeetCode patterns list').")
        hours = st.number_input("Actual Deep Work Hours", 0.0, 24.0, 0.0, step=0.5)

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        mood = col1.slider("Mood (1=Bad, 5=Great)", 1, 5, 3)
        productivity = col2.slider("Productivity (1=Low Focus, 5=High Focus)", 1, 5, 3)
        energy = col3.slider("Energy (1=Drained, 5=Energized)", 1, 5, 3)

        submitted = st.form_submit_button("Save Log", type="primary")

        if submitted:
            entry = {
                "task": task,
                "hours": hours,
                "mood": mood,
                "productivity": productivity,
                "energy": energy,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            push(f"daily/{st.session_state['user']}", entry)
            st.success("Daily work saved! Check the 'Graphs & Insights' for your trend.")
            st.experimental_rerun()


    st.markdown("---")
    st.subheader("History (Recent Logs)")
    df = get_daily_logs(st.session_state['user'])
    if not df.empty:
        st.dataframe(df[['date', 'hours', 'task', 'productivity', 'energy']].head(10).rename(columns={'hours': 'Hours', 'task': 'Task Description', 'productivity': 'Prod', 'energy': 'Energy'}), 
                     use_container_width=True, 
                     hide_index=True)
    else:
        st.info("No work history found.")


# -----------------------------
# PROJECT TRACKER
# -----------------------------
def projects():
    st.header("⚙️ Project Tracker", divider='blue')

    with st.expander("Add/Update Project", expanded=False):
        with st.form("project_form"):
            name = st.text_input("Project Name (e.g., 4th Sem AI Project, Personal Web Dev)")
            progress = st.slider("Progress (%)", 0, 100, 0)
            notes = st.text_area("Pending: What is left to be done?")
            
            submitted = st.form_submit_button("Save Project", type="primary")

            if submitted:
                entry = {
                    "name": name,
                    "progress": progress,
                    "notes": notes,
                    "updated": datetime.now().strftime("%Y-%m-%d")
                }
                push(f"projects/{st.session_state['user']}", entry) 
                st.success("Project saved/updated.")
                st.experimental_rerun()

    st.subheader("Project Status (Pending Work)")
    data = read(f"projects/{st.session_state['user']}") or {}
    
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()]) 
        
        st.dataframe(df[['name', 'progress', 'updated', 'notes']].rename(columns={'name': 'Project', 'progress': 'Progress (%)', 'updated': 'Last Update', 'notes': 'Pending Tasks'}), 
                     use_container_width=True, hide_index=True)
        
        fig = px.bar(df.sort_values(by='progress', ascending=False), 
                     x='name', y='progress', 
                     color='progress', 
                     color_continuous_scale=px.colors.sequential.Teal,
                     title='Project Progress Overview', 
                     template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No projects added yet.")


# -----------------------------
# LEARNING TRACKER
# -----------------------------
def learning():
    st.header("🧠 Learning Log: Concepts & Resources", divider='blue')

    with st.form("learning_form"):
        topic = st.text_input("What specific concept/skill did you learn/revise?")
        source = st.text_input("Source (e.g., Coursera NLP module, LeetCode 100, Textbook Chapter 6)")
        link = st.text_input("Resource Link (Optional)")
        keywords = st.text_input("Keywords (e.g., Python, DP, OOP, React)", help="Separate with commas")
        
        submitted = st.form_submit_button("Save Learning", type="primary")

        if submitted:
            entry = {
                "topic": topic,
                "source": source,
                "link": link,
                "keywords": [k.strip() for k in keywords.split(',')],
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            push(f"learning/{st.session_state['user']}", entry)
            st.success("Learning saved. Track your skills!")
            st.experimental_rerun()

    st.subheader("Learning History")
    data = read(f"learning/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame(data.values())
        df = df.sort_values(by='date', ascending=False)
        st.dataframe(df[['date', 'topic', 'source', 'keywords']].rename(columns={'topic': 'Concept', 'source': 'Source'}), use_container_width=True, hide_index=True)
        
        all_keywords = [item for sublist in df['keywords'].dropna() for item in sublist]
        if all_keywords:
            kw_series = pd.Series(all_keywords).value_counts().head(10)
            fig = px.pie(kw_series, values=kw_series.values, names=kw_series.index, title='Top 10 Learning Focus Areas', color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No learning history found.")


# -----------------------------
# WEEKLY GOALS
# -----------------------------
def weekly_goals():
    st.header("📅 Weekly Goals", divider='blue')
    current_week = datetime.now().isocalendar().week
    st.subheader(f"Goals for Week **{current_week}**")

    with st.expander("Add a New Goal", expanded=False):
        with st.form("goal_form"):
            goal = st.text_input("Goal Title (e.g., Complete 5 LeetCode Mediums)")
            target = st.text_area("Target Description/Success Criteria")
            status = st.selectbox("Initial Status", ["To Do", "In Progress", "Completed", "Failed/Deferred"])

            submitted = st.form_submit_button("Add Goal", type="primary")

            if submitted:
                entry = {
                    "goal": goal,
                    "target": target,
                    "week": current_week,
                    "status": status,
                    "created": datetime.now().strftime("%Y-%m-%d")
                }
                push(f"goals/{st.session_state['user']}", entry)
                st.success("Goal added! Good luck.")
                st.experimental_rerun()

    st.subheader("Current Week Goals")
    data = read(f"goals/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()])
        df = df.sort_values(by=['week', 'status'], ascending=[False, True])
        
        current_week_df = df[df['week'] == current_week]
        
        if not current_week_df.empty:
            
            st.dataframe(current_week_df[['goal', 'status', 'target']].rename(columns={'goal': 'Goal', 'target': 'Details'}), 
                         use_container_width=True, hide_index=True)

            status_counts = current_week_df['status'].value_counts()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Goals", len(current_week_df))
            c2.metric("Completed ✅", status_counts.get("Completed", 0))
            c3.metric("In Progress ⏳", status_counts.get("In Progress", 0))
            c4.metric("To Do 💡", status_counts.get("To Do", 0))
            
            st.markdown("---")
            st.markdown("**Quick Status Update**")
            
            update_data = current_week_df[current_week_df['status'] != 'Completed']
            if not update_data.empty:
                goal_options = update_data['goal'].tolist()
                
                col_goal, col_status, col_button = st.columns([3, 2, 1])
                
                goal_to_update = col_goal.selectbox("Select Goal to Update Status", goal_options)
                
                initial_status = update_data[update_data['goal'] == goal_to_update]['status'].iloc[0]
                status_options = ["To Do", "In Progress", "Completed", "Failed/Deferred"]
                
                new_status = col_status.selectbox(
                    "New Status", 
                    status_options,
                    index=status_options.index(initial_status)
                )
                
                if col_button.button("Update"):
                    key_to_update = current_week_df[current_week_df['goal'] == goal_to_update]['key'].iloc[0]
                    update(f"goals/{st.session_state['user']}/{key_to_update}", {"status": new_status})
                    st.success(f"Status for '{goal_to_update}' updated to **{new_status}**.")
                    st.experimental_rerun()
            else:
                st.info("All current goals are completed or no goals set!")

        else:
            st.info(f"No goals set for week {current_week} yet.")

        if len(df[df['week'] != current_week]) > 0:
             if st.checkbox("Show Past Goals"):
                st.dataframe(df[df['week'] != current_week][['week', 'goal', 'status']], use_container_width=True, hide_index=True)
    else:
        st.info("No goals added yet.")


# -----------------------------
# HABIT TRACKER
# -----------------------------
def habits():
    st.header("✅ Daily Habit Tracker (Consistency Check)", divider='blue')

    today = datetime.now().strftime("%Y-%m-%d")
    
    df_habits = get_habit_logs(st.session_state['user'])
    today_log = df_habits[df_habits['date'].dt.strftime('%Y-%m-%d') == today]
    
    is_logged = not today_log.empty
    current_checked = today_log['habits'].iloc[0] if is_logged else {}

    if is_logged:
        st.warning(f"Habits for **{today}** are already logged. Use the form below to **UPDATE**.")
    else:
        st.info(f"Log your habits for **{today}**.")

    with st.form("habit_form"):
        st.subheader("Check the habits you completed today:")
        checked = {}

        cols = st.columns(3)
        
        for idx, habit in enumerate(HABITS):
            col = cols[idx % 3]
            default_state = current_checked.get(habit, False)
            checked[habit] = col.checkbox(habit, value=default_state)

        button_label = "Update Habits" if is_logged else "Save Habits"
        if st.form_submit_button(button_label, type="primary"):
            entry = {
                "date": today,
                "habits": checked
            }
            
            if is_logged:
                key_to_update = today_log['key'].iloc[0]
                update(f"habits/{st.session_state['user']}/{key_to_update}", entry)
                st.success(f"Habit log for {today} updated!")
            else:
                push(f"habits/{st.session_state['user']}", entry)
                st.success("Habit log saved!")
                
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Habit Consistency & Streak")
    
    if not df_habits.empty:
        df_habits['total_done'] = df_habits['habits'].apply(lambda x: sum(x.values()))
        df_habits['date_str'] = df_habits['date'].dt.strftime('%Y-%m-%d')

        fig = px.bar(df_habits.sort_values(by='date', ascending=True).tail(14), 
                     x='date_str', y='total_done', 
                     title='Habits Completed (Last 14 Days)',
                     labels={'total_done': 'Number of Habits Done', 'date_str': 'Date'},
                     template='plotly_white',
                     color='total_done', 
                     color_continuous_scale=px.colors.sequential.Viridis)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_habits[['date', 'total_done']].tail(10).rename(columns={'total_done': 'Habits Done'}), 
                     use_container_width=True, hide_index=True)
    else:
        st.info("No habit history found.")


# -----------------------------
# GRAPHS & INSIGHTS 
# -----------------------------
def graphs_and_insights():
    st.header("📊 Graphs & Insights", divider='blue')
    
    tab1, tab2, tab3 = st.tabs(["Performance Graphs", "Actionable Suggestions", "Comparison (Peer View)"])

    # --- TAB 1: Performance Graphs ---
    with tab1:
        st.subheader("Daily Log Trends")
        df = get_daily_logs(st.session_state['user'])
    
        if df.empty:
            st.info("No data to graph yet.")
        else:
            fig_hours = px.line(df, x="date", y="hours", title="Hours Worked Over Time", template='plotly_white', line_shape='spline')
            st.plotly_chart(fig_hours, use_container_width=True)
            
            df_melted = df.melt(id_vars='date', value_vars=['mood', 'productivity', 'energy'], var_name='Metric', value_name='Rating')
            fig_ratings = px.line(df_melted, x="date", y="Rating", color='Metric', title="Mood, Productivity, & Energy Trends (1-5)", template='plotly_white')
            st.plotly_chart(fig_ratings, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Correlation Analysis")
            st.info("Check if higher Mood/Energy correlates with better Productivity.")
            fig_corr = px.scatter(df, x='mood', y='productivity', 
                                  title='Mood vs. Productivity Scatter Plot', 
                                  color='hours', 
                                  size='hours', 
                                  template='plotly_white')
            st.plotly_chart(fig_corr, use_container_width=True)

    # --- TAB 2: AI Suggestions ---
    with tab2:
        st.subheader("Improvement Suggestions (Based on Your Logs)")

        df_work = get_daily_logs(st.session_state['user'])
        df_habits = get_habit_logs(st.session_state['user'])

        if df_work.empty:
            st.info("Add some logs to generate suggestions.")
            return

        suggestions = []
        
        avg_productivity = df_work['productivity'].mean().round(2)
        avg_energy = df_work['energy'].mean().round(2)
        avg_hours = df_work['hours'].mean().round(2)

        if avg_productivity < 3.8:
             suggestions.append(f"**Productivity is moderate ({avg_productivity}/5).** Try implementing the **Pomodoro technique** (25 mins work, 5 mins break) or dedicated **deep work sessions** to minimize distractions.")
        elif avg_productivity >= 4.5:
             suggestions.append(f"**Excellent Productivity!** Keep doing what you're doing. To maintain this, consider **pre-planning your next day's top 3 tasks** every evening.")

        if avg_energy < 3.5:
            suggestions.append(f"**Average Energy is low ({avg_energy}/5).** Prioritize **sleep (7-8 hours)** and hydration. Low energy severely limits the capacity for deep work.")

        if not df_habits.empty:
            df_habits['total_done'] = df_habits['habits'].apply(lambda x: sum(x.values()))
            recent_habits = df_habits.head(7)
            avg_habits = recent_habits['total_done'].mean().round(1)
            
            if avg_habits < 5:
                suggestions.append(f"**Recent Habit Completion is only {avg_habits}/{len(HABITS)} per day.** Focus on completing the **DSA Practice** or **Project Coding** habits daily for consistency.")

        if avg_hours < 3.5:
            suggestions.append(f"**Average Daily Hours are low ({avg_hours} hrs).** Aim for a minimum of 4-5 focused deep work hours per day. Use the **Daily Planner** to allocate this time effectively.")
            
        st.write("### Personalized Insights:")
        for s in suggestions:
            st.markdown(f"**💡 {s}**")

    # --- TAB 3: Comparison ---
    with tab3:
        st.subheader("Peer Performance Comparison (Motivational View)")
        st.write("Compare key metrics with your group to see relative effort and consistency.")
        
        users_list = list(USERS.keys())
        comparison_data = []
        
        for user in users_list:
            df_user = get_daily_logs(user)
            df_habits_user = get_habit_logs(user)
            
            comp_entry = {
                "User": user.title(),
                "Total Logs": len(df_user),
                "Avg Hours": df_user['hours'].mean().round(2) if not df_user.empty else 0.0,
                "Avg Prod": df_user['productivity'].mean().round(2) if not df_user.empty else 0.0,
                "Habit Days": len(df_habits_user)
            }
            comparison_data.append(comp_entry)

        df_comp = pd.DataFrame(comparison_data)

        def highlight_max(s):
            is_max = s == s.max()
            return ['background-color: #d4edda; color: #155724; font-weight: bold;' if v else '' for v in is_max]

        st.dataframe(
            df_comp.style.apply(highlight_max, subset=['Avg Hours', 'Avg Prod', 'Total Logs', 'Habit Days']),
            use_container_width=True
        )


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
        "Graphs & Insights": graphs_and_insights
    }
    
    if page in page_functions:
        page_functions[page]()
    else:
        st.error("Page not found!")
