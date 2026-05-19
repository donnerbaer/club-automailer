#!/usr/bin/env python3
"""Quick SMTP configuration tester for web.de and other providers."""

import smtplib
import sys
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.web.de")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Test configurations
CONFIGS = [
    {"port": 587, "starttls": True,
        "name": "Port 587 with STARTTLS (standard)"},
    {"port": 465, "starttls": False, "name": "Port 465 with implicit SSL"},
    {"port": 25, "starttls": True, "name": "Port 25 with STARTTLS"},
]


def test_smtp(host: str, port: int, user: str, password: str, starttls: bool, config_name: str) -> bool:
    """Test SMTP connection with given config."""
    print(f"\n[TEST] {config_name}")
    print(f"       Host: {host}:{port} | User: {user}")

    try:
        if starttls:
            smtp = smtplib.SMTP(host, port, timeout=10)
            print(f"       ✓ Connected (will use STARTTLS)")
            smtp.starttls()
            print(f"       ✓ STARTTLS negotiated")
        else:
            smtp = smtplib.SMTP_SSL(host, port, timeout=10)
            print(f"       ✓ Connected (implicit SSL)")

        smtp.login(user, password)
        print(f"       ✓ Authentication SUCCESSFUL")
        smtp.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"       ✗ Auth failed: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"       ✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"       ✗ Connection error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[ERROR] Missing SMTP_USER or SMTP_PASSWORD in .env")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"SMTP Configuration Tester for {SMTP_HOST}")
    print(f"{'='*60}")

    success_count = 0
    for config in CONFIGS:
        if test_smtp(
            SMTP_HOST,
            config["port"],
            SMTP_USER,
            SMTP_PASSWORD,
            config["starttls"],
            config["name"]
        ):
            success_count += 1

    print(f"\n{'='*60}")
    if success_count > 0:
        print(f"✓ SUCCESS: Found {success_count} working configuration(s)")
        print(f"Update your .env with the correct SMTP_PORT and test again.")
    else:
        print(f"✗ FAILED: No configuration worked")
        print(f"Possible issues:")
        print(f"  1. Wrong password or credentials")
        print(f"  2. web.de may require an app-specific password")
        print(f"  3. SMTP may not be enabled for this account")
        print(f"  4. IP address may be blocked")
    print(f"{'='*60}\n")

    sys.exit(0 if success_count > 0 else 1)
