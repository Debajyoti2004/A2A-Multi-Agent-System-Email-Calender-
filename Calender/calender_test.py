import os
from google_auth import get_calendar_service
from dotenv import load_dotenv

load_dotenv()

try:
    print("🔄 Testing Google Calendar Connection...")
    service = get_calendar_service()
    
    # Try to list the next 1 event to verify access
    events_result = service.events().list(
        calendarId='primary', 
        maxResults=1, 
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    print("✅ CALENDAR ACCESS ACTIVE!")
    print(f"Connected to: {os.getenv('EMAIL_USER')}")
    
except Exception as e:
    print(f"❌ Connection failed. Error: {e}")
    print("\nTroubleshooting Check:")
    print("1. Does 'credentials.json' exist in your folder?")
    print("2. Is your Google Cloud App in 'Production' mode?")