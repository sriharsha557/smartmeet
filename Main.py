import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import json

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="SmartMeet AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mock classes for when imports fail
class MockSchedulerAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def generate_suggestions(self, title, participants, duration, priority, preferred_dates):
        return generate_mock_suggestions(preferred_dates, duration)

class MockCalendarAgent:
    def __init__(self):
        pass
    
    def get_availability(self, participants, date_range):
        return {}

class MockNotificationAgent:
    def __init__(self):
        pass
    
    def send_invitations(self, title, participants, suggestion):
        return True

class MockDatabaseService:
    def __init__(self):
        self.meetings = []
    
    def create_meeting(self, meeting_record):
        meeting_record['id'] = len(self.meetings) + 1
        self.meetings.append(meeting_record)
        return meeting_record['id']
    
    def get_meetings(self):
        return self.meetings

# Authentication functions
def authenticate_microsoft():
    """Mock authentication function"""
    st.session_state.microsoft_tokens = {"access_token": "mock_token"}
    return True

def get_auth_button():
    """Display authentication button"""
    if st.button("🔗 Connect to Microsoft 365"):
        authenticate_microsoft()
        st.success("✅ Connected successfully!")
        return True
    return False

def logout():
    """Logout function"""
    if 'microsoft_tokens' in st.session_state:
        del st.session_state.microsoft_tokens
    st.success("👋 Logged out successfully!")

# Utility functions
def parse_duration_string(duration_str):
    """Parse duration string to minutes"""
    duration_map = {
        "30 minutes": 30,
        "45 minutes": 45,
        "1 hour": 60,
        "1.5 hours": 90,
        "2 hours": 120,
        "2.5 hours": 150,
        "3 hours": 180
    }
    return duration_map.get(duration_str, 60)

def generate_mock_suggestions(preferred_dates, duration):
    """Generate mock suggestions when AI is not available"""
    suggestions = []
    
    for i, date in enumerate(preferred_dates[:3]):
        for hour in [9, 10, 14, 15]:
            if isinstance(date, date):
                suggestion_time = datetime.combine(date, datetime.min.time().replace(hour=hour))
            else:
                suggestion_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            duration_minutes = parse_duration_string(duration)
            end_time = suggestion_time + timedelta(minutes=duration_minutes)
            
            suggestions.append({
                "date": suggestion_time.strftime("%Y-%m-%d"),
                "time": suggestion_time.strftime("%I:%M %p"),
                "end_time": end_time.strftime("%I:%M %p"),
                "available_count": 3,
                "total_participants": 3,
                "conflicts": [],
                "confidence": max(95 - (i * 10) - (hour - 9) * 5, 60),
                "reasoning": f"Good time slot for {suggestion_time.strftime('%A')} meetings"
            })
    
    return suggestions[:5]

# Initialize services with error handling
@st.cache_resource
def init_services():
    """Initialize all services with proper error handling"""
    try:
        # Try to import actual modules
        scheduler = None
        calendar = None
        notifier = None
        db = None
        
        # Check if GROQ_API_KEY is available
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            st.warning("⚠️ GROQ_API_KEY not found. Using mock AI features.")
        
        try:
            from agents.scheduler_agent import SchedulerAgent
            scheduler = SchedulerAgent(groq_key) if groq_key else MockSchedulerAgent()
        except ImportError:
            scheduler = MockSchedulerAgent(groq_key)
        
        try:
            from agents.calendar_agent import CalendarAgent
            calendar = CalendarAgent()
        except ImportError:
            calendar = MockCalendarAgent()
        
        try:
            from agents.notification_agent import NotificationAgent
            notifier = NotificationAgent()
        except ImportError:
            notifier = MockNotificationAgent()
        
        try:
            from services.database import DatabaseService
            db = DatabaseService()
        except ImportError:
            db = MockDatabaseService()
        
        return scheduler, calendar, notifier, db
        
    except Exception as e:
        st.info(f"Running in demo mode: {e}")
        return MockSchedulerAgent(), MockCalendarAgent(), MockNotificationAgent(), MockDatabaseService()

def main():
    """Main application function"""
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .feature-card {
        padding: 1rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">🤖 SmartMeet AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Intelligent Meeting Scheduling Assistant</p>', unsafe_allow_html=True)

    # Initialize services
    scheduler, calendar, notifier, db = init_services()

    # Sidebar
    with st.sidebar:
        st.title("🤖 SmartMeet AI")
        st.title("🎯 Navigation")
        
        # Check authentication status
        is_authenticated = 'microsoft_tokens' in st.session_state
        
        if is_authenticated:
            st.success("✅ Connected to Microsoft 365")
            if st.button("🚪 Logout"):
                logout()
                st.rerun()
        else:
            st.warning("🔒 Not connected to Microsoft 365")
            if get_auth_button():
                st.rerun()

        st.markdown("---")
        
        # Navigation menu
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Dashboard", "📅 Schedule Meeting", "📊 Analytics", "⚙️ Settings"]
        )
        
        st.markdown("---")
        st.markdown("### 🚀 Quick Actions")
        if st.button("📝 New Meeting", use_container_width=True):
            st.session_state.page = "📅 Schedule Meeting"
        if st.button("📈 View Analytics", use_container_width=True):
            st.session_state.page = "📊 Analytics"

    # Main content based on selected page
    if page == "🏠 Dashboard":
        show_dashboard(db)
    elif page == "📅 Schedule Meeting":
        show_schedule_meeting(scheduler, calendar, notifier, db)
    elif page == "📊 Analytics":
        show_analytics(db)
    elif page == "⚙️ Settings":
        show_settings()

def show_dashboard(db):
    """Show dashboard with meeting overview"""
    st.header("📊 Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📅 Today's Meetings</h3>
            <h2>3</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>⏰ This Week</h3>
            <h2>12</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>✅ Scheduled</h3>
            <h2>8</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>⏳ Pending</h3>
            <h2>4</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Recent meetings
    st.subheader("📋 Recent Activity")
    
    # Sample data
    sample_meetings = pd.DataFrame({
        'Meeting': ['Team Standup', 'Client Review', 'Project Planning', 'Training Session'],
        'Date': ['2024-01-15', '2024-01-15', '2024-01-16', '2024-01-17'],
        'Time': ['09:00 AM', '02:00 PM', '10:00 AM', '03:00 PM'],
        'Status': ['Completed', 'Scheduled', 'Scheduled', 'Pending'],
        'Participants': [5, 3, 8, 12]
    })
    
    st.dataframe(sample_meetings, use_container_width=True)

def show_schedule_meeting(scheduler, calendar, notifier, db):
    """Show meeting scheduling interface"""
    st.header("📅 Schedule New Meeting")
    
    # Meeting details form
    with st.form("meeting_form"):
        st.subheader("Meeting Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Meeting Title*", placeholder="e.g., Team Standup")
            duration = st.selectbox("Duration", [
                "30 minutes", "45 minutes", "1 hour", 
                "1.5 hours", "2 hours", "2.5 hours", "3 hours"
            ], index=2)
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"], index=1)
        
        with col2:
            participants_input = st.text_area(
                "Participants (one email per line)*",
                placeholder="john@company.com\nmary@company.com",
                help="Enter email addresses of participants, one per line"
            )
            
            preferred_dates = st.date_input(
                "Preferred Dates",
                value=[datetime.now().date() + timedelta(days=1)],
                min_value=datetime.now().date(),
                help="Select one or more preferred dates"
            )
        
        description = st.text_area("Description (optional)", placeholder="Meeting agenda and details...")
        
        submitted = st.form_submit_button("🤖 Get AI Suggestions", type="primary")
        
        if submitted:
            if not title or not participants_input:
                st.error("Please fill in all required fields (marked with *)")
            else:
                participants = [email.strip() for email in participants_input.split('\n') if email.strip()]
                
                if isinstance(preferred_dates, date):
                    preferred_dates = [preferred_dates]
                preferred_datetimes = [datetime.combine(d, datetime.min.time()) for d in preferred_dates]
                
                with st.spinner("🤖 AI is analyzing schedules and generating suggestions..."):
                    try:
                        suggestions = scheduler.generate_suggestions(
                            title, participants, duration, priority, preferred_datetimes
                        )
                        
                        st.session_state.meeting_suggestions = {
                            'title': title,
                            'participants': participants,
                            'duration': duration,
                            'priority': priority,
                            'description': description,
                            'suggestions': suggestions
                        }
                        
                        st.success("✅ AI suggestions generated!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating suggestions: {e}")

    # Show suggestions if available
    if 'meeting_suggestions' in st.session_state:
        show_meeting_suggestions(notifier, db)

def show_meeting_suggestions(notifier, db):
    """Display AI-generated meeting suggestions"""
    suggestions_data = st.session_state.meeting_suggestions
    suggestions = suggestions_data['suggestions']
    
    st.markdown("---")
    st.subheader("🤖 AI Recommendations")
    
    for i, suggestion in enumerate(suggestions):
        with st.expander(f"Option {i+1}: {suggestion['date']} at {suggestion['time']}", expanded=i==0):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**📅 Date:** {suggestion['date']}")
                st.write(f"**🕐 Time:** {suggestion['time']} - {suggestion['end_time']}")
                st.write(f"**👥 Availability:** {suggestion['available_count']}/{suggestion['total_participants']} participants")
                st.write(f"**🎯 Confidence:** {suggestion['confidence']}%")
                st.write(f"**💭 Reasoning:** {suggestion['reasoning']}")
                
                if suggestion['conflicts']:
                    st.warning(f"⚠️ Conflicts with: {', '.join(suggestion['conflicts'])}")
            
            with col2:
                # Confidence meter
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = suggestion['confidence'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Confidence"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkgreen" if suggestion['confidence'] > 80 else "orange" if suggestion['confidence'] > 60 else "red"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"}],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90}}))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                if st.button(f"📅 Schedule This", key=f"schedule_{i}"):
                    schedule_meeting(suggestion, suggestions_data, notifier, db)

def schedule_meeting(suggestion, meeting_data, notifier, db):
    """Schedule the selected meeting"""
    try:
        meeting_record = {
            'title': meeting_data['title'],
            'description': meeting_data['description'],
            'participants': meeting_data['participants'],
            'duration_minutes': parse_duration_string(meeting_data['duration']),
            'priority': meeting_data['priority'],
            'scheduled_start': f"{suggestion['date']} {suggestion['time']}",
            'scheduled_end': f"{suggestion['date']} {suggestion['end_time']}"
        }
        meeting_id = db.create_meeting(meeting_record)
        
        notifier.send_invitations(
            meeting_data['title'],
            meeting_data['participants'],
            suggestion
        )
        
        st.success("🎉 Meeting scheduled successfully!")
        st.balloons()
        
        if 'meeting_suggestions' in st.session_state:
            del st.session_state.meeting_suggestions
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error scheduling meeting: {e}")

def show_analytics(db):
    """Show analytics dashboard"""
    st.header("📊 Meeting Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Meeting frequency chart
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        meetings_per_day = pd.DataFrame({
            'Date': dates,
            'Meetings': [abs(hash(str(d))) % 5 for d in dates]
        })
        
        fig = px.line(meetings_per_day, x='Date', y='Meetings', 
                      title='📅 Meetings Over Time')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Meeting duration distribution
        durations = ['30 min', '1 hour', '1.5 hours', '2 hours']
        counts = [25, 45, 20, 10]
        
        fig = px.pie(values=counts, names=durations, 
                     title='⏰ Meeting Duration Distribution')
        st.plotly_chart(fig, use_container_width=True)

def show_settings():
    """Show settings page"""
    st.header("⚙️ Settings")
    
    st.subheader("🔑 API Configuration")
    
    with st.expander("Groq AI Configuration"):
        current_key = os.getenv("GROQ_API_KEY", "")
        groq_key = st.text_input("GROQ_API_KEY", type="password", 
                                 value="*" * len(current_key) if current_key else "")
        
        if st.button("Test Groq Connection"):
            if groq_key and not groq_key.startswith("*"):
                try:
                    # Mock test - replace with actual Groq test
                    st.success("✅ Groq connection successful! (Mock test)")
                except Exception as e:
                    st.error(f"❌ Groq connection failed: {e}")
            else:
                st.warning("Please enter your Groq API key")
    
    st.subheader("🔧 Notification Settings")
    
    with st.expander("Email Configuration"):
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587)
        st.info("Email notifications are in demo mode. Configure SMTP settings for production.")
    
    st.subheader("🗃️ Data Management")
    
    if st.button("🗑️ Clear All Data"):
        if st.checkbox("I understand this will delete all meeting data"):
            st.warning("This feature is disabled in demo mode.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("The application is running in demo mode with mock data.")
        st.code(f"Error details: {str(e)}")
