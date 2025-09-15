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