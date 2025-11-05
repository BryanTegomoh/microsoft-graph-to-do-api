"""Test email configuration."""

import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.config import Config
from src.utils.logging_config import setup_logging
from src.writers.email_sender import EmailSender

def main():
    """Test email sending."""
    setup_logging()

    print("Testing email configuration...")
    print(f"From: {Config.EMAIL_FROM}")
    print(f"To: {Config.EMAIL_TO}")
    print(f"Server: {Config.EMAIL_SMTP_SERVER}:{Config.EMAIL_SMTP_PORT}")
    print()

    try:
        Config.validate()
        print("[OK] Configuration validated\n")
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
        print("\nPlease update your .env file with email settings.")
        sys.exit(1)

    print("Sending test email...")
    sender = EmailSender()

    if sender.send_test_email():
        print("\n[SUCCESS] Test email sent successfully!")
        print(f"Check your inbox at: {Config.EMAIL_TO}")
        print("\nNext step: Run 'python main.py' for your first daily brief!")
        return True
    else:
        print("\n[ERROR] Failed to send test email")
        print("\nCommon issues:")
        print("1. Gmail: Make sure you're using an App Password, not your regular password")
        print("   - Create one at: https://myaccount.google.com/apppasswords")
        print("2. Check that 2-Factor Authentication is enabled on your Google account")
        print("3. Verify EMAIL_FROM, EMAIL_TO, and EMAIL_PASSWORD in .env")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
