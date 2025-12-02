import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import firebase_admin
from firebase_admin import credentials, db
import json
import uuid
from collections import defaultdict

# ==========================================================
# 1. CONFIGURATION AND FIREBASE SETUP
# ==========================================================

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI/DS Progress Tracker", layout="wide", initial_sidebar_state="expanded")

# --- FIXED USERS ---
# Only Manav and Kaaysha are authorized.
USERS = {
    "manav": "1234",
    "kaaysha": "1234",
}
PEER_USERS = list(USERS.keys())

# --- HABITS LIST ---
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

# --- FIREBASE SETUP (Securely reading from st.secrets) ---
try:
    if 'firebase_key' in st.secrets and 'database_url' in st.secrets:
        # Load the key from st.secrets and parse the JSON string
        key_dict = json.loads(st.secrets['firebase_key'])
        cred = credentials.Certificate(key_dict)
        db_url = st.secrets['database_url']

    else:
        st.error("FATAL ERROR: Firebase secrets not found. Please ensure 'firebase_key' and 'database_url' are configured in st.secrets.")
        st.stop() # Stops execution if secrets aren't found.

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {'databaseURL': db_url})
    
    database_ref = db.reference('/')
    
except Exception as e:
    # Handles the case where Firebase might be initialized twice (common in Streamlit)
    if "already been initialized" not in str(e):
        st.error(f"FATAL ERROR: Firebase Initialization Failed. Check your JSON format in secrets. Error: {e}")
        st.stop() 

# -----------------------------
# DESIGN/STYLES (Optional: Requires styles.css in the same directory)
# -----------------------------
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass 

# ==========================================================
# 2. DATABASE WRAPPER FUNCTIONS & CACHING
# ==========================================================

def fire_read(path):
    """Reads data from Firebase."""
    return db.reference(path).get()

def fire_write(path, data):
    """Writes data to Firebase."""
    db.reference(path).set(data)
    return True

def fire_update(path, data):
    """Updates data in Firebase."""
    db.reference(path).update(data)
    return True

def fire_push(path, data):
    """Pushes new data with a unique key and returns the key."""
    new_ref = db.reference(path).push(data)
    return new_ref.key

@st.cache_data(ttl=600)
def get_daily_logs(user):
    """Fetches and processes daily logs."""
    data = fire_read(f"daily/{user}") or {}
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
    """Fetches and processes habit logs."""
    data = fire_read(f"habits/{user}") or {}
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False).reset_index(drop=True)
        return df
    return pd.DataFrame()


# ==========================================================
# 3. PAGE FUNCTIONS
# ==========================================================

# --- LOGIN PAGE ---
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
    
    st.info("Available users: **manav** / **kaaysha**. Password: **1234**")


# --- DASHBOARD ---
def dashboard():
    st.header(f"🚀 Welcome Back, **{st.session_state['user'].title()}**!", divider='blue')

    df_work = get_daily_logs(st.session_state['user'])
    df_proj = pd.DataFrame((fire_read(f"projects/{st.session_state['user']}") or {}).values())
    
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Deep Work Logs", len(df_work))
    col2.metric("Active Projects", len(df_proj[df_proj['progress'] < 100]) if not df_proj.empty else 0)
    col3.metric("Avg Productivity (All Time)", f"{df_work['productivity'].mean().round(2) if not df_work.empty else 0.0}/5")
    
    st.markdown("---")
    
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

# --- DAILY PLANNER ---
def daily_planner():
    st.header("📝 Daily Pre-Work Planner", divider='orange')
    today = datetime.now().strftime("%Y-%m-%d")
    planner_key = f"planner/{st.session_state['user']}/{today}"
    current_plan = fire_read(planner_key) or {}

    with st.form("planner_form"):
        st.subheader(f"Plan for Today: **{today}**")
        p1 = st.text_input("🎯 P1 (Most Important/Deep Work Task)", value=current_plan.get('p1', ''))
        p2 = st.text_input("🔹 P2 (Secondary Task/Review)", value=current_plan.get('p2', ''))
        p3 = st.text_input("🔸 P3 (Minor Task/Skill Practice)", value=current_plan.get('p3', ''))
        est_hours = st.number_input("Est. Total Hours of Deep Work", 0.0, 12.0, value=current_plan.get('est_hours', 4.0), step=0.5)

        focus_options = ["DSA/Algorithms", "AI/ML Project", "Semester Subject Review", "Skill Development (e.g., DevOps)", "Other"]
        focus_area = st.selectbox("Main Focus Area Today", focus_options, index=focus_options.index(current_plan.get('focus_area', 'DSA/Algorithms')) if current_plan.get('focus_area') in focus_options else 0)
        
        submitted = st.form_submit_button("Save Today's Plan", type="primary")

        if submitted:
            plan = {"date": today, "p1": p1, "p2": p2, "p3": p3, "est_hours": est_hours, "focus_area": focus_area}
            fire_write(planner_key, plan)
            st.success("Daily Plan Saved! Ready for execution.")
            st.cache_data.clear()
            st.experimental_rerun()
            
    if current_plan:
        st.markdown("---")
        st.subheader("Current Plan Summary")
        st.markdown(f"**Focus Area:** **{current_plan['focus_area']}**")
        st.markdown(f"**Estimated Hours:** `{current_plan['est_hours']} hrs`")


# --- DAILY WORK LOG ---
def daily_work():
    st.header("✍️ Daily Work Log", divider='blue')

    with st.form("daily_log_form"):
        st.subheader("Log Your Accomplishments")
        task = st.text_area("Describe **what specific task you completed** and **from where**.")
        hours = st.number_input("Actual Deep Work Hours", 0.0, 24.0, 0.0, step=0.5)

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        mood = col1.slider("Mood (1=Bad, 5=Great)", 1, 5, 3)
        productivity = col2.slider("Productivity (1=Low Focus, 5=High Focus)", 1, 5, 3)
        energy = col3.slider("Energy (1=Drained, 5=Energized)", 1, 5, 3)

        submitted = st.form_submit_button("Save Log", type="primary")

        if submitted:
            entry = {"task": task, "hours": hours, "mood": mood, "productivity": productivity, "energy": energy, "date": datetime.now().strftime("%Y-%m-%d")}
            fire_push(f"daily/{st.session_state['user']}", entry)
            st.success("Daily work saved! Check the 'Graphs & Insights' for your trend.")
            st.cache_data.clear()
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("History (Recent Logs)")
    df = get_daily_logs(st.session_state['user'])
    if not df.empty:
        st.dataframe(df[['date', 'hours', 'task', 'productivity', 'energy']].head(10).rename(columns={'hours': 'Hours', 'task': 'Task Description', 'productivity': 'Prod', 'energy': 'Energy'}), use_container_width=True, hide_index=True)
    else:
        st.info("No work history found.")


# --- PROJECT TRACKER ---
def projects():
    st.header("⚙️ Project Tracker", divider='blue')

    with st.expander("Add/Update Project", expanded=False):
        with st.form("project_form"):
            name = st.text_input("Project Name (e.g., 4th Sem AI Project)")
            progress = st.slider("Progress (%)", 0, 100, 0)
            notes = st.text_area("Pending: What is left to be done?")
            
            submitted = st.form_submit_button("Save Project", type="primary")

            if submitted:
                entry = {"name": name, "progress": progress, "notes": notes, "updated": datetime.now().strftime("%Y-%m-%d")}
                fire_push(f"projects/{st.session_state['user']}", entry) 
                st.success("Project saved/updated.")
                st.cache_data.clear()
                st.experimental_rerun()

    st.subheader("Project Status (Pending Work)")
    data = fire_read(f"projects/{st.session_state['user']}") or {}
    
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()]) 
        st.dataframe(df[['name', 'progress', 'updated', 'notes']].rename(columns={'name': 'Project', 'progress': 'Progress (%)', 'updated': 'Last Update', 'notes': 'Pending Tasks'}), use_container_width=True, hide_index=True)
        fig = px.bar(df.sort_values(by='progress', ascending=False), x='name', y='progress', color='progress', color_continuous_scale=px.colors.sequential.Teal, title='Project Progress Overview', template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No projects added yet.")


# --- LEARNING LOG ---
def learning():
    st.header("🧠 Learning Log: Concepts & Resources", divider='blue')

    with st.form("learning_form"):
        topic = st.text_input("What specific concept/skill did you learn/revise?")
        source = st.text_input("Source (e.g., Coursera NLP module, Textbook Chapter 6)")
        link = st.text_input("Resource Link (Optional)")
        keywords = st.text_input("Keywords (e.g., Python, DP, OOP, React)", help="Separate with commas")
        
        submitted = st.form_submit_button("Save Learning", type="primary")

        if submitted:
            entry = {"topic": topic, "source": source, "link": link, "keywords": [k.strip() for k in keywords.split(',')], "date": datetime.now().strftime("%Y-%m-%d")}
            fire_push(f"learning/{st.session_state['user']}", entry)
            st.success("Learning saved. Track your skills!")
            st.cache_data.clear()
            st.experimental_rerun()

    st.subheader("Learning History")
    data = fire_read(f"learning/{st.session_state['user']}") or {}
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


# --- WEEKLY GOALS ---
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
                entry = {"goal": goal, "target": target, "week": current_week, "status": status, "created": datetime.now().strftime("%Y-%m-%d")}
                fire_push(f"goals/{st.session_state['user']}", entry)
                st.success("Goal added! Good luck.")
                st.cache_data.clear()
                st.experimental_rerun()

    st.subheader("Current Week Goals")
    data = fire_read(f"goals/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()])
        df['key'] = data.keys() 
        df = df.sort_values(by=['week', 'status'], ascending=[False, True])
        current_week_df = df[df['week'] == current_week]
        
        if not current_week_df.empty:
            st.dataframe(current_week_df[['goal', 'status', 'target']].rename(columns={'goal': 'Goal', 'target': 'Details'}), use_container_width=True, hide_index=True)

            status_counts = current_week_df['status'].value_counts()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Goals", len(current_week_df))
            c2.metric("Completed ✅", status_counts.get("Completed", 0))
            
            st.markdown("---")
            st.markdown("**Quick Status Update**")
            
            update_data = current_week_df[current_week_df['status'] != 'Completed']
            if not update_data.empty:
                goal_options = update_data['goal'].tolist()
                col_goal, col_status, col_button = st.columns([3, 2, 1])
                goal_to_update = col_goal.selectbox("Select Goal to Update Status", goal_options)
                
                initial_status = update_data[update_data['goal'] == goal_to_update]['status'].iloc[0]
                status_options = ["To Do", "In Progress", "Completed", "Failed/Deferred"]
                new_status = col_status.selectbox("New Status", status_options, index=status_options.index(initial_status))
                
                if col_button.button("Update"):
                    key_to_update = current_week_df[current_week_df['goal'] == goal_to_update]['key'].iloc[0]
                    fire_update(f"goals/{st.session_state['user']}/{key_to_update}", {"status": new_status})
                    st.success(f"Status for '{goal_to_update}' updated to **{new_status}**.")
                    st.cache_data.clear()
                    st.experimental_rerun()
            else:
                st.info("All current goals are completed or no goals set!")
        else:
            st.info(f"No goals set for week {current_week} yet.")


# --- HABIT TRACKER ---
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
            entry = {"date": today, "habits": checked}
            
            if is_logged:
                key_to_update = today_log['key'].iloc[0]
                fire_update(f"habits/{st.session_state['user']}/{key_to_update}", entry)
                st.success(f"Habit log for {today} updated!")
            else:
                fire_push(f"habits/{st.session_state['user']}", entry)
                st.success("Habit log saved!")
                
            st.cache_data.clear()
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
    else:
        st.info("No habit history found.")


# --- PEER REVIEW ---
def peer_review():
    st.header("🤝 Peer Review and Accountability", divider='violet')
    st.write("View the current status, today's plan, and recent activity of your group members.")

    current_user = st.session_state['user']
    other_users = [u for u in PEER_USERS if u != current_user]
    today = datetime.now().strftime("%Y-%m-%d")

    for peer in other_users:
        st.markdown(f"### 🧑‍💻 {peer.title()}'s Activity")
        
        col_plan, col_log = st.columns(2)

        # 1. Today's Plan
        with col_plan:
            plan_key = f"planner/{peer}/{today}"
            peer_plan = fire_read(plan_key) or {}
            
            st.markdown("#### 🎯 Today's Focus (Planned)")
            if peer_plan:
                st.info(f"**Focus Area:** {peer_plan.get('focus_area', 'N/A')}")
                st.markdown(f"**Est. Hours:** `{peer_plan.get('est_hours', 0.0)} hrs`")
                st.markdown(f"**P1 (Deep Work):** {peer_plan.get('p1', 'N/A')}")
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
            peer_projects = fire_read(f"projects/{peer}") or {}
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
        
        st.markdown("---")


# --- GRAPHS & INSIGHTS ---
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

    # --- TAB 2: AI Suggestions ---
    with tab2:
        st.subheader("Improvement Suggestions (Based on Your Logs)")

        df_work = get_daily_logs(st.session_state['user'])
        
        if df_work.empty:
            st.info("Add some logs to generate suggestions.")
            return

        suggestions = []
        avg_productivity = df_work['productivity'].mean().round(2)
        avg_energy = df_work['energy'].mean().round(2)

        if avg_productivity < 3.8:
             suggestions.append(f"**Productivity is moderate ({avg_productivity}/5).** Try implementing the **Pomodoro technique** or dedicated **deep work sessions** to minimize distractions.")

        if avg_energy < 3.5:
            suggestions.append(f"**Average Energy is low ({avg_energy}/5).** Prioritize **sleep (7-8 hours)** and hydration. Low energy severely limits the capacity for deep work.")

        st.write("### Personalized Insights:")
        for s in suggestions:
            st.markdown(f"**💡 {s}**")

    # --- TAB 3: Comparison ---
    with tab3:
        st.subheader("Peer Performance Comparison (Motivational View)")
        
        comparison_data = []
        
        for user in PEER_USERS:
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

        st.dataframe(df_comp.style.apply(highlight_max, subset=['Avg Hours', 'Avg Prod', 'Total Logs', 'Habit Days']), use_container_width=True)


# ==========================================================
# 4. MAIN ROUTER
# ==========================================================
if "user" not in st.session_state:
    login_page()
else:
    # Sidebar Navigation
    st.sidebar.title("📚 Student Progress Tracker")
    st.sidebar.markdown(f"**Logged in as: {st.session_state['user'].title()}**")
    
    page_functions = {
        "Dashboard": dashboard,
        "Daily Planner": daily_planner,
        "Daily Log": daily_work,
        "Projects": projects,
        "Learning": learning,
        "Weekly Goals": weekly_goals,
        "Habits": habits,
        "Peer Review": peer_review,
        "Graphs & Insights": graphs_and_insights
    }

    if "page" not in st.session_state:
         st.session_state["page"] = "Dashboard"

    selected_page = st.sidebar.selectbox(
        "Navigation",
        list(page_functions.keys()),
        index=list(page_functions.keys()).index(st.session_state["page"])
    )
    
    st.session_state["page"] = selected_page

    # Logout button in sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout 🚪"):
        st.session_state.clear()
        st.rerun()

    # Call the selected page function
    page_functions[st.session_state["page"]]()
