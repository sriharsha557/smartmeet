import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class DatabaseService:
    def __init__(self, db_path: str = "./data/meetings.db"):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                microsoft_user_id TEXT UNIQUE,
                access_token TEXT,
                refresh_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Meetings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                organizer_id TEXT,
                duration_minutes INTEGER NOT NULL,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'pending',
                scheduled_start TIMESTAMP,
                scheduled_end TIMESTAMP,
                microsoft_event_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organizer_id) REFERENCES users(id)
            )
        ''')
        
        # Meeting participants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meeting_participants (
                id TEXT PRIMARY KEY,
                meeting_id TEXT,
                email TEXT NOT NULL,
                name TEXT,
                status TEXT DEFAULT 'pending',
                is_required BOOLEAN DEFAULT 1,
                response_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE
            )
        ''')
        
        # Availability cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS availability_cache (
                id TEXT PRIMARY KEY,
                user_email TEXT,
                date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                is_busy BOOLEAN NOT NULL,
                event_subject TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
        # AI suggestions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_suggestions (
                id TEXT PRIMARY KEY,
                meeting_request TEXT,
                suggestions TEXT,
                selected_suggestion TEXT,
                confidence_scores TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_meeting(self, meeting_data: Dict) -> str:
        """Create a new meeting record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        meeting_id = f"meeting_{int(datetime.now().timestamp())}"
        
        cursor.execute('''
            INSERT INTO meetings (id, title, description, organizer_id, duration_minutes, 
                                priority, scheduled_start, scheduled_end)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            meeting_id,
            meeting_data.get('title'),
            meeting_data.get('description'),
            meeting_data.get('organizer_id'),
            meeting_data.get('duration_minutes', 60),
            meeting_data.get('priority', 'Medium'),
            meeting_data.get('scheduled_start'),
            meeting_data.get('scheduled_end')
        ))
        
        # Add participants
        for participant in meeting_data.get('participants', []):
            participant_id = f"participant_{int(datetime.now().timestamp())}_{participant}"
            cursor.execute('''
                INSERT INTO meeting_participants (id, meeting_id, email)
                VALUES (?, ?, ?)
            ''', (participant_id, meeting_id, participant))
        
        conn.commit()
        conn.close()
        
        return meeting_id
    
    def get_meetings(self, organizer_id: str = None, status: str = None) -> List[Dict]:
        """Get meetings with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT m.*, GROUP_CONCAT(mp.email) as participants
            FROM meetings m
            LEFT JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE 1=1
        '''
        params = []
        
        if organizer_id:
            query += ' AND m.organizer_id = ?'
            params.append(organizer_id)
        
        if status:
            query += ' AND m.status = ?'
            params.append(status)
        
        query += ' GROUP BY m.id ORDER BY m.created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        meetings = []
        for row in rows:
            meeting = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'organizer_id': row[3],
                'duration_minutes': row[4],
                'priority': row[5],
                'status': row[6],
                'scheduled_start': row[7],
                'scheduled_end': row[8],
                'microsoft_event_id': row[9],
                'created_at': row[10],
                'updated_at': row[11],
                'participants': row[12].split(',') if row[12] else []
            }
            meetings.append(meeting)
        
        conn.close()
        return meetings
    
    def update_meeting_status(self, meeting_id: str, status: str) -> bool:
        """Update meeting status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE meetings
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, meeting_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting and its participants"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def cache_availability(self, user_email: str, date: str, start_time: str,
                          end_time: str, is_busy: bool, event_subject: str = None):
        """Cache user availability data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cache_id = f"cache_{user_email}_{date}_{start_time}"
        expires_at = datetime.now() + timedelta(hours=1)  # Cache for 1 hour
        
        cursor.execute('''
            INSERT OR REPLACE INTO availability_cache
            (id, user_email, date, start_time, end_time, is_busy, event_subject, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cache_id, user_email, date, start_time, end_time, is_busy, event_subject, expires_at))
        
        conn.commit()
        conn.close()
    
    def get_cached_availability(self, user_email: str, date: str) -> List[Dict]:
        """Get cached availability for a user on a specific date"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM availability_cache
            WHERE user_email = ? AND date = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (user_email, date))
        
        rows = cursor.fetchall()
        availability = []
        
        for row in rows:
            availability.append({
                'start_time': row[3],
                'end_time': row[4],
                'is_busy': bool(row[5]),
                'event_subject': row[6]
            })
        
        conn.close()
        return availability
    
    def log_ai_suggestion(self, meeting_request: Dict, suggestions: List[Dict],
                         selected_suggestion: Dict = None) -> str:
        """Log AI suggestions for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        log_id = f"ai_log_{int(datetime.now().timestamp())}"
        
        cursor.execute('''
            INSERT INTO ai_suggestions
            (id, meeting_request, suggestions, selected_suggestion, confidence_scores)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            log_id,
            json.dumps(meeting_request),
            json.dumps(suggestions),
            json.dumps(selected_suggestion) if selected_suggestion else None,
            json.dumps([s.get('confidence', 0) for s in suggestions])
        ))
        
        conn.commit()
        conn.close()
        
        return log_id
    
    def create_user(self, user_data: Dict) -> str:
        """Create a new user record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user_id = f"user_{int(datetime.now().timestamp())}"
        
        cursor.execute('''
            INSERT INTO users (id, email, name, microsoft_user_id, access_token, refresh_token)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            user_data.get('email'),
            user_data.get('name'),
            user_data.get('microsoft_user_id'),
            user_data.get('access_token'),
            user_data.get('refresh_token')
        ))
        
        conn.commit()
        conn.close()
        
        return user_id
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        
        if row:
            user = {
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'microsoft_user_id': row[3],
                'access_token': row[4],
                'refresh_token': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            }
            conn.close()
            return user
        
        conn.close()
        return None
    
    def update_user_tokens(self, user_id: str, access_token: str, refresh_token: str) -> bool:
        """Update user's Microsoft tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET access_token = ?, refresh_token = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (access_token, refresh_token, user_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success