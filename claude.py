import os
import json
import re
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))

MODEL_NAME = "claude-sonnet-4-5-20250929"  # or "claude-3-5-haiku-20241022"?
MAX_TOKENS = 670 # 67 (~43 messages daily)

def extract_event_details(message_text: str) -> dict:
    """
    Uses Claude to extract event details from a forwarded message.
    Handles diverse event types: talks, workshops, hackathons, recruitment, career fairs, etc.
    
    Returns a dict with all fields - missing fields marked as 'TBC'.
    Required fields (title, event_type, date, synopsis, deadline, target_audience) MUST have values.
    """

    prompt = f"""You are an expert at extracting event information from university student group messages.

    These messages include: workshops, hackathons, recruitment drives, career fairs, Q&A sessions, mentorship programs, talks, networking events, and casual meetups.

    Here is a message about an event or activity:
    {message_text}

    Please extract and return ONLY a valid JSON object with these fields:
    {{
        "title": "event name/title - REQUIRED - infer intelligently if not explicit",
        "event_type": "REQUIRED - one of: Workshop, Hackathon, Talk, Career_Fair, Recruitment, Mentorship, QA_Session, Networking, Competition, Briefing, or Other",
        "date": "REQUIRED - date and time (e.g., '22 Oct 2025, 10am-2pm' or '8-9 Nov 2025' or 'Ongoing')",
        "location": "Physical location, 'Online', 'Hybrid', or 'TBC'",
        "fee": "0 if free, otherwise the amount as a float (e.g. 6.7, 10, 25), or assume free (0) if not specified",
        "signup_link": "URL to signup/register, 'Walk-in', or 'TBC'",
        "synopsis": "REQUIRED - 1-2 sentence description of what the event is about",
        "organisation": "organizing body/club/company (e.g., 'NUS Greyhats', 'DSO', 'Jane Street', 'NUS Fintech Society'), or 'TBC' if not mentioned",
        "deadline": "REQUIRED - registration/application deadline in format 'DD MMM YYYY, time' OR if not explicitly stated, estimate 24 hours before event start OR 'None' if ongoing/no deadline",
        "target_audience": "REQUIRED - who it's for (e.g., 'Women and gender-expansive students', 'CS students', 'Startup founders', 'All NUS students') - default to 'All students' if unclear",
        "key_speakers": "names of notable speakers/guests if mentioned, or 'None'",
        "refreshments": "type of refreshments if mentioned (e.g., 'Dinner', 'Lunch', 'Light refreshments', 'Snacks', 'Tea'), or 'None' if not mentioned",
        "contacts": "contact details for enquiries (usually telegram @), if mentioned, or 'None' if not mentioned."
    }}

    CRITICAL EXTRACTION RULES:
    1. **Required fields cannot be 'TBC'**: title, event_type, date, synopsis, deadline (estimate if needed), target_audience
    2. **Optional fields use 'TBC' if missing**: location, signup_link, key_speakers
    3. **Deadline estimation**: If no explicit deadline, calculate 24 hours before event date
    - Example: Event on "23 Oct 2025, 7pm" → deadline = "22 Oct 2025, 7pm"
    - If event is "Ongoing" or rolling recruitment → deadline = "None"
    4. **Target audience defaults**: If unclear → "All students"
    5. **Refreshments detection**: Look for keywords and extract the TYPE: "Dinner provided" → "Dinner", "Light refreshments" → "Light refreshments", "Snacks" → "Snacks", "Free acai" → "Acai", "Networking dinner" → "Dinner", etc. If nothing mentioned → "None"
    6. **Signup link priority**: Direct URL > Walk-in > Email > Telegram link > 'TBC'
    7. **Date format**: Always include year (2025 or 2026) for clarity
    8. **Organisation detection**: Look for organizing body - could be prefixed with "On Behalf of", company names, student clubs, government agencies, etc.
    9. **Contacts extraction**: Look for any contact details provided for enquiries (usually Telegram handles, e.g., @username). If none mentioned, set to "None". If more than one handle is provided, include all separated by commas. In front of each handle, include the platform if mentioned (e.g., Telegram @username), and retain the @ symbol for Telegram handles.

    Handle edge cases:
    - "Walk in anytime" → signup_link is "Walk-in", fee usually 0
    - Multiple dates → extract the main event date(s)
    - QR code mentions → signup_link = "TBC" (mention QR in synopsis if important)
    - Meta-events (newsletters) → extract the newsletter/post itself as the event

    Return ONLY valid JSON, nothing else."""

    # Generate response
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )
    response_text = response.content[0].text.strip()

    # Clean up response
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()
    
    try:
        event_data = json.loads(response_text)
        # Validate required fields are present
        required_fields = ["title", "event_type", "date", "synopsis", "deadline", "target_audience"]
        for field in required_fields:
            if field not in event_data or not event_data[field]:
                event_data[field] = "Unknown" if field != "target_audience" else "all students"
        
        return event_data
    
    except json.JSONDecodeError:
        print(f"⚠️ Claude response wasn't valid JSON: {response_text[:200]}")
        # Return minimal valid structure on parse failure
        return {
            "title": "Unable to parse event",
            "event_type": "other",
            "date": "TBC",
            "location": "TBC",
            "fee": "TBC",
            "signup_link": "TBC",
            "synopsis": "Could not automatically extract event details. Please view original message.",
            "organisation": "TBC",
            "deadline": "TBC",
            "target_audience": "all students",
            "key_speakers": "None",
            "refreshments": "None",
            "contacts": "None",
            "raw_message": message_text,
            "parse_error": True
        }

def clean_event_data(event_data: dict) -> dict:
    """
    Clean and standardize event data before saving to database.
    Applies formatting rules consistently.
    """
    cleaned = event_data.copy()
    if 'title' in cleaned: # Remove markdown from title
        cleaned['title'] = cleaned['title'].replace('**', '').replace('*', '').strip()
    if 'event_type' in cleaned:
        cleaned['event_type'] = cleaned['event_type'].capitalize()
    if 'refreshments' in cleaned: 
        cleaned['refreshments'] = cleaned['refreshments'].capitalize()

    # Convert fee to proper format (handle "free" -> 0, "TBC" -> None)
    fee = cleaned.get('fee')
    if fee in ['free', 'Free', 'FREE', 0, '0', 0.0]:
        cleaned['fee'] = 0.0
    elif fee in ['TBC', 'tbc', None]:
        cleaned['fee'] = None
    elif isinstance(fee, (int, float)):
        cleaned['fee'] = float(fee)
    elif isinstance(fee, str): # If it's a string like "$10.50" or "12.5", try to extract number
        match = re.search(r'\d+\.?\d*', fee)
        cleaned['fee'] = float(match.group()) if match else None
    
    return cleaned

def format_event_for_display(event_data: dict) -> str:
    """Format extracted event data into a readable Telegram message"""
    result = f"""
📌 {event_data.get('title', 'Untitled')}
🏷️ Type: {event_data.get('event_type', 'other')}
📅 Date: {event_data.get('date', 'TBC')}
📍 Location: {event_data.get('location', 'TBC')}
📝 Synopsis: {event_data.get('synopsis', 'TBC')}"""
    
    # --- Add optional fields if they have values --- #
    # Add org
    org = event_data.get('organisation', 'TBC')
    if org and org != 'TBC':
        result += f"\n🏢 Organised by: {org}"
    
    # Add fees
    fee = event_data.get('fee')
    if fee != 0.0:
        result += f"\n💰 Fee: {fee}"

    # Add signup link
    signup = event_data.get('signup_link', 'TBC')
    if signup and signup not in ['TBC', 'None']:
        if signup.startswith('http'):
            result += f"\n🔗 Sign up: {signup}"

    # Add target audience if not default
    if event_data.get('target_audience') and event_data['target_audience'] != 'All students':
        result += f"\n👥 For: {event_data['target_audience']}"
    
    # Add refreshments
    if event_data.get('refreshments') and event_data['refreshments'] not in ['None', 'No']:
        result += f"\n🍽️ Refreshments: {event_data['refreshments']}"
    
    # Add key speakers
    if event_data.get('key_speakers') and event_data['key_speakers'] != 'None':
        result += f"\n🎤 Speakers: {event_data['key_speakers']}"

    if event_data.get("parse_error"):
        result = "⚠️ Had trouble parsing this message automatically. I've saved what I could extract.\n" + result
    else:
        result = "✅ Event details extracted successfully!\n" + result
    
    return result