"""Test configuration and setup."""

import sys
import os
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_config():
    """Test configuration is valid."""
    print("Testing configuration...")

    try:
        from src.config import Config
        from src.utils.logging_config import setup_logging

        setup_logging()

        print("\n[OK] Imports successful")

        # Validate config
        Config.validate()
        print("[OK] Configuration valid")

        # Check credentials
        print("\nConfiguration Summary:")
        print(f"  CLIENT_ID: {'[OK] Set' if Config.CLIENT_ID else '[MISSING]'}")
        print(f"  TENANT_ID: {'[OK] Set' if Config.TENANT_ID else '[MISSING]'}")
        print(f"  CLIENT_SECRET: {'[OK] Set' if Config.CLIENT_SECRET else '[MISSING]'}")
        print(f"  AI_PROVIDER: {Config.AI_PROVIDER}")

        if Config.AI_PROVIDER == "anthropic":
            print(f"  ANTHROPIC_API_KEY: {'[OK] Set' if Config.ANTHROPIC_API_KEY else '[MISSING]'}")
        elif Config.AI_PROVIDER == "openai":
            print(f"  OPENAI_API_KEY: {'[OK] Set' if Config.OPENAI_API_KEY else '[MISSING]'}")
        elif Config.AI_PROVIDER == "google":
            print(f"  GOOGLE_API_KEY: {'[OK] Set' if Config.GOOGLE_API_KEY else '[MISSING]'}")

        print(f"\n  Email From: {Config.EMAIL_FROM}")
        print(f"  Email To: {Config.EMAIL_TO}")
        print(f"  Send Email Brief: {'Enabled' if Config.SEND_EMAIL_BRIEF else 'Disabled'}")
        print(f"\n  Output Directory: {Config.OUTPUT_DIR}")
        print(f"  Task Updates: {'Enabled' if Config.ENABLE_TASK_UPDATES else 'Disabled'}")
        print(f"  Markdown Brief: {'Enabled' if Config.GENERATE_MARKDOWN_BRIEF else 'Disabled'}")

        print("\n[SUCCESS] All tests passed!")
        print("\nNext steps:")
        print("1. Run: python test_email.py")
        print("2. Run: python main.py")
        print("3. Check your email for the brief")

        return True

    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required values are set.")
        print("See SETUP_GUIDE.md for detailed instructions.")
        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
