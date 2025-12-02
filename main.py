import streamlit as st
from firebase import read, write, update, push # Assuming these are defined elsewhere
from datetime import datetime, timedelta, date
import pandas as pd
import plotly.express as px
# from fpdf import FPDF # Removed unused import

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Performance Tracker Pro", layout="wide", initial_sidebar_state="collapsed")

# Load CSS
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("styles.css not found. Skipping CSS load.")

# -----------------------------
# FIXED LOGIN CREDENTIALS
# -----------------------------
USERS = {
    "manav": "1234",
    "kaaysha": "1234"
}

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def get_daily_logs(user):
    """Fetches daily work logs and converts to DataFrame."""
    data = read(f"daily/{user}") or {}
    if data:
        # Include Firebase key for potential deletion/update
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()])
        # Ensure date is a proper datetime object for sorting/filtering
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False).reset_index(drop=True)
        return df
    return pd.DataFrame()

def get_habit_logs(user):
    """Fetches habit logs and converts to DataFrame."""
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
    st.title("🔑 Login to Your Performance Dashboard")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if username in USERS and USERS[username] == password:
            st.session_state["user"] = username
            st.session_state["page"] = "Dashboard" # Set default page
            st.rerun()
        else:
            st.error("Invalid credentials")
    
    st.info("Demo users: **manav** / **1234** or **kaaysha** / **1234**")


# -----------------------------
# NAVIGATION BAR
# -----------------------------
def navbar():
    st.markdown("---")
    # Increased columns for cleaner layout and added 'Planner'
    pages = [
        "Dashboard", "Daily Planner", "Daily Log", "Projects", "Learning", 
        "Weekly Goals", "Habits", "Graphs & Insights"
    ]
    
    # Add Logout button separately
    cols = st.columns([0.8] * len(pages) + [0.1]) 
    
    for idx, pg in enumerate(pages):
        # Highlight active page
        button_type = "primary" if st.session_state.get("page") == pg else "secondary"
        if cols[idx].button(pg, type=button_type):
            st.session_state["page"] = pg
            st.rerun()
            
    if cols[-1].button("Logout 🚪"):
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
    col1.metric("Total Daily Logs", len(df_work), help="Total number of daily work entries.")
    col2.metric("Active Projects", len(df_proj[df_proj['progress'] < 100]) if not df_proj.empty else 0)
    col3.metric("Total Learnings", len(df_learn))
    col4.metric("Habit Days Logged", len(df_habits))
    
    st.markdown("---")
    
    # 2. Daily Log Snapshot (Last 7 Days)
    st.subheader("🗓️ Last 7 Days Summary")
    
    if not df_work.empty:
        df_work_recent = df_work[df_work['date'] >= (datetime.now() - timedelta(days=7))]
        
        if not df_work_recent.empty:
            
            # Calculate Averages for the last 7 days
            avg_hours = df_work_recent['hours'].mean().round(1)
            avg_prod = df_work_recent['productivity'].mean().round(2)
            avg_energy = df_work_recent['energy'].mean().round(2)

            # Metrics for recent performance
            c1, c2, c3 = st.columns(3)
            c1.metric("Avg Hours/Day (7D)", f"{avg_hours}", help="Average hours worked in the last 7 days.")
            c2.metric("Avg Productivity (7D)", f"{avg_prod}/5", help="Average Productivity rating (1-5) in the last 7 days.")
            c3.metric("Avg Energy (7D)", f"{avg_energy}/5", help="Average Energy rating (1-5) in the last 7 days.")
            
            # Simple plot for trend
            fig = px.bar(df_work_recent.sort_values(by='date'), 
                         x='date', y='hours', 
                         title='Hours Logged in the Last Week', 
                         template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No work logs in the last 7 days.")
    else:
        st.info("Start logging your daily work to see a summary here!")

# -----------------------------
# DAILY PLANNER (NEW)
# -----------------------------
def daily_planner():
    st.header("📝 Daily Pre-Work Planner", divider='orange')
    st.write("Plan your main tasks, focus areas, and time allocation before you start working.")
    
    today = datetime.now().strftime("%Y-%m-%d")
    planner_key = f"planner/{st.session_state['user']}/{today}"
    current_plan = read(planner_key) or {}

    with st.form("planner_form"):
        st.subheader(f"Plan for Today: **{today}**")
        
        # Priority Tasks (1-3)
        p1 = st.text_input("🎯 P1 (Most Important Task)", value=current_plan.get('p1', ''))
        p2 = st.text_input("🔹 P2 (Secondary Task)", value=current_plan.get('p2', ''))
        p3 = st.text_input("🔸 P3 (Minor Task/Skill)", value=current_plan.get('p3', ''))
        
        # Estimated Hours
        est_hours = st.number_input("Est. Total Hours of Deep Work", 0.0, 12.0, value=current_plan.get('est_hours', 4.0))

        # Focus Area Dropdown
        focus_area = st.selectbox(
            "Main Focus Area Today",
            ["Academics/Review", "Project Work", "Skill Learning (DSA/AI)", "Job Prep"],
            index=["Academics/Review", "Project Work", "Skill Learning (DSA/AI)", "Job Prep"].index(current_plan.get('focus_area', 'Project Work'))
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
            write(planner_key, plan) # Use 'write' to overwrite/update for the current day
            st.success("Daily Plan Saved! Now go execute it.")
            st.experimental_rerun()
            
    # Display the current plan
    if current_plan:
        st.markdown("---")
        st.subheader("Current Plan")
        st.markdown(f"**Focus:** {current_plan['focus_area']}")
        st.markdown(f"**Est. Hours:** {current_plan['est_hours']} hrs")
        st.markdown(f"* **P1:** {current_plan['p1']}")
        st.markdown(f"* **P2:** {current_plan['p2']}")
        st.markdown(f"* **P3:** {current_plan['p3']}")

# -----------------------------
# DAILY WORK PAGE (Renamed to Daily Log)
# -----------------------------
def daily_work():
    st.header("✍️ Daily Work Log", divider='blue')

    with st.form("daily_log_form"):
        st.subheader("Log Your Performance")
        
        task = st.text_area("Describe **what you accomplished today** (specifics are better)")
        hours = st.number_input("Actual Hours Worked", 0.0, 24.0, 0.0, step=0.5)

        st.markdown("---")
        # Use columns for a cleaner rating UI
        col1, col2, col3 = st.columns(3)
        mood = col1.slider("Mood (1=Bad, 5=Great)", 1, 5, 3)
        productivity = col2.slider("Productivity (1=Low, 5=High)", 1, 5, 3)
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
            # Use push for a new unique entry key
            push(f"daily/{st.session_state['user']}", entry)
            st.success("Daily work saved! Check the 'Graphs & Insights' for your trend.")

    st.markdown("---")
    st.subheader("History (Recent Logs)")
    df = get_daily_logs(st.session_state['user'])
    if not df.empty:
        # Display key columns only and limit to 10 entries
        st.dataframe(df[['date', 'hours', 'task', 'productivity', 'energy']].head(10), 
                     use_container_width=True, 
                     hide_index=True)
    else:
        st.info("No work history found.")


# -----------------------------
# PROJECT TRACKER
# -----------------------------
def projects():
    st.header("⚙️ Project Tracker", divider='blue')

    with st.expander("Add/Update Project"):
        with st.form("project_form"):
            name = st.text_input("Project Name")
            progress = st.slider("Progress (%)", 0, 100, 0)
            notes = st.text_area("Project Notes/Next Steps")
            
            submitted = st.form_submit_button("Save Project", type="primary")

            if submitted:
                entry = {
                    "name": name,
                    "progress": progress,
                    "notes": notes,
                    "updated": datetime.now().strftime("%Y-%m-%d")
                }
                # To implement *updates* efficiently, you'd need a key for existing projects.
                # For simplicity, this uses PUSH (adds new) or relies on manual Firebase key management.
                # A more robust solution would involve a project_id/name lookup.
                push(f"projects/{st.session_state['user']}", entry) 
                st.success("Project saved/updated.")
                st.experimental_rerun()

    st.subheader("Project Status")
    data = read(f"projects/{st.session_state['user']}") or {}
    
    if data:
        # Include the key to potentially implement 'delete' or 'update' functionality later
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()]) 
        
        # Use a better visual representation
        st.dataframe(df[['name', 'progress', 'updated', 'notes']], use_container_width=True)
        
        # Simple Progress Visualization
        fig = px.bar(df.sort_values(by='progress', ascending=False), 
                     x='name', y='progress', 
                     color='progress', 
                     title='Project Progress Overview', 
                     template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No projects added yet.")


# -----------------------------
# LEARNING TRACKER
# -----------------------------
def learning():
    st.header("🧠 Learning Log", divider='blue')

    with st.form("learning_form"):
        topic = st.text_input("What specific concept/skill did you learn?")
        source = st.text_input("Source (e.g., Coursera NLP module, LeetCode 100, YouTube - DP Tutorial)")
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
            st.success("Learning saved. Keep track of those skills!")
            st.experimental_rerun()

    st.subheader("Learning History")
    data = read(f"learning/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame(data.values())
        df = df.sort_values(by='date', ascending=False)
        st.dataframe(df[['date', 'topic', 'source', 'keywords']], use_container_width=True)
        
        # Show keyword distribution (Productivity Enhancement)
        all_keywords = [item for sublist in df['keywords'].dropna() for item in sublist]
        if all_keywords:
            kw_series = pd.Series(all_keywords).value_counts().head(10)
            fig = px.pie(kw_series, values=kw_series.values, names=kw_series.index, title='Top 10 Learning Focus Areas')
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

    with st.expander("Add a New Goal"):
        with st.form("goal_form"):
            goal = st.text_input("Goal Title (e.g., Finish Chapter 5, Complete 5 LeetCode Mediums)")
            target = st.text_area("Target Description/Success Criteria")
            
            # Use 'Status' to track progress
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

    st.subheader("All Goals")
    data = read(f"goals/{st.session_state['user']}") or {}
    if data:
        df = pd.DataFrame([dict(key=k, **v) for k, v in data.items()])
        df = df.sort_values(by=['week', 'status'], ascending=[False, True])
        
        # Display goals for the current week first
        st.markdown(f"**Week {current_week} Goals:**")
        current_week_df = df[df['week'] == current_week]
        
        if not current_week_df.empty:
            st.dataframe(current_week_df[['goal', 'status', 'target']], use_container_width=True, hide_index=True)

            # Display a progress summary
            status_counts = current_week_df['status'].value_counts()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Goals", len(current_week_df))
            col2.metric("Completed ✅", status_counts.get("Completed", 0))
            col3.metric("In Progress ⏳", status_counts.get("In Progress", 0))
            
            # --- Simple Goal Update (Productivity Enhancement) ---
            st.markdown("---")
            st.markdown("**Quick Status Update**")
            
            # Use a selectbox to pick a goal to update
            goal_to_update = st.selectbox(
                "Select Goal to Update Status", 
                current_week_df['goal'].tolist()
            )
            new_status = st.selectbox(
                "New Status", 
                ["To Do", "In Progress", "Completed", "Failed/Deferred"],
                index=["To Do", "In Progress", "Completed", "Failed/Deferred"].index(current_week_df[current_week_df['goal'] == goal_to_update]['status'].iloc[0])
            )
            
            if st.button("Update Goal Status"):
                # Find the Firebase key for the selected goal
                key_to_update = current_week_df[current_week_df['goal'] == goal_to_update]['key'].iloc[0]
                update(f"goals/{st.session_state['user']}/{key_to_update}", {"status": new_status})
                st.success(f"Status for '{goal_to_update}' updated to **{new_status}**.")
                st.experimental_rerun()
        else:
            st.info(f"No goals set for week {current_week} yet.")

        # Optionally show past goals
        if len(df[df['week'] != current_week]) > 0:
             if st.checkbox("Show Past Goals"):
                st.dataframe(df[df['week'] != current_week][['week', 'goal', 'status']], use_container_width=True)
    else:
        st.info("No goals added yet.")


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
    "Health Habit (Exercise/Walk)", # Refined text
    "No Phone 1 Hour Study",
    "Wake Up on Time"
]

def habits():
    st.header("✅ Daily Habit Tracker", divider='blue')

    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if a log already exists for today
    df_habits = get_habit_logs(st.session_state['user'])
    today_log = df_habits[df_habits['date'].dt.strftime('%Y-%m-%d') == today]
    
    if not today_log.empty:
        st.info(f"Habits for **{today}** are already logged.")
        current_checked = today_log['habits'].iloc[0]
    else:
        current_checked = {}

    with st.form("habit_form"):
        st.subheader(f"Check the habits you completed today ({today}):")
        checked = {}

        for habit in HABITS:
            # Pre-populate with existing data if available
            default_state = current_checked.get(habit, False)
            checked[habit] = st.checkbox(habit, value=default_state)

        # Change button label based on action
        button_label = "Update Habits" if not today_log.empty else "Save Habits"
        if st.form_submit_button(button_label, type="primary"):
            entry = {
                "date": today,
                "habits": checked
            }
            
            if not today_log.empty:
                # Update existing entry
                key_to_update = today_log['key'].iloc[0]
                update(f"habits/{st.session_state['user']}/{key_to_update}", entry)
                st.success(f"Habit log for {today} updated!")
            else:
                # Save new entry
                push(f"habits/{st.session_state['user']}", entry)
                st.success("Habit log saved!")
                
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Habit History & Streak")
    
    if not df_habits.empty:
        # Calculate consistency/streak (Productivity Enhancement)
        df_habits['total_done'] = df_habits['habits'].apply(lambda x: sum(x.values()))
        
        # Simple Habit Consistency Plot
        fig = px.bar(df_habits.sort_values(by='date', ascending=True).tail(14), 
                     x='date', y='total_done', 
                     title='Habits Completed (Last 14 Days)',
                     labels={'total_done': 'Number of Habits Done'},
                     template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)

        # Show raw data
        st.dataframe(df_habits[['date', 'total_done']].tail(10), use_container_width=True, hide_index=True)
    else:
        st.info("No habit history found.")


# -----------------------------
# GRAPHS & INSIGHTS (Combined Graphs, Suggestions, Compare, Calendar)
# -----------------------------
def graphs_and_insights():
    st.header("📊 Graphs & Insights", divider='blue')
    
    tab1, tab2, tab3 = st.tabs(["Performance Graphs", "AI Suggestions", "Comparison"])

    # --- TAB 1: Performance Graphs ---
    with tab1:
        st.subheader("Daily Log Trends")
        df = get_daily_logs(st.session_state['user'])
    
        if df.empty:
            st.info("No data to graph yet.")
        else:
            # 1. Hours Worked
            fig_hours = px.line(df, x="date", y="hours", title="Hours Worked Over Time", template='plotly_white')
            st.plotly_chart(fig_hours, use_container_width=True)
            
            # 2. Mood/Productivity/Energy Over Time
            df_melted = df.melt(id_vars='date', value_vars=['mood', 'productivity', 'energy'], var_name='Metric', value_name='Rating')
            fig_ratings = px.line(df_melted, x="date", y="Rating", color='Metric', title="Mood, Productivity, & Energy Trends", template='plotly_white')
            st.plotly_chart(fig_ratings, use_container_width=True)
            
            # 3. Correlation (Productivity Enhancement)
            st.markdown("---")
            st.subheader("Correlation Analysis")
            st.write("Does higher **Mood** correlate with higher **Productivity**?")
            fig_corr = px.scatter(df, x='mood', y='productivity', 
                                  title='Mood vs. Productivity Scatter Plot', 
                                  color='hours', # Color by hours worked
                                  template='plotly_white')
            st.plotly_chart(fig_corr, use_container_width=True)

    # --- TAB 2: AI Suggestions ---
    with tab2:
        st.subheader("Improvement Suggestions (Based on Your Logs)")

        work = read(f"daily/{st.session_state['user']}") or {}
        habits = read(f"habits/{st.session_state['user']}") or {}

        if not work:
            st.info("Add some logs to generate suggestions.")
            return

        suggestions = []
        
        # Calculations (using DataFrames for clean aggregation)
        df_work = get_daily_logs(st.session_state['user'])
        avg_productivity = df_work['productivity'].mean().round(2)
        avg_energy = df_work['energy'].mean().round(2)
        
        # 1. Productivity Analysis
        if avg_productivity < 3.5:
             suggestions.append(f"**Average Productivity is low ({avg_productivity}/5).** Try implementing the **Pomodoro technique** or dedicated **deep work sessions** to increase focus.")
        elif avg_productivity >= 4.5:
             suggestions.append(f"**Excellent Productivity!** Keep doing what you're doing. Consider taking a **challenging project** to maximize this performance.")

        # 2. Energy Analysis
        if avg_energy < 3:
            suggestions.append(f"**Average Energy is low ({avg_energy}/5).** Prioritize **sleep and proper nutrition**. Low energy directly impacts deep work capacity.")

        # 3. Habit Consistency
        if habits:
            df_habits = get_habit_logs(st.session_state['user'])
            if not df_habits.empty:
                df_habits['total_done'] = df_habits['habits'].apply(lambda x: sum(x.values()))
                
                recent_habits = df_habits.head(7) # Last 7 days
                avg_habits = recent_habits['total_done'].mean().round(1)
                
                if avg_habits < 5:
                    suggestions.append(f"**Recent Habit Completion is only {avg_habits}/{len(HABITS)} per day.** Focus on completing at least 5 habits daily for better consistency and skill-stacking.")

        # 4. Low Hours
        avg_hours = df_work['hours'].mean().round(2)
        if avg_hours < 3.0:
            suggestions.append(f"**Average Daily Hours are low ({avg_hours} hrs).** Aim for a minimum of 4-5 focused hours per day to see significant progress in your preparation.")
            
        st.write("### Personalized Insights:")
        for s in suggestions:
            st.markdown(f"**💡 {s}**")

    # --- TAB 3: Comparison ---
    with tab3:
        st.subheader("Performance Comparison")
        st.write("Compare key metrics with other users (e.g., Manav vs Kaaysha).")
        
        users = ["manav", "kaaysha"]
        comparison_data = []
        
        for user in users:
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

        # Highlight better performance (Productivity Enhancement)
        def highlight_max(s):
            is_max = s == s.max()
            return ['background-color: lightgreen' if v else '' for v in is_max]

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

    # Default to Dashboard if 'page' is not set
    page = st.session_state.get("page", "Dashboard") 

    # Consolidated Page Logic
    page_functions = {
        "Dashboard": dashboard,
        "Daily Planner": daily_planner, # New planning feature
        "Daily Log": daily_work, # Renamed from Daily Work
        "Projects": projects,
        "Learning": learning,
        "Weekly Goals": weekly_goals,
        "Habits": habits,
        "Graphs & Insights": graphs_and_insights # Consolidated graphs, suggestions, and comparison
    }
    
    if page in page_functions:
        page_functions[page]()
    else:
        st.error("Page not found!")
