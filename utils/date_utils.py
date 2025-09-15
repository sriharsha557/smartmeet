# utils/date_utils.py
from datetime import datetime, timedelta, time
from typing import List, Dict, Tuple
import calendar

def get_business_hours(start_hour: int = 9, end_hour: int = 17) -> Tuple[time, time]:
    """Get business hours as time objects"""
    return time(start_hour, 0), time(end_hour, 0)

def format_time_slot(start_time: datetime, end_time: datetime) -> str:
    """Format a time slot for display"""
    date_str = start_time.strftime("%Y-%m-%d")
    start_str = start_time.strftime("%I:%M %p")
    end_str = end_time.strftime("%I:%M %p")
    return f"{date_str} from {start_str} to {end_str}"

def is_business_day(date: datetime) -> bool:
    """Check if a date is a business day (Monday-Friday)"""
    return date.weekday() < 5

def get_next_business_day(date: datetime) -> datetime:
    """Get the next business day after the given date"""
    next_day = date + timedelta(days=1)
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def get_business_days_in_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """Get all business days in a date range"""
    business_days = []
    current_date = start_date
    
    while current_date <= end_date:
        if is_business_day(current_date):
            business_days.append(current_date)
        current_date += timedelta(days=1)
    
    return business_days

def generate_time_slots(date: datetime, duration_minutes: int = 30, 
                       start_hour: int = 9, end_hour: int = 17) -> List[Dict]:
    """Generate time slots for a given date"""
    slots = []
    
    # Start at the beginning of business hours
    current_time = datetime.combine(date.date(), time(start_hour, 0))
    end_of_day = datetime.combine(date.date(), time(end_hour, 0))
    
    while current_time + timedelta(minutes=duration_minutes) <= end_of_day:
        slot_end = current_time + timedelta(minutes=duration_minutes)
        slots.append({
            'start': current_time,
            'end': slot_end,
            'duration_minutes': duration_minutes,
            'formatted': format_time_slot(current_time, slot_end)
        })
        current_time += timedelta(minutes=30)  # 30-minute intervals
    
    return slots

def time_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
    """Check if two time periods overlap"""
    return start1 < end2 and start2 < end1

def find_free_slots(busy_periods: List[Dict], date: datetime, 
                   duration_minutes: int = 60, start_hour: int = 9, end_hour: int = 17) -> List[Dict]:
    """Find free time slots on a given date, avoiding busy periods"""
    all_slots = generate_time_slots(date, duration_minutes, start_hour, end_hour)
    free_slots = []
    
    for slot in all_slots:
        is_free = True
        for busy_period in busy_periods:
            if time_overlap(slot['start'], slot['end'], busy_period['start'], busy_period['end']):
                is_free = False
                break
        
        if is_free:
            free_slots.append(slot)
    
    return free_slots

def get_week_dates(date: datetime) -> List[datetime]:
    """Get all dates in the same week as the given date"""
    # Find Monday of the week
    monday = date - timedelta(days=date.weekday())
    
    week_dates = []
    for i in range(7):
        week_dates.append(monday + timedelta(days=i))
    
    return week_dates

def get_month_business_days(year: int, month: int) -> List[datetime]:
    """Get all business days in a given month"""
    # Get first and last day of the month
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    
    return get_business_days_in_range(first_day, last_day)

def format_duration(minutes: int) -> str:
    """Format duration in minutes to human-readable string"""
    if minutes < 60:
        return f"{minutes} minutes"
    elif minutes == 60:
        return "1 hour"
    elif minutes < 120:
        return f"1 hour {minutes - 60} minutes"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours {remaining_minutes} minutes"

def parse_duration_string(duration_str: str) -> int:
    """Parse duration string to minutes"""
    duration_map = {
        "15 minutes": 15,
        "30 minutes": 30,
        "45 minutes": 45,
        "1 hour": 60,
        "1.5 hours": 90,
        "2 hours": 120,
        "2.5 hours": 150,
        "3 hours": 180
    }
    
    return duration_map.get(duration_str, 60)  # Default to 1 hour

def get_timezone_offset() -> str:
    """Get current timezone offset"""
    now = datetime.now()
    utc_now = datetime.utcnow()
    offset = now - utc_now
    
    hours = int(offset.total_seconds() // 3600)
    minutes = int((offset.total_seconds() % 3600) // 60)
    
    sign = '+' if hours >= 0 else '-'
    return f"{sign}{abs(hours):02d}:{abs(minutes):02d}"

def convert_to_utc(local_datetime: datetime) -> datetime:
    """Convert local datetime to UTC (simplified - assumes system timezone)"""
    # In a real implementation, you'd use proper timezone handling
    # This is a simplified version
    return local_datetime

def format_date_for_display(date: datetime) -> str:
    """Format date for user-friendly display"""
    today = datetime.now().date()
    date_only = date.date()
    
    if date_only == today:
        return "Today"
    elif date_only == today + timedelta(days=1):
        return "Tomorrow"
    elif date_only == today - timedelta(days=1):
        return "Yesterday"
    elif date_only < today + timedelta(days=7) and date_only > today:
        return date.strftime("%A")  # Day name for this week
    else:
        return date.strftime("%B %d, %Y")  # Full date

def get_meeting_time_suggestions(preferred_date: datetime, duration_minutes: int = 60) -> List[str]:
    """Get common meeting time suggestions for a date"""
    suggestions = []
    common_times = [9, 10, 11, 13, 14, 15, 16]  # Skip lunch hour (12)
    
    for hour in common_times:
        meeting_time = datetime.combine(preferred_date.date(), time(hour, 0))
        end_time = meeting_time + timedelta(minutes=duration_minutes)
        
        # Make sure meeting doesn't go past business hours
        if end_time.time() <= time(17, 0):
            suggestions.append(meeting_time.strftime("%I:%M %p"))
    
    return suggestions

def calculate_meeting_end_time(start_time: datetime, duration_str: str) -> datetime:
    """Calculate meeting end time based on start time and duration string"""
    duration_minutes = parse_duration_string(duration_str)
    return start_time + timedelta(minutes=duration_minutes)

def is_valid_meeting_time(start_time: datetime, duration_minutes: int, 
                         business_start: int = 9, business_end: int = 17) -> bool:
    """Check if a meeting time is within business hours"""
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Check if start time is within business hours
    if start_time.time() < time(business_start, 0) or start_time.time() >= time(business_end, 0):
        return False
    
    # Check if end time is within business hours
    if end_time.time() > time(business_end, 0):
        return False
    
    # Check if it's a business day
    if not is_business_day(start_time):
        return False
    
    return True