#!/usr/bin/env python3
"""Extended SMTP debugging for web.de authentication issues."""

import smtplib
import sys
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.web.de")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

print(f"{'='*70}")
print(f"Extended SMTP Diagnostics for {SMTP_HOST}")
print(f"{'='*70}\n")

print(f"Configuration from .env:")
print(f"  SMTP_HOST: {SMTP_HOST}")
print(f"  SMTP_USER: {SMTP_USER}")
print(
    f"  SMTP_PASSWORD: {'*' * (len(SMTP_PASSWORD) - 4) + SMTP_PASSWORD[-4:]}")
print()

# Step 1: Connection test
print("[1/4] Testing connection...")
try:
    smtp = smtplib.SMTP(SMTP_HOST, 587, timeout=10)
    print(f"  ✓ Connected to {SMTP_HOST}:587")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

# Step 2: STARTTLS test
print("[2/4] Testing STARTTLS...")
try:
    smtp.starttls()
    print(f"  ✓ STARTTLS successful")
except Exception as e:
    print(f"  ✗ STARTTLS failed: {e}")
    smtp.quit()
    sys.exit(1)

# Step 3: Detailed login debugging
print("[3/4] Attempting login...")
print(f"  Username: {SMTP_USER}")
print(f"  Password length: {len(SMTP_PASSWORD)} chars")

# Check for potential issues
if "@" not in SMTP_USER:
    print(f"  ⚠ WARNING: Username might be missing domain (@web.de)")

# Try login with extended error capture
try:
    smtp.login(SMTP_USER, SMTP_PASSWORD)
    print(f"  ✓ Login SUCCESSFUL!")
except smtplib.SMTPAuthenticationError as e:
    print(f"  ✗ Authentication failed: {e}")
    print()
    print(f"Troubleshooting:")
    print(f"  1. Check that SMTP is enabled in web.de account:")
    print(f"     → https://mein.web.de → Sicherheit")
    print(f"  2. If using 2FA, you may need an App-Passwort instead")
    print(f"  3. Try resetting your password at https://mein.web.de")
    print(f"  4. Check for special characters in password that need escaping")
    print(f"  5. Wait 15-30 minutes if you just changed the password")
    print(f"  6. Account might be locked after too many login attempts")
    smtp.quit()
    sys.exit(1)
except smtplib.SMTPException as e:
    print(f"  ✗ SMTP error: {e}")
    smtp.quit()
    sys.exit(1)

# Step 4: Send a test email (optional)
print("[4/4] Login successful! SMTP is configured correctly.")
print()

smtp.quit()

print(f"{'='*70}")
print(f"✓ All tests passed! Your SMTP is ready.")
print(f"{'='*70}\n")
