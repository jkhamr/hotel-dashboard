import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Connect to Google Sheets
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)

client = gspread.authorize(creds)

# Open your sheet
sheet = client.open("Hotel Message").sheet1

# ✅ ONLY ONE, and AFTER imports
st.set_page_config(
    page_title="Hotel Operations",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏨 Hotel Operations Dashboard")

# ------------------ INITIALIZE SESSION STATE ------------------ #

if "messages" not in st.session_state:
    st.session_state.messages = []

if "tasks_data" not in st.session_state:
    st.session_state.tasks_data = [
        {"task": "Restock breakfast buffet", "team": "Kitchen", "priority": "High", "status": "Open"},
        {"task": "Prepare VIP welcome kit", "team": "Front Desk", "priority": "Medium", "status": "Open"},
        {"task": "Linen count verification", "team": "Housekeeping", "priority": "Low", "status": "Done"},
    ]

if "rooms_data" not in st.session_state:
    st.session_state.rooms_data = [
        {"room": "101", "floor": "1", "status": "Ready", "housekeeper": "Maria"},
        {"room": "102", "floor": "1", "status": "Dirty", "housekeeper": "Liam"},
        {"room": "103", "floor": "1", "status": "Occupied", "housekeeper": "Priya"},
        {"room": "201", "floor": "2", "status": "Ready", "housekeeper": "Noah"},
        {"room": "202", "floor": "2", "status": "Maintenance", "housekeeper": "Ava"},
        {"room": "203", "floor": "2", "status": "Dirty", "housekeeper": "Maya"},
    ]

if "maintenance_data" not in st.session_state:
    st.session_state.maintenance_data = [
        {"issue": "AC not cooling", "room": "202", "priority": "High", "owner": "Engineering"},
        {"issue": "Flickering light", "room": "103", "priority": "Medium", "owner": "Electrical"},
        {"issue": "Leaky tap", "room": "101", "priority": "Low", "owner": "Plumbing"},
    ]

# ------------------ MESSAGE SYSTEM ------------------ #

st.markdown("## 📢 Staff Messages")

# Use a form to properly clear the input
with st.form(key="message_form", clear_on_submit=True):
    new_message = st.text_input("Write a message", key="message_input")
    submit_button = st.form_submit_button("Post Message")
    
    if submit_button and new_message:
    time_now = datetime.datetime.now().strftime("%I:%M %p")

    sheet.append_row([new_message, time_now])

    st.rerun()

    # Save to Google Sheet
    sheet.append_row([new_message, time_now])

    st.rerun()

# Display messages
records = sheet.get_all_records()

if records:
    for row in reversed(records[-10:]):  # last 10 messages
        st.markdown(f"""
            <div style='
                background:white;
                padding:12px;
                border-radius:12px;
                margin-bottom:10px;
                box-shadow:0 2px 6px rgba(0,0,0,0.08);
            '>
                💬 {row['Message']}<br>
                <small style='color:gray;'>🕒 {row['Time']}</small>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("No messages yet. Post the first message!")

st.divider()

# ------------------ CONVERT TO DATAFRAMES ------------------ #

rooms_df = pd.DataFrame(st.session_state.rooms_data)
maintenance_df = pd.DataFrame(st.session_state.maintenance_data)
tasks_df = pd.DataFrame(st.session_state.tasks_data)

# ------------------ FILTERS ------------------ #

st.markdown("### 🔍 Filters")
f1, f2, f3 = st.columns(3)

selected_floor = f1.selectbox("Floor", ["All"] + sorted(rooms_df["floor"].unique()))
selected_room_status = f2.selectbox("Room Status", ["All"] + sorted(rooms_df["status"].unique()))
selected_task_team = f3.selectbox("Task Team", ["All"] + sorted(tasks_df["team"].unique()))

# Apply filters
filtered_rooms = rooms_df.copy()
if selected_floor != "All":
    filtered_rooms = filtered_rooms[filtered_rooms["floor"] == selected_floor]
if selected_room_status != "All":
    filtered_rooms = filtered_rooms[filtered_rooms["status"] == selected_room_status]

filtered_tasks = tasks_df.copy()
if selected_task_team != "All":
    filtered_tasks = filtered_tasks[filtered_tasks["team"] == selected_task_team]

# ------------------ SUMMARY ------------------ #

st.markdown("### 📊 Summary")
s1, s2, s3, s4 = st.columns(4)

s1.metric("Total Rooms", len(rooms_df))
s2.metric("Ready Rooms", (rooms_df['status'] == 'Ready').sum(), 
          delta=f"{(rooms_df['status'] == 'Ready').sum() / len(rooms_df) * 100:.0f}%")
s3.metric("Open Tasks", (tasks_df['status'] == 'Open').sum())
s4.metric("Maintenance Issues", len(maintenance_df))

st.divider()

# ------------------ TABS ------------------ #

tabs = st.tabs(["📋 Tasks", "🚪 Rooms", "🔧 Maintenance", "👥 Staffing"])

# ---------- TASKS TAB ----------
with tabs[0]:
    st.markdown("### Task Board")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Task", use_container_width=True):
            st.session_state.tasks_data.append(
                {"task": "New task", "team": "Front Desk", "priority": "Low", "status": "Open"}
            )
            st.rerun()
    
    if len(filtered_tasks) > 0:
        for idx, row in filtered_tasks.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            status_emoji = {"Open": "⏳", "Done": "✅"}
            
            col1.markdown(f"{status_emoji.get(row['status'], '⏳')} **{row['task']}** | {row['team']} | {priority_emoji.get(row['priority'], '🟡')} {row['priority']}")
            
            if row['status'] == 'Open':
                if col2.button("Mark Done", key=f"done_{idx}"):
                    st.session_state.tasks_data[idx]['status'] = "Done"
                    st.rerun()
            
            if col3.button("🗑️ Delete", key=f"delete_task_{idx}"):
                st.session_state.tasks_data.pop(idx)
                st.rerun()
    else:
        st.info("No tasks match the current filter.")

# ---------- ROOMS TAB ----------
with tabs[1]:
    st.markdown("### Room Status")
    
    if len(filtered_rooms) > 0:
        # Display as cards
        for idx, row in filtered_rooms.iterrows():
            status_colors = {
                "Ready": "#28a745",
                "Dirty": "#ffc107",
                "Occupied": "#17a2b8",
                "Maintenance": "#dc3545"
            }
            
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"""
                <div style='
                    background:white;
                    padding:15px;
                    border-radius:8px;
                    margin-bottom:10px;
                    border-left:5px solid {status_colors.get(row['status'], '#6c757d')};
                    box-shadow:0 2px 4px rgba(0,0,0,0.1);
                '>
                    <strong>Room {row['room']}</strong> (Floor {row['floor']})<br>
                    Status: <span style='color:{status_colors.get(row['status'], '#6c757d')};font-weight:bold;'>{row['status']}</span><br>
                    Housekeeper: {row['housekeeper']}
                </div>
            """, unsafe_allow_html=True)
            
            # Room status update
            if col2.button("Update", key=f"update_{idx}"):
                new_status = col2.selectbox("New Status", ["Ready", "Dirty", "Occupied", "Maintenance"], key=f"status_{idx}")
    else:
        st.info("No rooms match the current filter.")

# ---------- MAINTENANCE TAB ----------
with tabs[2]:
    st.markdown("### Maintenance Queue")
    
    if len(maintenance_df) > 0:
        for idx, row in maintenance_df.iterrows():
            priority_colors = {"High": "#dc3545", "Medium": "#ffc107", "Low": "#28a745"}
            
            st.markdown(f"""
                <div style='
                    background:white;
                    padding:15px;
                    border-radius:8px;
                    margin-bottom:10px;
                    border-left:5px solid {priority_colors.get(row['priority'], '#6c757d')};
                    box-shadow:0 2px 4px rgba(0,0,0,0.1);
                '>
                    🔧 <strong>{row['issue']}</strong><br>
                    Room: {row['room']} | Priority: <span style='color:{priority_colors.get(row['priority'], '#6c757d')};font-weight:bold;'>{row['priority']}</span> | Owner: {row['owner']}
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No maintenance issues!")

# ---------- STAFFING TAB ----------
with tabs[3]:
    st.markdown("### Staffing")
    
    staff_df = pd.DataFrame([
        {"staff": "Maria", "role": "Housekeeping", "shift": "Morning"},
        {"staff": "Liam", "role": "Housekeeping", "shift": "Evening"},
        {"staff": "Priya", "role": "Front Desk", "shift": "Morning"},
        {"staff": "Noah", "role": "Maintenance", "shift": "Night"},
        {"staff": "Ava", "role": "Housekeeping", "shift": "Morning"},
        {"staff": "Maya", "role": "Housekeeping", "shift": "Evening"},
    ])
    
    st.dataframe(
        staff_df,
        use_container_width=True,
        column_config={
            "staff": st.column_config.TextColumn("Staff Name", width="medium"),
            "role": st.column_config.TextColumn("Role", width="medium"),
            "shift": st.column_config.TextColumn("Shift", width="medium"),
        },
        hide_index=True
    )
    
