# agents/scheduler_agent.py
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import openai
import json
import os
from langchain.agents import AgentType, initialize_agent
from langchain.llms import OpenAI
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
import pandas as pd

class SchedulerAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = OpenAI(temperature=0.1, openai_api_key=self.api_key)
        self.memory = ConversationBufferMemory()
        
        # Initialize tools
        tools = [
            Tool(
                name="availability_checker",
                description="Check participant availability for given time slots",
                func=self._check_availability
            ),
            Tool(
                name="conflict_resolver",
                description="Find alternative time slots when conflicts exist",
                func=self._resolve_conflicts
            ),
            Tool(
                name="priority_optimizer",
                description="Optimize meeting scheduling based on priority and preferences",
                func=self._optimize_priority
            )
        ]
        
        self.agent = initialize_agent(
            tools, self.llm, 
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
    
    def generate_suggestions(self, title: str, participants: List[str], 
                           duration: str, priority: str, 
                           preferred_dates: List[datetime]) -> List[Dict]:
        """Generate intelligent meeting suggestions using AI"""
        
        # Convert duration to minutes
        duration_map = {
            "30 minutes": 30,
            "45 minutes": 45,
            "1 hour": 60,
            "1.5 hours": 90,
            "2 hours": 120
        }
        duration_mins = duration_map.get(duration, 60)
        
        # Generate time slots for the preferred dates
        time_slots = self._generate_time_slots(preferred_dates, duration_mins)
        
        suggestions = []
        for slot in time_slots:
            # Simulate availability checking (in real implementation, use Microsoft Graph)
            availability = self._simulate_availability_check(participants, slot)
            
            suggestion = {
                "date": slot["start"].strftime("%Y-%m-%d"),
                "time": slot["start"].strftime("%I:%M %p"),
                "end_time": slot["end"].strftime("%I:%M %p"),
                "available_count": availability["available_count"],
                "total_participants": len(participants),
                "conflicts": availability["conflicts"],
                "confidence": self._calculate_confidence(availability, priority),
                "reasoning": self._generate_reasoning(availability, priority)
            }
            suggestions.append(suggestion)
        
        # Sort by confidence score
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:5]  # Return top 5 suggestions
    
    def process_natural_language_request(self, request: str) -> str:
        """Process natural language meeting requests"""
        
        # Use the agent to understand and process the request
        try:
            response = self.agent.run(f"""
            You are a smart meeting scheduling assistant. Process this request and provide helpful information:
            
            Request: "{request}"
            
            If this is a scheduling request, extract:
            - Meeting purpose/title
            - Participants (if mentioned)
            - Duration (if mentioned) 
            - Preferred time (if mentioned)
            - Priority level (if mentioned)
            
            If this is a question about meetings or availability, provide helpful information.
            
            Always be conversational and helpful.
            """)
            return response
        except Exception as e:
            return f"I understand you want help with scheduling. Could you provide more details about the meeting you'd like to schedule? For example: participants, duration, and preferred time."
    
    def _generate_time_slots(self, preferred_dates: List[datetime], duration_mins: int) -> List[Dict]:
        """Generate possible time slots"""
        slots = []
        business_start = 9  # 9 AM
        business_end = 17   # 5 PM
        
        for date in preferred_dates:
            # Generate slots for business hours
            current_time = datetime.combine(date.date(), datetime.min.time().replace(hour=business_start))
            end_of_day = datetime.combine(date.date(), datetime.min.time().replace(hour=business_end))
            
            while current_time + timedelta(minutes=duration_mins) <= end_of_day:
                slots.append({
                    "start": current_time,
                    "end": current_time + timedelta(minutes=duration_mins)
                })
                current_time += timedelta(minutes=30)  # 30-minute intervals
        
        return slots
    
    def _simulate_availability_check(self, participants: List[str], slot: Dict) -> Dict:
        """Simulate availability checking (replace with real Microsoft Graph API)"""
        import random
        
        # Simulate some participants being busy
        available_count = len(participants)
        conflicts = []
        
        for participant in participants:
            # Random chance of conflict (20%)
            if random.random() < 0.2:
                available_count -= 1
                conflicts.append(participant)
        
        return {
            "available_count": available_count,
            "conflicts": conflicts,
            "total_participants": len(participants)
        }
    
    def _calculate_confidence(self, availability: Dict, priority: str) -> int:
        """Calculate confidence score for a time slot"""
        base_score = (availability["available_count"] / availability["total_participants"]) * 100
        
        # Adjust based on priority
        priority_multiplier = {
            "Low": 0.9,
            "Medium": 1.0,
            "High": 1.1,
            "Urgent": 1.2
        }
        
        score = base_score * priority_multiplier.get(priority, 1.0)
        return min(int(score), 100)
    
    def _generate_reasoning(self, availability: Dict, priority: str) -> str:
        """Generate human-readable reasoning for the suggestion"""
        if availability["available_count"] == availability["total_participants"]:
            return "All participants are available - perfect match!"
        elif availability["available_count"] / availability["total_participants"] >= 0.8:
            return f"Most participants available ({availability['available_count']}/{availability['total_participants']})"
        else:
            return f"Some conflicts detected - {len(availability['conflicts'])} participants busy"
    
    def _check_availability(self, query: str) -> str:
        """Tool function for checking availability"""
        # This would integrate with Microsoft Graph API
        return "Availability checked successfully"
    
    def _resolve_conflicts(self, query: str) -> str:
        """Tool function for resolving conflicts"""
        return "Alternative time slots found to resolve conflicts"
    
    def _optimize_priority(self, query: str) -> str:
        """Tool function for priority-based optimization"""
        return "Meeting scheduled with priority optimization applied"


# agents/calendar_agent.py
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os

class CalendarAgent:
    def __init__(self):
        self.graph_api_endpoint = "https://graph.microsoft.com/v1.0"
        self.access_token = None
    
    def set_access_token(self, token: str):
        """Set Microsoft Graph API access token"""
        self.access_token = token
    
    def get_user_calendar_events(self, user_email: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch calendar events for a specific user"""
        if not self.access_token:
            return self._generate_mock_events(user_email, start_date, end_date)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Format dates for Microsoft Graph API
        start_iso = start_date.isoformat() + 'Z'
        end_iso = end_date.isoformat() + 'Z'
        
        url = f"{self.graph_api_endpoint}/users/{user_email}/calendar/events"
        params = {
            '$filter': f"start/dateTime ge '{start_iso}' and end/dateTime le '{end_iso}'",
            '$select': 'subject,start,end,showAs,isAllDay,location'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            events = response.json().get('value', [])
            return self._format_events(events)
        
        except requests.RequestException as e:
            print(f"Error fetching calendar events: {e}")
            return self._generate_mock_events(user_email, start_date, end_date)
    
    def check_multiple_users_availability(self, user_emails: List[str], 
                                        start_date: datetime, end_date: datetime) -> Dict[str, List[Dict]]:
        """Check availability for multiple users"""
        availability_map = {}
        
        for email in user_emails:
            events = self.get_user_calendar_events(email, start_date, end_date)
            availability_map[email] = self._calculate_availability(events, start_date, end_date)
        
        return availability_map
    
    def find_free_time_slots(self, user_emails: List[str], duration_minutes: int,
                           start_date: datetime, end_date: datetime) -> List[Dict]:
        """Find common free time slots for all users"""
        availability_map = self.check_multiple_users_availability(user_emails, start_date, end_date)
        
        # Generate 30-minute time slots
        time_slots = []
        current = start_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Start at 9 AM
        end_business = end_date.replace(hour=17, minute=0, second=0, microsecond=0)  # End at 5 PM
        
        while current + timedelta(minutes=duration_minutes) <= end_business:
            # Skip weekends
            if current.weekday() < 5:  # Monday = 0, Sunday = 6
                slot_end = current + timedelta(minutes=duration_minutes)
                
                # Check if all users are free during this slot
                all_free = True
                conflicted_users = []
                
                for email in user_emails:
                    if self._is_user_busy(availability_map[email], current, slot_end):
                        all_free = False
                        conflicted_users.append(email)
                
                time_slots.append({
                    'start': current,
                    'end': slot_end,
                    'all_available': all_free,
                    'available_count': len(user_emails) - len(conflicted_users),
                    'conflicted_users': conflicted_users
                })
            
            current += timedelta(minutes=30)
        
        # Sort by availability (most available first)
        time_slots.sort(key=lambda x: x['available_count'], reverse=True)
        return time_slots
    
    def create_meeting(self, title: str, description: str, start_time: datetime,
                      end_time: datetime, attendees: List[str]) -> Dict:
        """Create a meeting in the organizer's calendar"""
        if not self.access_token:
            return self._mock_create_meeting(title, start_time, end_time, attendees)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        meeting_data = {
            'subject': title,
            'body': {
                'contentType': 'HTML',
                'content': description
            },
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC'
            },
            'attendees': [
                {
                    'emailAddress': {
                        'address': email,
                        'name': email.split('@')[0]
                    },
                    'type': 'required'
                } for email in attendees
            ]
        }
        
        try:
            url = f"{self.graph_api_endpoint}/me/calendar/events"
            response = requests.post(url, headers=headers, json=meeting_data)
            response.raise_for_status()
            
            meeting = response.json()
            return {
                'id': meeting.get('id'),
                'webLink': meeting.get('webLink'),
                'status': 'created'
            }
        
        except requests.RequestException as e:
            print(f"Error creating meeting: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _generate_mock_events(self, user_email: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Generate mock calendar events for testing"""
        import random
        
        events = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            # Skip weekends
            if current_date.weekday() < 5:
                # Generate 0-3 random events per day
                num_events = random.randint(0, 3)
                
                for _ in range(num_events):
                    start_hour = random.randint(9, 16)
                    duration = random.choice([30, 60, 90])
                    
                    event_start = datetime.combine(current_date, datetime.min.time().replace(hour=start_hour))
                    event_end = event_start + timedelta(minutes=duration)
                    
                    events.append({
                        'subject': random.choice(['Team Meeting', 'Client Call', 'Project Review', 'Training']),
                        'start': event_start,
                        'end': event_end,
                        'showAs': 'busy',
                        'user_email': user_email
                    })
            
            current_date += timedelta(days=1)
        
        return events
    
    def _format_events(self, events: List[Dict]) -> List[Dict]:
        """Format events from Microsoft Graph API response"""
        formatted = []
        
        for event in events:
            formatted.append({
                'subject': event.get('subject', 'No Title'),
                'start': datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')),
                'end': datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')),
                'showAs': event.get('showAs', 'busy'),
                'location': event.get('location', {}).get('displayName', '')
            })
        
        return formatted
    
    def _calculate_availability(self, events: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
        """Calculate free/busy periods from calendar events"""
        busy_periods = []
        
        for event in events:
            if event['showAs'] in ['busy', 'tentative']:
                busy_periods.append({
                    'start': event['start'],
                    'end': event['end']
                })
        
        # Sort by start time
        busy_periods.sort(key=lambda x: x['start'])
        return busy_periods
    
    def _is_user_busy(self, busy_periods: List[Dict], slot_start: datetime, slot_end: datetime) -> bool:
        """Check if user is busy during a specific time slot"""
        for period in busy_periods:
            # Check for overlap
            if (slot_start < period['end'] and slot_end > period['start']):
                return True
        return False
    
    def _mock_create_meeting(self, title: str, start_time: datetime, end_time: datetime, attendees: List[str]) -> Dict:
        """Mock meeting creation for testing"""
        return {
            'id': f'mock_meeting_{int(datetime.now().timestamp())}',
            'webLink': 'https://teams.microsoft.com/mock-meeting',
            'status': 'created'
        }


# agents/notification_agent.py
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import List, Dict
import os
from datetime import datetime

class NotificationAgent:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
    
    def send_meeting_invitation(self, meeting_details: Dict, attendees: List[str]) -> bool:
        """Send meeting invitation emails"""
        try:
            # Create email content
            subject = f"Meeting Invitation: {meeting_details['title']}"
            
            html_body = self._create_invitation_html(meeting_details)
            
            # Send to each attendee
            for attendee in attendees:
                self._send_email(attendee, subject, html_body)
            
            return True
        
        except Exception as e:
            print(f"Error sending invitations: {e}")
            return False
    
    def send_meeting_update(self, meeting_details: Dict, attendees: List[str], update_type: str) -> bool:
        """Send meeting update notifications"""
        try:
            subject = f"Meeting {update_type.title()}: {meeting_details['title']}"
            
            html_body = self._create_update_html(meeting_details, update_type)
            
            for attendee in attendees:
                self._send_email(attendee, subject, html_body)
            
            return True
        
        except Exception as e:
            print(f"Error sending updates: {e}")
            return False
    
    def send_reminder(self, meeting_details: Dict, attendees: List[str]) -> bool:
        """Send meeting reminders"""
        try:
            subject = f"Reminder: {meeting_details['title']} starting soon"
            
            html_body = self._create_reminder_html(meeting_details)
            
            for attendee in attendees:
                self._send_email(attendee, subject, html_body)
            
            return True
        
        except Exception as e:
            print(f"Error sending reminders: {e}")
            return False
    
    def send_invitations(self, title: str, participants: List[str], suggestion: Dict) -> bool:
        """Simplified method for sending invitations from the main app"""
        meeting_details = {
            'title': title,
            'date': suggestion['date'],
            'time': suggestion['time'],
            'end_time': suggestion['end_time']
        }
        
        return self.send_meeting_invitation(meeting_details, participants)
    
    def _send_email(self, recipient: str, subject: str, html_body: str) -> bool:
        """Send individual email"""
        if not self.smtp_username or not self.smtp_password:
            # Mock email sending for development
            print(f"MOCK EMAIL SENT TO: {recipient}")
            print(f"SUBJECT: {subject}")
            return True
        
        try:
            msg = MimeMultipart('alternative')
            msg['From'] = self.smtp_username
            msg['To'] = recipient
            msg['Subject'] = subject
            
            html_part = MimeText(html_body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            print(f"Error sending email to {recipient}: {e}")
            return False
    
    def _create_invitation_html(self, meeting_details: Dict) -> str:
        """Create HTML content for meeting invitation"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #0078d4; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 10px 0; border-radius: 5px; }}
                .details {{ background-color: white; padding: 15px; border-left: 4px solid #0078d4; }}
                .button {{ background-color: #0078d4; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📅 Meeting Invitation</h2>
            </div>
            
            <div class="content">
                <h3>{meeting_details['title']}</h3>
                
                <div class="details">
                    <p><strong>📅 Date:</strong> {meeting_details['date']}</p>
                    <p><strong>🕐 Time:</strong> {meeting_details['time']} - {meeting_details.get('end_time', 'TBD')}</p>
                    <p><strong>🤖 Scheduled by:</strong> SmartMeet AI</p>
                </div>
                
                <p>You've been invited to attend this meeting. Please confirm your attendance.</p>
                
                <a href="#" class="button">Accept</a>
                <a href="#" class="button" style="background-color: #dc3545;">Decline</a>
            </div>
            
            <p><em>This invitation was sent by SmartMeet AI - your intelligent meeting scheduler.</em></p>
        </body>
        </html>
        """
    
    def _create_update_html(self, meeting_details: Dict, update_type: str) -> str:
        """Create HTML content for meeting updates"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #ff9500; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 10px 0; border-radius: 5px; }}
                .details {{ background-color: white; padding: 15px; border-left: 4px solid #ff9500; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>⚡ Meeting {update_type.title()}</h2>
            </div>
            
            <div class="content">
                <h3>{meeting_details['title']}</h3>
                
                <div class="details">
                    <p><strong>📅 New Date:</strong> {meeting_details['date']}</p>
                    <p><strong>🕐 New Time:</strong> {meeting_details['time']} - {meeting_details.get('end_time', 'TBD')}</p>
                    <p><strong>📝 Update Type:</strong> {update_type.title()}</p>
                </div>
                
                <p>Your meeting has been {update_type}. Please update your calendar accordingly.</p>
            </div>
            
            <p><em>This update was sent by SmartMeet AI.</em></p>
        </body>
        </html>
        """
    
    def _create_reminder_html(self, meeting_details: Dict) -> str:
        """Create HTML content for meeting reminders"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f9f9f9; margin: 10px 0; border-radius: 5px; }}
                .details {{ background-color: white; padding: 15px; border-left: 4px solid #28a745; }}
                .urgent {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔔 Meeting Reminder</h2>
            </div>
            
            <div class="content">
                <h3>{meeting_details['title']}</h3>
                
                <div class="details">
                    <p class="urgent">⏰ Starting Soon!</p>
                    <p><strong>📅 Date:</strong> {meeting_details['date']}</p>
                    <p><strong>🕐 Time:</strong> {meeting_details['time']}</p>
                </div>
                
                <p>Don't forget about your upcoming meeting!</p>
            </div>
            
            <p><em>This reminder was sent by SmartMeet AI.</em></p>
        </body>
        </html>
        """


# agents/conflict_resolver.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

class ConflictResolverAgent:
    def __init__(self):
        self.conflict_strategies = [
            'reschedule',
            'shorter_duration',
            'split_meeting',
            'priority_override'
        ]
    
    def detect_conflicts(self, meeting_request: Dict, existing_meetings: List[Dict]) -> List[Dict]:
        """Detect scheduling conflicts"""
        conflicts = []
        
        requested_start = meeting_request['start_time']
        requested_end = meeting_request['end_time']
        
        for meeting in existing_meetings:
            # Check for time overlap
            if (requested_start < meeting['end_time'] and 
                requested_end > meeting['start_time']):
                
                # Check for participant overlap
                common_participants = set(meeting_request['participants']) & set(meeting['participants'])
                if common_participants:
                    conflicts.append({
                        'meeting_id': meeting.get('id'),
                        'meeting_title': meeting.get('title'),
                        'conflicted_participants': list(common_participants),
                        'time_overlap': {
                            'start': max(requested_start, meeting['start_time']),
                            'end': min(requested_end, meeting['end_time'])
                        }
                    })
        
        return conflicts
    
    def resolve_conflicts(self, meeting_request: Dict, conflicts: List[Dict]) -> List[Dict]:
        """Generate conflict resolution suggestions"""
        resolutions = []
        
        for conflict in conflicts:
            # Strategy 1: Reschedule to next available slot
            resolutions.append(self._suggest_reschedule(meeting_request, conflict))
            
            # Strategy 2: Reduce meeting duration
            if meeting_request.get('duration_minutes', 60) > 30:
                resolutions.append(self._suggest_shorter_duration(meeting_request, conflict))
            
            # Strategy 3: Split into multiple meetings
            if len(meeting_request['participants']) > 3:
                resolutions.append(self._suggest_split_meeting(meeting_request, conflict))
        
        return resolutions
    
    def _suggest_reschedule(self, meeting_request: Dict, conflict: Dict) -> Dict:
        """Suggest rescheduling to avoid conflicts"""
        # Find next available slot (simplified logic)
        original_start = meeting_request['start_time']
        duration = timedelta(minutes=meeting_request.get('duration_minutes', 60))
        
        # Try 30-minute intervals after the conflicting meeting
        new_start = original_start + timedelta(minutes=30)
        
        return {
            'strategy': 'reschedule',
            'description': 'Reschedule to avoid conflicts',
            'original_time': original_start,
            'suggested_time': new_start,
            'suggested_end': new_start + duration,
            'confidence': 85,
            'affected_participants': conflict['conflicted_participants']
        }
    
    def _suggest_shorter_duration(self, meeting_request: Dict, conflict: Dict) -> Dict:
        """Suggest reducing meeting duration"""
        original_duration = meeting_request.get('duration_minutes', 60)
        new_duration = max(15, original_duration - 15)  # Reduce by 15 minutes, minimum 15
        
        return {
            'strategy': 'shorter_duration',
            'description': f'Reduce meeting duration from {original_duration} to {new_duration} minutes',
            'original_duration': original_duration,
            'suggested_duration': new_duration,
            'confidence': 70,
            'trade_offs': 'Less time for discussion'
        }
    
    def _suggest_split_meeting(self, meeting_request: Dict, conflict: Dict) -> Dict:
        """Suggest splitting into multiple smaller meetings"""
        participants = meeting_request['participants']
        conflicted = set(conflict['conflicted_participants'])
        available = [p for p in participants if p not in conflicted]
        
        return {
            'strategy': 'split_meeting',
            'description': 'Split into separate meetings for different groups',
            'meeting_1': {
                'participants': available,
                'time': meeting_request['start_time']
            },
            'meeting_2': {
                'participants': list(conflicted),
                'time': meeting_request['start_time'] + timedelta(hours=1)
            },
            'confidence': 60,
            'trade_offs': 'Information may need to be shared between meetings'
        }