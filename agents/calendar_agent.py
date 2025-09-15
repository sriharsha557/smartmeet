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