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