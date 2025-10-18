import os
import json
from datetime import datetime
from anthropic import Anthropic

client = Anthropic()

def extract_event_details(message_text: str) -> dict:
    prompt = f"""Extract event details from this message and return ONLY valid JSON (no other text):

    MESSAGE:
    {message_text}

    RESPONSE FORMAT (JSON only):
    {{
        "event_name": "name of the event",
        "date": "date (e.g., '15 Nov 2024' or 'Not specified')",
        "start_time": "start time (e.g., '2:00 PM' or 'Not specified')",
        "end_time": "end time (e.g., '5:00 PM' or 'Not specified')",
        "location": "venue or 'Online' if virtual",
        "fee": "cost (e.g., '$10', 'Free', or 'Not specified')",
        "signup_link": "URL to registration/signup",
        "synopsis": "brief description (1-2 sentences)",
        "organisation": "organizer/company/group name",
        "category": "one of: networking, school, work, social, workshop, competition, conference, other",
        "registration_deadline": "deadline to register (e.g., '1 Nov 2024' or 'Not specified')"
    }}

    Rules:
    - Use "NIL" for any missing information
    - For category, choose the BEST fit from the list
    - Keep responses concise
    - Return ONLY the JSON object, nothing else"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022", # "claude-3-5-haiku-20241022" haiku is cheaper
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    response_text = response.content[0].text
    
    try:
        event_data = json.loads(response_text)
        return event_data
    except json.JSONDecodeError:
        return {
            "error": "Could not parse event details",
            "raw_response": response_text
        }


def create_event_record(message_text: str, extracted_data: dict, user_id: int, username: str = None) -> dict:
    """
    Args:
        message_text: The forwarded message content
        extracted_data: LLM-extracted event fields
        user_id: Telegram user ID (unique identifier)
        username: Telegram username (optional, may be None)
    """
    
    if "error" in extracted_data:
        return {
            "error": extracted_data["error"],
            "raw_message": message_text,
            "user_id": user_id,
            "username": username,
            "date_created": datetime.now().isoformat()
        }
    
    # Create the full record
    record = {
        "event_name": extracted_data.get("event_name", "Not specified"),
        "date": extracted_data.get("date", "Not specified"),
        "start_time": extracted_data.get("start_time", "Not specified"),
        "end_time": extracted_data.get("end_time", "Not specified"),
        "location": extracted_data.get("location", "Not specified"),
        "fee": extracted_data.get("fee", "Not specified"),
        "signup_link": extracted_data.get("signup_link", "Not specified"),
        "synopsis": extracted_data.get("synopsis", "Not specified"),
        "organisation": extracted_data.get("organisation", "Not specified"),
        "category": extracted_data.get("category", "other"),
        "registration_deadline": extracted_data.get("registration_deadline", "Not specified"),
        "raw_message": message_text,
        "user_id": user_id,
        "username": username,
        "date_created": datetime.now().isoformat()
    }
    
    return record


def format_event_for_display(event_data: dict) -> str:
    """Format extracted event data into a readable Telegram message"""
    
    if "error" in event_data:
        return f"❌ Error extracting details:\n{event_data.get('raw_response', 'Unknown error')}"
    
    return f"""📅 Event Details:
        🎯 Event: {event_data.get('event_name', 'N/A')}
        📆 Date: {event_data.get('date', 'N/A')}
        ⏰ Time: {event_data.get('start_time', 'N/A')} - {event_data.get('end_time', 'N/A')}
        📍 Location: {event_data.get('location', 'N/A')}
        💰 Fee: {event_data.get('fee', 'N/A')}
        🏢 Organiser: {event_data.get('organisation', 'N/A')}
        🏷️ Category: {event_data.get('category', 'N/A')}
        📝 Synopsis: {event_data.get('synopsis', 'N/A')}
        📅 Register by: {event_data.get('registration_deadline', 'N/A')}
        🔗 Signup: {event_data.get('signup_link', 'N/A')}"""