import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # Connect to Gmail's IMAP server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    # Try to login with the App Password from your .env
    mail.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
    print("✅ IMAP is ACTIVE and working!")
    mail.logout()
except Exception as e:
    print(f"❌ Connection failed. Error: {e}")
    print("This means either the App Password is wrong or IMAP is truly disabled.")