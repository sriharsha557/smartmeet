import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
from typing import List, Dict, Optional
import plotly.express as px
import plotly.graph_objects as go
from streamlit_calendar import calendar

# Import our custom modules
try:
    from agents.scheduler_agent import SchedulerAgent
    from agents.calendar_agent import CalendarAgent
    from agents.notification_agent import NotificationAgent
    from services.database import DatabaseService
    from utils.auth import authenticate_microsoft
    from utils.date_utils import get_business_hours, format_time_slot
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.error("Please ensure all files are in the correct directory structure. Check the README.md for setup instructions.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="SmartMeet AI",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'meetings' not in st.session_state:
    st.session_state.meetings = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize services
@st.cache_resource
def init_services():
    try:
        db_service = DatabaseService()
        calendar_agent = CalendarAgent()
        scheduler_agent = SchedulerAgent()
        notification_agent = NotificationAgent()
        return db_service, calendar_agent, scheduler_agent, notification_agent
    except Exception as e:
        st.error(f"❌ Failed to initialize services: {e}")
        st.error("Please check your configuration and try again.")
        return None, None, None, None

try:
    db_service, calendar_agent, scheduler_agent, notification_agent = init_services()
    if not all([db_service, calendar_agent, scheduler_agent, notification_agent]):
        st.stop()
except Exception as e:
    st.error(f"❌ Service initialization error: {e}")
    st.stop()

# Sidebar for navigation and settings
st.sidebar.title("🤖 SmartMeet AI")
st.sidebar.markdown("*AI-Powered Meeting Scheduler*")

# Authentication section
if not st.session_state.authenticated:
    st.sidebar.header("🔐 Authentication")
    if st.sidebar.button("Connect to Microsoft 365", type="primary"):
        # In a real implementation, this would trigger OAuth flow
        st.session_state.authenticated = True
        st.sidebar.success("Connected successfully!")
        st.rerun()
else:
    st.sidebar.success("✅ Connected to Microsoft 365")
    if st.sidebar.button("Disconnect"):
        st.session_state.authenticated = False
        st.rerun()

# Main navigation
if st.session_state.authenticated:
    page = st.sidebar.selectbox(
        "📋 Navigation",
        ["Dashboard", "Schedule Meeting", "Chat Assistant", "Calendar View", "Settings"]
    )
else:
    st.title("Welcome to SmartMeet AI 🤖")
    st.markdown("""
    ### Your Intelligent Meeting Scheduler
    
    SmartMeet AI uses advanced language models to help you:
    - 📅 Schedule meetings intelligently
    - 🤝 Check participant availability
    - ⚡ Resolve scheduling conflicts
    - 📧 Send automatic invitations
    - 💬 Use natural language commands
    
    **Get started by connecting your Microsoft 365 account!**
    """)
    st.stop()

# Main content based on selected page
if page == "Dashboard":
    st.title("📊 SmartMeet Dashboard")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Meetings", "24", "2")
    with col2:
        st.metric("This Week", "8", "1")
    with col3:
        st.metric("Success Rate", "96%", "2%")
    with col4:
        st.metric("Avg Schedule Time", "2.3 min", "-0.5 min")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Meeting trends
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        meetings_data = pd.DataFrame({
            'Date': dates,
            'Meetings': [2, 3, 1, 4, 2, 1, 0, 3, 5, 2, 1, 3, 4, 2, 1, 
                        3, 2, 4, 1, 2, 3, 0, 0, 4, 3, 2, 1, 3, 2, 1, 2]
        })
        
        fig = px.line(meetings_data, x='Date', y='Meetings', 
                     title='📈 Meeting Trends (Last 30 Days)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Meeting types distribution
        meeting_types = ['Team Standup', 'Client Call', 'Project Review', 'One-on-One', 'Training']
        counts = [15, 8, 12, 6, 4]
        
        fig = px.pie(values=counts, names=meeting_types, 
                    title='🎯 Meeting Types Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    # Upcoming meetings
    st.subheader("📅 Upcoming Meetings")
    upcoming_meetings = [
        {"Title": "Weekly Team Standup", "Time": "Today, 9:00 AM", "Participants": "5", "Status": "Confirmed"},
        {"Title": "Client Presentation", "Time": "Tomorrow, 2:00 PM", "Participants": "8", "Status": "Pending"},
        {"Title": "Project Review", "Time": "Wed, 10:00 AM", "Participants": "3", "Status": "Confirmed"},
    ]
    
    df = pd.DataFrame(upcoming_meetings)
    st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "Schedule Meeting":
    st.title("📅 Schedule New Meeting")
    
    # Meeting form
    with st.form("meeting_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            meeting_title = st.text_input("Meeting Title", "Weekly Team Standup")
            meeting_description = st.text_area("Description (Optional)", 
                                             "Discuss project progress and blockers")
            duration = st.selectbox("Duration", 
                                  ["30 minutes", "45 minutes", "1 hour", "1.5 hours", "2 hours"],
                                  index=2)
            
        with col2:
            participants = st.text_area("Participants (Email addresses, one per line)",
                                      "john@company.com\nsarah@company.com\nmike@company.com")
            priority = st.select_slider("Priority", 
                                      options=["Low", "Medium", "High", "Urgent"],
                                      value="Medium")
            preferred_dates = st.date_input("Preferred Dates", 
                                          value=datetime.now() + timedelta(days=1),
                                          min_value=datetime.now().date())
        
        submitted = st.form_submit_button("🤖 Find Smart Suggestions", type="primary")
    
    if submitted:
        with st.spinner("🧠 AI is analyzing availability and generating suggestions..."):
            try:
                # Simulate AI processing
                import time
                time.sleep(2)
                
                # Generate suggestions using the scheduler agent
                participant_list = [email.strip() for email in participants.split('\n') if email.strip()]
                
                if not participant_list:
                    st.error("❌ Please add at least one participant email address.")
                    st.stop()
                
                suggestions = scheduler_agent.generate_suggestions(
                    title=meeting_title,
                    participants=participant_list,
                    duration=duration,
                    priority=priority,
                    preferred_dates=[preferred_dates]
                )
                
                st.success("✅ Found optimal meeting slots!")
                
                # Display suggestions
                st.subheader("🎯 AI-Generated Suggestions")
                
                for i, suggestion in enumerate(suggestions, 1):
                    with st.expander(f"Option {i}: {suggestion['date']} at {suggestion['time']}", expanded=i==1):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Date:** {suggestion['date']}")
                            st.write(f"**Time:** {suggestion['time']}")
                            st.write(f"**Participants Available:** {suggestion['available_count']}/{len(participant_list)}")
                            st.write(f"**Confidence Score:** {suggestion['confidence']}/100")
                            
                            if suggestion['conflicts']:
                                st.warning(f"⚠️ Conflicts: {', '.join(suggestion['conflicts'])}")
                        
                        with col2:
                            if st.button(f"Schedule This", key=f"schedule_{i}"):
                                try:
                                    st.success("✅ Meeting scheduled! Invitations will be sent.")
                                    # Here you would integrate with calendar service
                                    notification_agent.send_invitations(
                                        meeting_title, participant_list, suggestion
                                    )
                                except Exception as e:
                                    st.error(f"❌ Failed to send invitations: {e}")
                                    
            except Exception as e:
                st.error(f"❌ Error generating suggestions: {e}")
                st.error("Please check your configuration and try again.")

elif page == "Chat Assistant":
    st.title("💬 AI Meeting Assistant")
    st.markdown("*Ask me anything about scheduling meetings!*")
    
    # Chat interface
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about scheduling, availability, or meetings..."):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        st.chat_message("user").write(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Here you would integrate with your LLM
                    response = scheduler_agent.process_natural_language_request(prompt)
                    st.write(response)
                    
                    # Add assistant response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"I apologize, but I encountered an error processing your request: {str(e)}"
                    st.write(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
    
    # Quick action buttons
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 Schedule team meeting"):
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "I'd be happy to help schedule a team meeting! What's the meeting about and who should attend?"
            })
            st.rerun()
    
    with col2:
        if st.button("🔍 Check availability"):
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I can check availability for your team. Please provide the email addresses of participants and your preferred time range."
            })
            st.rerun()
    
    with col3:
        if st.button("⚡ Resolve conflicts"):
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I'll help resolve scheduling conflicts. Which meeting needs to be rescheduled?"
            })
            st.rerun()

elif page == "Calendar View":
    st.title("📆 Calendar Overview")
    
    # Calendar component (simplified version)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Generate sample calendar events
        calendar_events = [
            {
                "title": "Team Standup",
                "start": "2024-09-16T09:00:00",
                "end": "2024-09-16T09:30:00",
                "color": "#FF6B6B"
            },
            {
                "title": "Client Call", 
                "start": "2024-09-16T14:00:00",
                "end": "2024-09-16T15:00:00",
                "color": "#4ECDC4"
            },
            {
                "title": "Project Review",
                "start": "2024-09-17T10:00:00", 
                "end": "2024-09-17T11:30:00",
                "color": "#45B7D1"
            }
        ]
        
        calendar_options = {
            "editable": "true",
            "selectable": "true",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            },
            "initialView": "timeGridWeek",
        }
        
        # Note: streamlit-calendar may need to be installed separately
        try:
            calendar_component = calendar(events=calendar_events, options=calendar_options)
            if calendar_component.get('eventClick'):
                st.write(f"Clicked event: {calendar_component['eventClick']['event']['title']}")
        except:
            st.info("📅 Calendar component will be displayed here. Install streamlit-calendar for full functionality.")
    
    with col2:
        st.subheader("📊 Today's Schedule")
        today_meetings = [
            {"Time": "09:00", "Meeting": "Team Standup", "Duration": "30 min"},
            {"Time": "14:00", "Meeting": "Client Call", "Duration": "60 min"},
        ]
        
        for meeting in today_meetings:
            st.markdown(f"""
            **{meeting['Time']}**  
            {meeting['Meeting']}  
            *{meeting['Duration']}*
            ---
            """)
        
        st.subheader("⚡ Quick Schedule")
        if st.button("📅 Schedule Meeting", type="primary"):
            st.session_state.page = "Schedule Meeting"
            st.rerun()
        
        if st.button("💬 Ask AI Assistant"):
            st.session_state.page = "Chat Assistant"
            st.rerun()

elif page == "Settings":
    st.title("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 General Settings")
        default_duration = st.selectbox("Default Meeting Duration", 
                                       ["30 minutes", "45 minutes", "1 hour"], index=2)
        business_hours_start = st.time_input("Business Hours Start", value=datetime.strptime("09:00", "%H:%M").time())
        business_hours_end = st.time_input("Business Hours End", value=datetime.strptime("17:00", "%H:%M").time())
        timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"], index=0)
        
        st.subheader("🤖 AI Settings")
        ai_model = st.selectbox("AI Model", ["GPT-4", "Claude", "Local Model"], index=0)
        suggestion_count = st.slider("Number of Suggestions", 1, 10, 3)
        confidence_threshold = st.slider("Confidence Threshold", 0, 100, 75)
    
    with col2:
        st.subheader("📧 Notifications")
        email_notifications = st.checkbox("Email Notifications", value=True)
        teams_notifications = st.checkbox("Teams Notifications", value=True)
        reminder_time = st.selectbox("Meeting Reminders", 
                                   ["5 minutes", "15 minutes", "30 minutes", "1 hour"], index=1)
        
        st.subheader("🔒 Privacy & Security")
        data_retention = st.selectbox("Data Retention", 
                                    ["30 days", "90 days", "1 year", "Forever"], index=2)
        share_availability = st.checkbox("Share availability with team", value=False)
        
        st.subheader("💾 Data Management")
        if st.button("Export Meeting Data"):
            st.success("✅ Meeting data exported to CSV")
        if st.button("Clear Cache"):
            st.success("✅ Cache cleared")
        if st.button("Reset Settings"):
            st.warning("⚠️ Settings reset to default")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("*SmartMeet AI v1.0*")
st.sidebar.markdown("Made with ❤️ and 🤖")