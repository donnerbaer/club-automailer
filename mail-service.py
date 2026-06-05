"""Scheduled mail service for automated notification delivery.

This script is intended to be executed by cron. It reads active notification
rules from the same database used by the Flask web application, resolves due
targets (events or members), sends emails, and writes audit logs.

Usage:
  python mail-service.py          # Normal cron mode (silent unless errors)
  python mail-service.py --debug  # Verbose diagnostic output
    python mail-service.py --simulate  # Dry-run mode (no real email send, no audit log writes)
    python mail-service.py --force-working-hours-monthly  # Force monthly working-hours mail
"""

import os
import sys
import random
import smtplib
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask
from icalendar import Calendar, Event as ICalEvent
from jinja2 import ChainableUndefined
from jinja2.exceptions import SecurityError, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import extract, func

from app import db
from app.model.model import (
    Event,
    Group,
    Member,
    NotificationLog,
    NotificationRule,
    NotificationRuleReceiver,
    NotificationTemplate,
    TriggerType,
)
from app.model.model import WorkingHoursLog
from config import Config


load_dotenv()

# Global debug flag
DEBUG = "--debug" in sys.argv
SIMULATE = (
    "--simulate" in sys.argv
    or "--sumlate" in sys.argv
    or os.getenv("SIMULATE", "") == "1"
)
FORCE_WORKING_HOURS_MONTHLY = (
    "--force-working-hours-monthly" in sys.argv
    or os.getenv("FORCE_WORKING_HOURS_MONTHLY", "") == "1"
)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
TEMPLATE_ENV = SandboxedEnvironment(
    autoescape=False, undefined=ChainableUndefined)


class TemplateParticipants(list):
    """List-like wrapper that also exposes summary attributes for templates."""

    def __init__(self, items):
        super().__init__(items or [])
        self.count = len(self)
        self.names = ", ".join(
            [item.get("name", "") for item in self if item.get("name")]
        )
        self.emails = ", ".join(
            [item.get("email", "") for item in self if item.get("email")]
        )


# Calendar import link generation functions
def generate_google_calendar_link(event: Event) -> str:
    """Generate a Google Calendar event creation link."""
    text = quote(event.title or "Event")

    # Format dates for Google Calendar: YYYYMMDDTHHMMSS
    start_date = event.start_at.strftime("%Y%m%dT%H%M%S")
    end_date = event.end_at.strftime(
        "%Y%m%dT%H%M%S") if event.end_at else start_date
    dates = f"{start_date}/{end_date}"

    details = quote(event.description or "")
    location = quote(event.location or "")

    params = [
        f"text={text}",
        f"dates={dates}",
    ]

    if details:
        params.append(f"details={details}")
    if location:
        params.append(f"location={location}")

    return f"https://calendar.google.com/calendar/r/eventedit?{'&'.join(params)}"


def generate_outlook_calendar_link(event: Event) -> str:
    """Generate an Outlook calendar event creation link."""
    # Format dates for Outlook: YYYY-MM-DDTHH:MM:SS
    start_dt = event.start_at.strftime("%Y-%m-%dT%H:%M:%S")
    end_dt = event.end_at.strftime(
        "%Y-%m-%dT%H:%M:%S") if event.end_at else start_dt

    subject = quote(event.title or "Event")
    body = quote(event.description or "")
    location = quote(event.location or "")

    params = [
        "rru=addevent",
        f"startdt={start_dt}",
        f"enddt={end_dt}",
        f"subject={subject}",
    ]

    if body:
        params.append(f"body={body}")
    if location:
        params.append(f"location={location}")

    return f"https://outlook.office.com/calendar/0/deeplink/compose?{'&'.join(params)}"


def generate_ics_file(event: Event) -> bytes:
    """Generate ICS (iCalendar) file content as bytes."""
    cal = Calendar()
    cal.add('prodid', '-//ENT//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')

    ical_event = ICalEvent()
    ical_event.add('summary', event.title or "Event")
    ical_event.add('dtstart', event.start_at)
    if event.end_at:
        ical_event.add('dtend', event.end_at)
    if event.description:
        ical_event.add('description', event.description)
    if event.location:
        ical_event.add('location', event.location)

    ical_event.add(
        'uid', f"event-{event.id}@{Config.EVENT_DOMAIN}")

    ical_event.add('dtstamp', datetime.now())

    cal.add_component(ical_event)

    return cal.to_ical()


def debug_log(message: str) -> None:
    """Print debug message if DEBUG mode is enabled."""
    if DEBUG:
        print(f"[DEBUG] {message}")


def sleep_between_emails() -> None:
    """Add a random pause between deliveries to avoid burst sending."""
    if SIMULATE:
        return
    time.sleep(random.randint(1, 3))


def build_runtime_app() -> Flask:
    """Create a minimal Flask app for database access in cron jobs."""
    flask_app = Flask("runtime_app")
    flask_app.config.from_object(Config)
    db.init_app(flask_app)
    return flask_app


def send_email(recipient: str, subject: str, body: str, event: Event = None) -> None:
    """Send a single plain-text email via SMTP.

    If event is provided, automatically appends calendar import links to the body
    and attaches an ICS file.
    """
    # Skip sending to example.org addresses (commonly used as a test domain)
    if recipient and recipient.lower().endswith("@example.org"):
        debug_log(f"Skipping email send to test domain: {recipient}")
        return

    email_body = body

    # Automatically add calendar import links if event is provided
    if event:
        google_link = generate_google_calendar_link(event)
        outlook_link = generate_outlook_calendar_link(event)

        calendar_section = f"\n\n{'='*70}\nAdd to Calendar:\n{'='*70}\n"
        calendar_section += f"Google Calendar: {google_link}\n\n"
        calendar_section += f"Outlook: {outlook_link}\n\n"

        email_body = body + calendar_section

    email_body = email_body + \
        "\n\nThis is an automated notification. Please do not reply to this email."

    if SIMULATE:
        #    debug_log(f"[SIMULATE] Rendered email for {recipient}")
        #    debug_log(f"[SIMULATE] Subject: {subject}")
        #    if DEBUG:
        #        print("[DEBUG] [SIMULATE] Body:")
        #        print(email_body)
        #        print("[DEBUG] [SIMULATE] End of rendered body")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["BCC"] = recipient
    msg.set_content(email_body)

    # Attach ICS file if event is provided
    if event:
        ics_filename = f"{event.title or 'event'}_{event.id}.ics"
        # Sanitize filename
        ics_filename = "".join(
            c for c in ics_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        ics_content = generate_ics_file(event)
        msg.add_attachment(ics_content, maintype='text',
                           subtype='calendar', filename=ics_filename)

    debug_log(f"Sending email to {recipient} | Subject: {subject[:50]}")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        debug_log("  └─ ✓ Email sent successfully")
    except Exception as e:
        debug_log(f"  └─ ✗ SMTP Error: {type(e).__name__}: {e}")
        raise


def render_text(raw_text: str, context: dict) -> str:
    """Render template content using safe placeholder substitution."""

    class SafeDict(defaultdict):
        def __missing__(self, key):
            return ""

    if raw_text is None:
        return ""

    if "{{" in raw_text or "{%" in raw_text:
        try:
            return TEMPLATE_ENV.from_string(raw_text).render(context)
        except (SecurityError, TemplateSyntaxError, UndefinedError) as exc:
            debug_log(
                f"Template render fallback ({type(exc).__name__}): {exc}")
            return raw_text

    try:
        return raw_text.format_map(SafeDict(str, context))
    except (ValueError, KeyError, IndexError):
        # Keep service execution robust if a stored template is malformed.
        return raw_text


def format_template_value(value):
    """Convert values to stable plain-text template output."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def add_years(value, years):
    """Add years to a date or datetime value for anniversary templates."""
    if value in (None, ""):
        return ""

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value

    if not isinstance(value, (datetime, date)):
        return value

    try:
        shifted = value.replace(year=value.year + int(years))
    except ValueError:
        shifted = value.replace(month=2, day=28, year=value.year + int(years))
    return format_template_value(shifted)


TEMPLATE_ENV.globals["add_years"] = add_years


def build_person_template_context(member: Member = None, email: str = "") -> dict:
    """Build a reusable context for a member-like person."""
    first_name = member.first_name if member and member.first_name else ""
    last_name = member.last_name if member and member.last_name else ""
    resolved_email = email or (member.email if member and member.email else "")
    member_number = member.member_number if member and member.member_number else ""
    phone = member.phone if member and member.phone else ""
    birth_date = member.birth_date if member else None
    join_date = member.join_date if member else None
    active = member.active if member else False

    # Compute age if birth date is available
    age = None
    if birth_date:
        today = date.today()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )

    return {
        "first_name": first_name,
        "last_name": last_name,
        "fullname": f"{first_name} {last_name}".strip(),
        "email": resolved_email,
        "phone": phone,
        "member_number": member_number,
        "number": member_number,
        "birth_date": birth_date,
        "birthday": birth_date,
        "_birth_date": format_template_value(birth_date),
        "join_date": join_date,
        "member_since": join_date,
        "_join_date": format_template_value(join_date),
        "active": active,
        "age": age,
    }


def build_named_template_context(name: str, person_context: dict) -> dict:
    """Expose a person context both nested and as flat aliases."""
    return {
        name: person_context,
        f"{name}_first_name": person_context["first_name"],
        f"{name}_last_name": person_context["last_name"],
        f"{name}_fullname": person_context.get("fullname", ""),
        f"{name}_email": person_context["email"],
        f"{name}_phone": person_context.get("phone", ""),
        f"{name}_member_number": person_context["member_number"],
        f"{name}_birth_date": person_context["birth_date"],
        f"{name}_join_date": person_context["join_date"],
        f"{name}_age": person_context.get("age"),
    }


def build_member_template_context(member: Member) -> dict:
    """Build a nested and flat template context for a member."""
    # Base person context
    person_ctx = build_person_template_context(member)

    # Compute working hours aggregates
    try:
        required_hours = float(member.required_hours or 0)
    except Exception:
        required_hours = 0.0

    all_hours = 0.0
    hours_this_year = 0.0
    hours_today = 0.0
    hours_yesterday = 0.0
    hours_this_week = 0.0
    hours_last_week = 0.0
    hours_this_month = 0.0
    hours_last_month = 0.0
    hours_last_year = 0.0

    today = date.today()
    current_year = today.year
    current_month = today.month

    for log in getattr(member, "working_hours_logs", []) or []:
        try:
            h = float(getattr(log, "hours", 0) or 0)
        except Exception:
            h = 0.0

        log_date = getattr(log, "date", None)
        if not log_date:
            continue

        all_hours += h

        # This year
        if log_date.year == current_year:
            hours_this_year += h

        # Today
        if log_date == today:
            hours_today += h

        # Yesterday
        if log_date == today - timedelta(days=1):
            hours_yesterday += h

        # This week (Monday=0, Sunday=6)
        monday = today - timedelta(days=today.weekday())
        if monday <= log_date <= today:
            hours_this_week += h

        # Last week
        last_monday = monday - timedelta(days=7)
        if last_monday <= log_date < monday:
            hours_last_week += h

        # This month
        if log_date.year == current_year and log_date.month == current_month:
            hours_this_month += h

        # Last month
        if current_month == 1:
            last_m, last_y = 12, current_year - 1
        else:
            last_m, last_y = current_month - 1, current_year
        if log_date.year == last_y and log_date.month == last_m:
            hours_last_month += h

        # Last year
        if log_date.year == current_year - 1:
            hours_last_year += h

    # Compute membership duration
    membership_duration = None
    if member.join_date:
        td = today - member.join_date
        membership_duration = td.days // 365

    # Add aggregated fields to the nested person context
    person_ctx.update(
        {
            "required_hours": required_hours,
            "all_hours": all_hours,
            "hours_this_year": hours_this_year,
            "hours": {
                "today": hours_today,
                "yesterday": hours_yesterday,
                "this_week": hours_this_week,
                "last_week": hours_last_week,
                "this_month": hours_this_month,
                "last_month": hours_last_month,
                "this_year": hours_this_year,
                "last_year": hours_last_year,
            },
            "membership_duration": membership_duration,
        }
    )

    # Build named context and also expose flat aliases for the new fields
    ctx = build_named_template_context("member", person_ctx)
    ctx.update(
        {
            "member_required_hours": required_hours,
            "member_all_hours": all_hours,
            "member_hours_this_year": hours_this_year,
            "member_hours_today": hours_today,
            "member_hours_yesterday": hours_yesterday,
            "member_hours_this_week": hours_this_week,
            "member_hours_last_week": hours_last_week,
            "member_hours_this_month": hours_this_month,
            "member_hours_last_month": hours_last_month,
            "member_hours_last_year": hours_last_year,
            "member_membership_duration": membership_duration,
        }
    )

    return ctx


def build_receiver_template_context(recipient_email: str, receiver_member: Member = None) -> dict:
    """Build a nested and flat template context for the email receiver."""
    return build_named_template_context(
        "receiver",
        build_person_template_context(receiver_member, email=recipient_email),
    )


def build_recipient_template_context(recipient_email: str, recipient_member: Member = None) -> dict:
    """Build a nested and flat template context for recipient (newer name for receiver)."""
    return build_named_template_context(
        "recipient",
        build_person_template_context(recipient_member, email=recipient_email),
    )


def build_subject_template_context(member: Member) -> dict:
    """Build context for the 'subject' member (the one being referenced/about)."""
    member_ctx = build_member_template_context(member)

    # Create subject.* aliases with the same data as member.*
    subject_ctx = {}
    for key, value in member_ctx.items():
        if key.startswith("member_"):
            subject_ctx[key.replace("member_", "subject_")] = value
        elif key == "member":
            # Nested subject object
            subject_ctx["subject"] = value

    # Also add the flat top-level keys for convenience
    subject_ctx.update({
        "subject_first_name": member_ctx.get("member_first_name", ""),
        "subject_last_name": member_ctx.get("member_last_name", ""),
        "subject_fullname": member_ctx.get("member_fullname", ""),
        "subject_email": member_ctx.get("member_email", ""),
        "subject_phone": member_ctx.get("member_phone", ""),
        "subject_member_number": member_ctx.get("member_member_number", ""),
        "subject_birth_date": member_ctx.get("member_birth_date"),
        "subject_join_date": member_ctx.get("member_join_date"),
        "subject_age": member_ctx.get("member_age"),
        "subject_active": member_ctx.get("member_active", False),
        "subject_hours_today": member_ctx.get("member_hours_today", 0),
        "subject_hours_yesterday": member_ctx.get("member_hours_yesterday", 0),
        "subject_hours_this_week": member_ctx.get("member_hours_this_week", 0),
        "subject_hours_last_week": member_ctx.get("member_hours_last_week", 0),
        "subject_hours_this_month": member_ctx.get("member_hours_this_month", 0),
        "subject_hours_last_month": member_ctx.get("member_hours_last_month", 0),
        "subject_hours_this_year": member_ctx.get("member_hours_this_year", 0),
        "subject_hours_last_year": member_ctx.get("member_hours_last_year", 0),
        "subject_membership_duration": member_ctx.get("member_membership_duration"),
        "subject_required_hours": member_ctx.get("member_required_hours", 0),
        "subject_all_hours": member_ctx.get("member_all_hours", 0),
    })

    return subject_ctx


def build_anniversary_deprecated_context(member: Member) -> dict:
    """Build context for deprecated anniversary.* placeholders (kept for backwards compatibility)."""
    years = None
    if member and member.join_date:
        today = date.today()
        years = today.year - member.join_date.year - (
            (today.month, today.day) < (
                member.join_date.month, member.join_date.day)
        )

    return {
        "anniversary": {
            "firstname": member.first_name if member else "",
            "lastname": member.last_name if member else "",
            "fullname": f"{member.first_name} {member.last_name}".strip() if member else "",
            "years": years,
            "member_since": format_template_value(member.join_date) if member and member.join_date else "",
        },
        "anniversary_firstname": member.first_name if member else "",
        "anniversary_lastname": member.last_name if member else "",
        "anniversary_fullname": f"{member.first_name} {member.last_name}".strip() if member else "",
        "anniversary_years": years,
        "anniversary_member_since": format_template_value(member.join_date) if member and member.join_date else "",
    }


def build_event_template_context(event: Event, days_before: int) -> dict:
    """Build a nested and flat template context for an event."""
    # Compute duration in hours
    duration_hours = None
    if event.start_at and event.end_at:
        td = event.end_at - event.start_at
        duration_hours = td.total_seconds() / 3600.0

    # Get participants (list of member names/emails)
    participants = []
    participants_count = 0
    if event.participants:
        for ep in event.participants:
            if ep.member:
                name = f"{ep.member.first_name} {ep.member.last_name}".strip()
                participants.append({
                    "name": name,
                    "email": ep.member.email,
                    "member_number": ep.member.member_number,
                })
                participants_count += 1

    participant_collection = TemplateParticipants(participants)

    event_context = {
        "title": event.title,
        "description": event.description or "",
        "start_at": format_template_value(event.start_at),
        "end_at": format_template_value(event.end_at),
        "start_date": format_template_value(event.start_at),
        "end_date": format_template_value(event.end_at),
        "start_time": event.start_at.strftime("%H:%M") if event.start_at else "",
        "end_time": event.end_at.strftime("%H:%M") if event.end_at else "",
        "duration_hours": duration_hours,
        "location": event.location or "",
        "participants": participant_collection,
        "participants_count": participants_count,
        "participants_names": participant_collection.names,
        "participants_emails": participant_collection.emails,
    }

    # Generate calendar import links
    calendar_links = {
        "google": generate_google_calendar_link(event),
        "outlook": generate_outlook_calendar_link(event),
    }

    # Build participant name/email lists for convenience
    participant_names = ", ".join([p["name"] for p in participants])
    participant_emails = ", ".join([p["email"] for p in participants])

    return {
        "event": event_context,
        "event_title": event_context["title"],
        "event_description": event_context["description"],
        "event_start": event_context["start_at"],
        "event_end": event_context["end_at"],
        "event_start_date": event_context["start_date"],
        "event_start_time": event_context["start_time"],
        "event_end_date": event_context["end_date"],
        "event_end_time": event_context["end_time"],
        "event_duration_hours": duration_hours,
        "event_location": event_context["location"],
        "event_participants": participants,
        "event_participants_count": participants_count,
        "event_participants_names": participant_names,
        "event_participants_emails": participant_emails,
        "days_before": days_before,
        "calendar_links": calendar_links,
        "event_calendar_google": calendar_links["google"],
        "event_calendar_outlook": calendar_links["outlook"],
    }


def build_trigger_template_context(rule: NotificationRule, trigger: TriggerType) -> dict:
    """Build context for trigger/rule information."""
    return {
        "trigger": {
            "name": rule.name or "",
            "description": trigger.description if trigger else rule.description or "",
            "code": trigger.code if trigger else "",
            "days_before": rule.days_before or 0,
        },
        "trigger_name": rule.name or "",
        "trigger_description": trigger.description if trigger else rule.description or "",
        "trigger_days_before": rule.days_before or 0,
    }


def build_global_hours_context() -> dict:
    """Build context for global working hours statistics."""
    try:
        total_hours = db.session.query(
            func.sum(WorkingHoursLog.hours)).scalar() or 0
        total_hours = float(total_hours)
    except Exception:
        total_hours = 0.0

    try:
        current_year = date.today().year
        total_hours_this_year = (
            db.session.query(func.sum(WorkingHoursLog.hours))
            .filter(extract("year", WorkingHoursLog.date) == current_year)
            .scalar()
            or 0
        )
        total_hours_this_year = float(total_hours_this_year)
    except Exception:
        total_hours_this_year = 0.0

    try:
        current_month = date.today().month
        total_hours_this_month = (
            db.session.query(func.sum(WorkingHoursLog.hours))
            .filter(
                extract("year", WorkingHoursLog.date) == date.today().year,
                extract("month", WorkingHoursLog.date) == current_month,
            )
            .scalar()
            or 0
        )
        total_hours_this_month = float(total_hours_this_month)
    except Exception:
        total_hours_this_month = 0.0

    try:
        if date.today().month == 1:
            last_month, last_year = 12, date.today().year - 1
        else:
            last_month, last_year = date.today().month - 1, date.today().year
        total_hours_last_month = (
            db.session.query(func.sum(WorkingHoursLog.hours))
            .filter(
                extract("year", WorkingHoursLog.date) == last_year,
                extract("month", WorkingHoursLog.date) == last_month,
            )
            .scalar()
            or 0
        )
        total_hours_last_month = float(total_hours_last_month)
    except Exception:
        total_hours_last_month = 0.0

    return {
        "hours": {
            "total": total_hours,
            "this_year": total_hours_this_year,
            "this_month": total_hours_this_month,
            "last_month": total_hours_last_month,
        },
        "hours_total": total_hours,
        "hours_this_year": total_hours_this_year,
        "hours_this_month": total_hours_this_month,
        "hours_last_month": total_hours_last_month,
        "all_working_hours": total_hours,
        "all_working_hours_this_year": total_hours_this_year,
    }


def build_participants_stats_context() -> dict:
    """Build context for global member/participant statistics."""
    try:
        total_members = db.session.query(func.count(Member.id)).scalar() or 0
    except Exception:
        total_members = 0

    try:
        active_members = (
            db.session.query(func.count(Member.id))
            .filter(Member.active == True)
            .scalar()
            or 0
        )
    except Exception:
        active_members = 0

    try:
        current_year = date.today().year
        current_month = date.today().month
        members_with_hours_this_month = (
            db.session.query(func.count(
                func.distinct(WorkingHoursLog.member_id)))
            .filter(
                extract("year", WorkingHoursLog.date) == current_year,
                extract("month", WorkingHoursLog.date) == current_month,
            )
            .scalar()
            or 0
        )
    except Exception:
        members_with_hours_this_month = 0

    try:
        if current_month == 1:
            last_month, last_year = 12, current_year - 1
        else:
            last_month, last_year = current_month - 1, current_year
        members_with_hours_last_month = (
            db.session.query(func.count(
                func.distinct(WorkingHoursLog.member_id)))
            .filter(
                extract("year", WorkingHoursLog.date) == last_year,
                extract("month", WorkingHoursLog.date) == last_month,
            )
            .scalar()
            or 0
        )
    except Exception:
        members_with_hours_last_month = 0

    try:
        members_with_hours_this_year = (
            db.session.query(func.count(
                func.distinct(WorkingHoursLog.member_id)))
            .filter(extract("year", WorkingHoursLog.date) == current_year)
            .scalar()
            or 0
        )
    except Exception:
        members_with_hours_this_year = 0

    return {
        "participants": {
            "total": {"count": total_members},
            "active": {"count": active_members},
            "worked": {
                "this_month": {"count": members_with_hours_this_month},
                "last_month": {"count": members_with_hours_last_month},
                "this_year": {"count": members_with_hours_this_year},
            },
        },
        "participants_total_count": total_members,
        "participants_active_count": active_members,
        "participants_worked_this_month_count": members_with_hours_this_month,
        "participants_worked_last_month_count": members_with_hours_last_month,
        "participants_worked_this_year_count": members_with_hours_this_year,
    }


def build_birthdays_context() -> dict:
    """Build context for birthdays in various periods."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    next_monday = sunday + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)

    try:
        # Today
        birthdays_today = [
            m
            for m in db.session.query(Member).all()
            if m.birth_date
            and m.birth_date.month == today.month
            and m.birth_date.day == today.day
        ]

        # Tomorrow
        birthdays_tomorrow = [
            m
            for m in db.session.query(Member).all()
            if m.birth_date
            and m.birth_date.month == tomorrow.month
            and m.birth_date.day == tomorrow.day
        ]

        # This week
        birthdays_this_week = [
            m
            for m in db.session.query(Member).all()
            if m.birth_date
            and (
                (m.birth_date.month == today.month and today.day <=
                 m.birth_date.day <= sunday.day)
                or (m.birth_date.month == sunday.month and sunday.month != today.month and m.birth_date.day <= sunday.day)
            )
        ]

        # Next week
        birthdays_next_week = [
            m
            for m in db.session.query(Member).all()
            if m.birth_date
            and (
                (m.birth_date.month == next_monday.month and next_monday.day <=
                 m.birth_date.day <= next_sunday.day)
                or (m.birth_date.month == next_sunday.month and next_sunday.month != next_monday.month and m.birth_date.day <= next_sunday.day)
            )
        ]

        # Current month
        birthdays_current_month = [
            m
            for m in db.session.query(Member).all()
            if m.birth_date and m.birth_date.month == today.month
        ]

        # Next month
        next_month = today.month + 1 if today.month < 12 else 1
        birthdays_next_month = [
            m
            for m in db.session.query(Member).all()
            if m.birth_date and m.birth_date.month == next_month
        ]
    except Exception:
        birthdays_today = []
        birthdays_tomorrow = []
        birthdays_this_week = []
        birthdays_next_week = []
        birthdays_current_month = []
        birthdays_next_month = []

    return {
        "birthdays": {
            "today": birthdays_today,
            "tomorrow": birthdays_tomorrow,
            "this_week": birthdays_this_week,
            "next_week": birthdays_next_week,
            "current_month": birthdays_current_month,
            "next_month": birthdays_next_month,
            "count": {
                "today": len(birthdays_today),
                "this_week": len(birthdays_this_week),
                "current_month": len(birthdays_current_month),
            },
        },
        "birthdays_today": birthdays_today,
        "birthdays_tomorrow": birthdays_tomorrow,
        "birthdays_this_week": birthdays_this_week,
        "birthdays_next_week": birthdays_next_week,
        "birthdays_current_month": birthdays_current_month,
        "birthdays_next_month": birthdays_next_month,
        "birthdays_count_today": len(birthdays_today),
        "birthdays_count_this_week": len(birthdays_this_week),
        "birthdays_count_current_month": len(birthdays_current_month),
    }


def build_anniversaries_context() -> dict:
    """Build context for membership anniversaries in various periods."""
    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1

    try:
        # Current month
        anniversaries_current_month = [
            m
            for m in db.session.query(Member).all()
            if m.join_date and m.join_date.month == today.month
        ]

        # Next month
        anniversaries_next_month = [
            m
            for m in db.session.query(Member).all()
            if m.join_date and m.join_date.month == next_month
        ]
    except Exception:
        anniversaries_current_month = []
        anniversaries_next_month = []

    return {
        "membership": {
            "anniversaries": {
                "current_month": anniversaries_current_month,
                "next_month": anniversaries_next_month,
                "count": {
                    "current_month": len(anniversaries_current_month),
                    "next_month": len(anniversaries_next_month),
                },
            }
        },
        "membership_anniversaries_current_month": anniversaries_current_month,
        "membership_anniversaries_next_month": anniversaries_next_month,
        "membership_anniversaries_count_current_month": len(anniversaries_current_month),
        "membership_anniversaries_count_next_month": len(anniversaries_next_month),
    }


def build_current_date_context() -> dict:
    """Build context for current, previous, and next date/time information."""
    today = date.today()
    current_month = today.month
    current_year = today.year

    # Previous month
    if current_month == 1:
        prev_month = 12
    else:
        prev_month = current_month - 1

    # Next month
    next_month = current_month + 1 if current_month < 12 else 1

    # Month names
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    return {
        "current": {
            "date": format_template_value(today),
            "time": datetime.now().strftime("%H:%M:%S"),
            "month": month_names[current_month - 1],
            "month_number": current_month,
            "year": current_year,
        },
        "previous": {
            "month": month_names[prev_month - 1],
            "month_number": prev_month,
        },
        "next": {
            "month": month_names[next_month - 1],
            "month_number": next_month,
        },
        "current_date": format_template_value(today),
        "current_time": datetime.now().strftime("%H:%M:%S"),
        "current_month": month_names[current_month - 1],
        "current_year": current_year,
        "previous_month": month_names[prev_month - 1],
        "next_month": month_names[next_month - 1],
    }


def build_members_with_hours_context() -> dict:
    """Build context for members with working hours in various time periods."""
    today = date.today()
    current_year = today.year
    current_month = today.month
    monday = today - timedelta(days=today.weekday())
    last_monday = monday - timedelta(days=7)
    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = current_year if current_month > 1 else current_year - 1

    try:
        # Current week
        members_with_hours_this_week = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                WorkingHoursLog.date >= monday,
                WorkingHoursLog.date <= today,
            )
            .distinct()
            .all()
        )

        # Last week
        members_with_hours_last_week = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                WorkingHoursLog.date >= last_monday,
                WorkingHoursLog.date < monday,
            )
            .distinct()
            .all()
        )

        # Current month
        members_with_hours_this_month = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                extract("year", WorkingHoursLog.date) == current_year,
                extract("month", WorkingHoursLog.date) == current_month,
            )
            .distinct()
            .all()
        )

        # Last month
        members_with_hours_last_month = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                extract("year", WorkingHoursLog.date) == last_month_year,
                extract("month", WorkingHoursLog.date) == last_month,
            )
            .distinct()
            .all()
        )

        # Current year
        members_with_hours_this_year = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(extract("year", WorkingHoursLog.date) == current_year)
            .distinct()
            .all()
        )

        # Last year
        members_with_hours_last_year = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(extract("year", WorkingHoursLog.date) == current_year - 1)
            .distinct()
            .all()
        )
    except Exception:
        members_with_hours_this_week = []
        members_with_hours_last_week = []
        members_with_hours_this_month = []
        members_with_hours_last_month = []
        members_with_hours_this_year = []
        members_with_hours_last_year = []

    return {
        "members": {
            "with_hours": {
                "current": {
                    "week": members_with_hours_this_week,
                    "month": members_with_hours_this_month,
                    "year": members_with_hours_this_year,
                },
                "last": {
                    "week": members_with_hours_last_week,
                    "month": members_with_hours_last_month,
                    "year": members_with_hours_last_year,
                },
            }
        },
        "members_with_hours_this_week": members_with_hours_this_week,
        "members_with_hours_last_week": members_with_hours_last_week,
        "members_with_hours_this_month": members_with_hours_this_month,
        "members_with_hours_last_month": members_with_hours_last_month,
        "members_with_hours_this_year": members_with_hours_this_year,
        "members_with_hours_last_year": members_with_hours_last_year,
    }


def build_members_without_hours_context() -> dict:
    """Build context for members without working hours in various time periods."""
    today = date.today()
    current_year = today.year
    current_month = today.month
    monday = today - timedelta(days=today.weekday())
    last_monday = monday - timedelta(days=7)
    last_month = current_month - 1 if current_month > 1 else 12
    last_month_year = current_year if current_month > 1 else current_year - 1

    try:
        # All active members
        all_active_members = db.session.query(
            Member).filter(Member.active.is_(True)).all()

        # Members with hours this week
        members_with_hours_this_week = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                WorkingHoursLog.date >= monday,
                WorkingHoursLog.date <= today,
            )
            .distinct()
            .all()
        )
        members_without_hours_this_week = [
            m for m in all_active_members if m not in members_with_hours_this_week]

        # Members with hours last week
        members_with_hours_last_week = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                WorkingHoursLog.date >= last_monday,
                WorkingHoursLog.date < monday,
            )
            .distinct()
            .all()
        )
        members_without_hours_last_week = [
            m for m in all_active_members if m not in members_with_hours_last_week]

        # Members with hours this month
        members_with_hours_this_month = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                extract("year", WorkingHoursLog.date) == current_year,
                extract("month", WorkingHoursLog.date) == current_month,
            )
            .distinct()
            .all()
        )
        members_without_hours_this_month = [
            m for m in all_active_members if m not in members_with_hours_this_month]

        # Members with hours last month
        members_with_hours_last_month = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(
                extract("year", WorkingHoursLog.date) == last_month_year,
                extract("month", WorkingHoursLog.date) == last_month,
            )
            .distinct()
            .all()
        )
        members_without_hours_last_month = [
            m for m in all_active_members if m not in members_with_hours_last_month]

        # Members with hours this year
        members_with_hours_this_year = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(extract("year", WorkingHoursLog.date) == current_year)
            .distinct()
            .all()
        )
        members_without_hours_this_year = [
            m for m in all_active_members if m not in members_with_hours_this_year]

        # Members with hours last year
        members_with_hours_last_year = (
            db.session.query(Member)
            .join(WorkingHoursLog, Member.id == WorkingHoursLog.member_id)
            .filter(extract("year", WorkingHoursLog.date) == current_year - 1)
            .distinct()
            .all()
        )
        members_without_hours_last_year = [
            m for m in all_active_members if m not in members_with_hours_last_year]
    except Exception:
        members_without_hours_this_week = []
        members_without_hours_last_week = []
        members_without_hours_this_month = []
        members_without_hours_last_month = []
        members_without_hours_this_year = []
        members_without_hours_last_year = []

    return {
        "members": {
            "without_hours": {
                "current": {
                    "week": members_without_hours_this_week,
                    "month": members_without_hours_this_month,
                    "year": members_without_hours_this_year,
                },
                "last": {
                    "week": members_without_hours_last_week,
                    "month": members_without_hours_last_month,
                    "year": members_without_hours_last_year,
                },
            }
        },
        "members_without_hours_this_week": members_without_hours_this_week,
        "members_without_hours_last_week": members_without_hours_last_week,
        "members_without_hours_this_month": members_without_hours_this_month,
        "members_without_hours_last_month": members_without_hours_last_month,
        "members_without_hours_this_year": members_without_hours_this_year,
        "members_without_hours_last_year": members_without_hours_last_year,
    }


def build_members_by_birthday_context() -> dict:
    """Build context for members with birthdays in the current month."""
    today = date.today()
    current_month = today.month

    try:
        members_birthday_current_month = [
            m
            for m in db.session.query(Member).all()
            if m.birth_date and m.birth_date.month == current_month
        ]
    except Exception:
        members_birthday_current_month = []

    return {
        "members": {
            "birthday": {
                "current_month": members_birthday_current_month,
            }
        },
        "members_birthday_current_month": members_birthday_current_month,
    }


def build_birthdays_milestones_context() -> dict:
    """Build context for birthdays filtered by milestone ages (40, 50, 60, etc.)."""
    today = date.today()

    try:
        all_members = db.session.query(Member).all()

        # Common milestone ages
        milestones = {40, 50, 60, 70, 80, 90, 100}
        birthdays_by_milestone = {}

        for milestone in milestones:
            birthdays_by_milestone[milestone] = [
                m for m in all_members
                if m.birth_date
                and (today.year - m.birth_date.year - (
                    (today.month, today.day) < (
                        m.birth_date.month, m.birth_date.day)
                )) == milestone
            ]
    except Exception:
        birthdays_by_milestone = {}

    return {
        "birthdays": {
            "milestones": birthdays_by_milestone,
        },
        "birthdays_milestone_40": birthdays_by_milestone.get(40, []),
        "birthdays_milestone_50": birthdays_by_milestone.get(50, []),
        "birthdays_milestone_60": birthdays_by_milestone.get(60, []),
        "birthdays_milestone_70": birthdays_by_milestone.get(70, []),
        "birthdays_milestone_80": birthdays_by_milestone.get(80, []),
        "birthdays_milestone_90": birthdays_by_milestone.get(90, []),
        "birthdays_milestone_100": birthdays_by_milestone.get(100, []),
    }


def build_anniversaries_milestones_context() -> dict:
    """Build context for membership anniversaries filtered by milestone years (10, 25, 50, etc.)."""
    today = date.today()

    try:
        all_members = db.session.query(Member).all()

        # Common milestone years
        milestones = {10, 25, 50, 75, 100}
        anniversaries_by_milestone = {}

        for milestone in milestones:
            anniversaries_by_milestone[milestone] = [
                m for m in all_members
                if m.join_date
                and (today.year - m.join_date.year - (
                    (today.month, today.day) < (
                        m.join_date.month, m.join_date.day)
                )) == milestone
            ]
    except Exception:
        anniversaries_by_milestone = {}

    return {
        "membership": {
            "anniversaries": {
                "milestones": anniversaries_by_milestone,
            }
        },
        "membership_anniversaries_milestone_10": anniversaries_by_milestone.get(10, []),
        "membership_anniversaries_milestone_25": anniversaries_by_milestone.get(25, []),
        "membership_anniversaries_milestone_50": anniversaries_by_milestone.get(50, []),
        "membership_anniversaries_milestone_75": anniversaries_by_milestone.get(75, []),
        "membership_anniversaries_milestone_100": anniversaries_by_milestone.get(100, []),
    }


def build_upcoming_birthdays_context() -> dict:
    """Build context for upcoming birthdays in various time periods."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    next_monday = sunday + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)

    try:
        all_members = db.session.query(Member).all()

        # Today
        upcoming_birthdays_today = [
            m for m in all_members
            if m.birth_date
            and m.birth_date.month == today.month
            and m.birth_date.day == today.day
        ]

        # Tomorrow
        upcoming_birthdays_tomorrow = [
            m for m in all_members
            if m.birth_date
            and m.birth_date.month == tomorrow.month
            and m.birth_date.day == tomorrow.day
        ]

        # This week
        upcoming_birthdays_this_week = [
            m for m in all_members
            if m.birth_date
            and (
                (m.birth_date.month == today.month and today.day <=
                 m.birth_date.day <= sunday.day)
                or (m.birth_date.month == sunday.month and sunday.month != today.month and m.birth_date.day <= sunday.day)
            )
        ]

        # Next week
        upcoming_birthdays_next_week = [
            m for m in all_members
            if m.birth_date
            and (
                (m.birth_date.month == next_monday.month and next_monday.day <=
                 m.birth_date.day <= next_sunday.day)
                or (m.birth_date.month == next_sunday.month and next_sunday.month != next_monday.month and m.birth_date.day <= next_sunday.day)
            )
        ]

        # Next month
        next_month = today.month + 1 if today.month < 12 else 1
        upcoming_birthdays_next_month = [
            m for m in all_members
            if m.birth_date and m.birth_date.month == next_month
        ]
    except Exception:
        upcoming_birthdays_today = []
        upcoming_birthdays_tomorrow = []
        upcoming_birthdays_this_week = []
        upcoming_birthdays_next_week = []
        upcoming_birthdays_next_month = []

    return {
        "upcoming_birthdays": {
            "current": {
                "today": upcoming_birthdays_today,
                "this_week": upcoming_birthdays_this_week,
            },
            "next": {
                "week": upcoming_birthdays_next_week,
                "month": upcoming_birthdays_next_month,
                "tomorrow": upcoming_birthdays_tomorrow,
            },
        },
        "upcoming_birthdays_today": upcoming_birthdays_today,
        "upcoming_birthdays_tomorrow": upcoming_birthdays_tomorrow,
        "upcoming_birthdays_this_week": upcoming_birthdays_this_week,
        "upcoming_birthdays_next_week": upcoming_birthdays_next_week,
        "upcoming_birthdays_next_month": upcoming_birthdays_next_month,
    }


def build_upcoming_anniversaries_context() -> dict:
    """Build context for upcoming membership anniversaries in various time periods."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    next_monday = sunday + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)

    try:
        all_members = db.session.query(Member).all()

        # Today
        upcoming_anniversaries_today = [
            m for m in all_members
            if m.join_date
            and m.join_date.month == today.month
            and m.join_date.day == today.day
        ]

        # Tomorrow
        upcoming_anniversaries_tomorrow = [
            m for m in all_members
            if m.join_date
            and m.join_date.month == tomorrow.month
            and m.join_date.day == tomorrow.day
        ]

        # This week
        upcoming_anniversaries_this_week = [
            m for m in all_members
            if m.join_date
            and (
                (m.join_date.month == today.month and today.day <=
                 m.join_date.day <= sunday.day)
                or (m.join_date.month == sunday.month and sunday.month != today.month and m.join_date.day <= sunday.day)
            )
        ]

        # Next week
        upcoming_anniversaries_next_week = [
            m for m in all_members
            if m.join_date
            and (
                (m.join_date.month == next_monday.month and next_monday.day <=
                 m.join_date.day <= next_sunday.day)
                or (m.join_date.month == next_sunday.month and next_sunday.month != next_monday.month and m.join_date.day <= next_sunday.day)
            )
        ]

        # Next month
        next_month = today.month + 1 if today.month < 12 else 1
        upcoming_anniversaries_next_month = [
            m for m in all_members
            if m.join_date and m.join_date.month == next_month
        ]
    except Exception:
        upcoming_anniversaries_today = []
        upcoming_anniversaries_tomorrow = []
        upcoming_anniversaries_this_week = []
        upcoming_anniversaries_next_week = []
        upcoming_anniversaries_next_month = []

    return {
        "upcoming_anniversaries": {
            "current": {
                "today": upcoming_anniversaries_today,
                "this_week": upcoming_anniversaries_this_week,
            },
            "next": {
                "week": upcoming_anniversaries_next_week,
                "month": upcoming_anniversaries_next_month,
                "tomorrow": upcoming_anniversaries_tomorrow,
            },
        },
        "upcoming_anniversaries_today": upcoming_anniversaries_today,
        "upcoming_anniversaries_tomorrow": upcoming_anniversaries_tomorrow,
        "upcoming_anniversaries_this_week": upcoming_anniversaries_this_week,
        "upcoming_anniversaries_next_week": upcoming_anniversaries_next_week,
        "upcoming_anniversaries_next_month": upcoming_anniversaries_next_month,
    }


def build_upcoming_events_context() -> dict:
    """Build context for upcoming events in various time periods."""
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    next_monday = sunday + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)
    next_month = today.month + 1 if today.month < 12 else 1
    next_month_year = today.year if today.month < 12 else today.year + 1

    try:
        all_events = db.session.query(Event).filter(Event.start_at > now).all()

        # Today
        upcoming_events_today = [
            e for e in all_events
            if e.start_at.date() == today
        ]

        # Tomorrow
        upcoming_events_tomorrow = [
            e for e in all_events
            if e.start_at.date() == tomorrow
        ]

        # This week
        upcoming_events_this_week = [
            e for e in all_events
            if monday <= e.start_at.date() <= sunday
        ]

        # Next week
        upcoming_events_next_week = [
            e for e in all_events
            if next_monday <= e.start_at.date() <= next_sunday
        ]

        # Next month
        upcoming_events_next_month = [
            e for e in all_events
            if e.start_at.month == next_month and e.start_at.year == next_month_year
        ]
    except Exception:
        upcoming_events_today = []
        upcoming_events_tomorrow = []
        upcoming_events_this_week = []
        upcoming_events_next_week = []
        upcoming_events_next_month = []

    return {
        "upcoming_events": {
            "current": {
                "today": upcoming_events_today,
                "this_week": upcoming_events_this_week,
            },
            "next": {
                "week": upcoming_events_next_week,
                "month": upcoming_events_next_month,
                "tomorrow": upcoming_events_tomorrow,
            },
        },
        "upcoming_events_today": upcoming_events_today,
        "upcoming_events_tomorrow": upcoming_events_tomorrow,
        "upcoming_events_this_week": upcoming_events_this_week,
        "upcoming_events_next_week": upcoming_events_next_week,
        "upcoming_events_next_month": upcoming_events_next_month,
    }


def log_notification(
    rule_id: int,
    recipient_email: str,
    subject: str,
    status: str,
    event_id: int = None,
    event_title: str = None,
    member_id: int = None,
    body: str = None,
    error_message: str = None,
) -> None:
    """Persist one delivery attempt in the notification log."""
    if SIMULATE:
        debug_log(
            f"[SIMULATE] Persisting NotificationLog entry | rule_id={rule_id} "
            f"recipient={recipient_email} status={status}"
        )

    entry = NotificationLog(
        rule_id=rule_id,
        event_id=event_id,
        event_title=event_title,
        member_id=member_id,
        recipient_email=recipient_email,
        subject=subject,
        body=body,
        status=status,
        error_message=error_message,
    )
    db.session.add(entry)
    db.session.commit()


def already_sent(rule_id: int, recipient_email: str, event_id: int = None, member_id: int = None) -> bool:
    """Check if a successful notification already exists for this target."""
    row = NotificationLog.query.filter_by(
        rule_id=rule_id,
        recipient_email=recipient_email,
        event_id=event_id,
        member_id=member_id,
        status="SENT",
    ).first()
    return row is not None


def resolve_recipients(rule: NotificationRule, fallback_members=None) -> list[dict]:
    """Resolve recipient list from rule receivers with optional fallback."""
    recipients = []
    receivers = NotificationRuleReceiver.query.filter_by(rule_id=rule.id).all()

    debug_log(
        f"Rule {rule.id} ({rule.name}): Resolving {len(receivers)} receiver(s)...")

    for receiver in receivers:
        receiver_type = (receiver.receiver_type or "").strip().upper()

        # Support legacy values from the web UI ("email" / "group").
        if receiver_type in ("CUSTOM_EMAIL", "EMAIL") and receiver.custom_email:
            recipients.append(
                {"email": receiver.custom_email.strip(), "member_id": None})
            debug_log(f"  └─ Custom email: {receiver.custom_email}")

        if receiver_type == "GROUP" and receiver.group_id:
            members = (
                Member.query.join(Member.groups)
                .filter(Group.id == receiver.group_id)
                .filter(Member.active.is_(True), Member.email.isnot(None))
                .all()
            )
            debug_log(
                f"  └─ Group {receiver.group_id}: {len(members)} active member(s)")
            recipients.extend(
                {"email": member.email.strip(), "member_id": member.id}
                for member in members
                if member.email
            )

    if not recipients and fallback_members:
        debug_log(
            f"  └─ No direct receivers, using {len(fallback_members)} fallback member(s)")
        recipients.extend(
            {"email": member.email.strip(), "member_id": member.id}
            for member in fallback_members
            if member and member.email
        )

    dedup = {}
    for recipient in recipients:
        email = recipient.get("email", "").lower()
        if email and email not in dedup:
            dedup[email] = recipient

    result = list(dedup.values())
    debug_log(f"  └─ Total deduplicated recipients: {len(result)}")
    return result


def due_members_by_date(member_date_field, target_day) -> list[Member]:
    """Return active members whose date-field month/day matches target_day."""
    return (
        Member.query.filter(Member.active.is_(True))
        .filter(member_date_field.isnot(None))
        .filter(extract("month", member_date_field) == target_day.month)
        .filter(extract("day", member_date_field) == target_day.day)
        .all()
    )


def process_event_start_rule(
    rule: NotificationRule,
    template: NotificationTemplate,
    now_dt: datetime,
    trigger_code: str,
    trigger: TriggerType = None,
) -> None:
    """Send notifications for EVENT_START trigger rules."""
    # Consider any future event whose start time is within the configured
    # "days_before" window. This ensures we still send notifications when a
    # previous scheduled run was missed, as long as the event hasn't started
    # yet and no successful notification exists.
    deadline = now_dt + timedelta(days=rule.days_before or 0)

    due_events = (
        Event.query.filter(Event.start_at > now_dt)
        .filter(Event.start_at <= deadline)
        .all()
    )

    debug_log(
        f"  └─ EVENT_START: Looking for events between {now_dt} and {deadline} → {len(due_events)} found")

    for event in due_events:
        # Only process events matching the rule's trigger code. Many setups
        # use custom trigger codes (e.g. TELL_SPOPI_1) stored in
        # `event.event_type`, so compare against the rule trigger. Keep the
        # original behavior when the trigger code is the generic
        # 'EVENT_START'.
        event_type = (event.event_type or "").upper()
        if trigger_code != "EVENT_START" and event_type != trigger_code:
            continue
        participants = [
            ep.member for ep in event.participants if ep.member and ep.member.active]
        recipients = resolve_recipients(rule, fallback_members=participants)

        for index, recipient in enumerate(recipients):
            email = recipient["email"]
            member_id = recipient.get("member_id")
            receiver_member = db.session.get(
                Member, member_id) if member_id else None

            if already_sent(rule.id, email, event_id=event.id, member_id=member_id):
                continue

            context = {
                "recipient_email": email,
            }
            context.update(build_receiver_template_context(
                email, receiver_member))
            context.update(build_recipient_template_context(
                email, receiver_member))
            context.update(build_event_template_context(
                event, rule.days_before or 0))
            context.update(build_trigger_template_context(rule, trigger))
            context.update(build_global_hours_context())
            context.update(build_participants_stats_context())
            context.update(build_birthdays_context())
            context.update(build_anniversaries_context())
            context.update(build_current_date_context())
            context.update(build_members_with_hours_context())
            context.update(build_members_without_hours_context())
            context.update(build_members_by_birthday_context())
            context.update(build_birthdays_milestones_context())
            context.update(build_anniversaries_milestones_context())
            context.update(build_upcoming_birthdays_context())
            context.update(build_upcoming_anniversaries_context())
            context.update(build_upcoming_events_context())

            subject = render_text(template.subject_template, context)
            body = render_text(template.body_template, context)

            try:
                send_email(email, subject, body, event=event)
                log_notification(
                    rule_id=rule.id,
                    event_id=event.id,
                    event_title=event.title,
                    member_id=member_id,
                    recipient_email=email,
                    subject=subject,
                    body=body,
                    status="SENT",
                )
            except (smtplib.SMTPException, OSError, ValueError) as exc:
                db.session.rollback()
                log_notification(
                    rule_id=rule.id,
                    event_id=event.id,
                    event_title=event.title,
                    member_id=member_id,
                    recipient_email=email,
                    subject=subject,
                    body=body,
                    status="FAILED",
                    error_message=str(exc),
                )

            if index < len(recipients) - 1:
                sleep_between_emails()


def process_member_date_rule(
    rule: NotificationRule,
    template: NotificationTemplate,
    now_dt: datetime,
    trigger_code: str,
    trigger: TriggerType = None,
) -> None:
    """Send notifications for BIRTHDAY and MEMBER_ANNIVERSARY rules."""
    target_day = now_dt.date() + timedelta(days=rule.days_before or 0)
    date_field = Member.birth_date if trigger_code == "BIRTHDAY" else Member.join_date
    due_members = due_members_by_date(date_field, target_day)

    debug_log(
        f"  └─ {trigger_code}: Looking for members on {target_day} → {len(due_members)} found")

    for member in due_members:
        fallback_members = [member] if member.email else []
        recipients = resolve_recipients(
            rule, fallback_members=fallback_members)

        for index, recipient in enumerate(recipients):
            email = recipient["email"]
            recipient_member_id = recipient.get("member_id")
            receiver_member = db.session.get(
                Member, recipient_member_id) if recipient_member_id else None
            reference_member_id = member.id

            if already_sent(rule.id, email, member_id=reference_member_id):
                continue

            context = {
                "recipient_email": email,
                "trigger_date": format_template_value(target_day),
                "days_before": rule.days_before or 0,
            }
            context.update(build_receiver_template_context(
                email, receiver_member))
            context.update(build_recipient_template_context(
                email, receiver_member))
            context.update(build_member_template_context(member))
            context.update(build_subject_template_context(member))
            context.update(build_anniversary_deprecated_context(member))
            context.update(build_trigger_template_context(rule, trigger))
            context.update(build_global_hours_context())
            context.update(build_participants_stats_context())
            context.update(build_birthdays_context())
            context.update(build_anniversaries_context())
            context.update(build_current_date_context())
            context.update(build_members_with_hours_context())
            context.update(build_members_without_hours_context())
            context.update(build_members_by_birthday_context())
            context.update(build_birthdays_milestones_context())
            context.update(build_anniversaries_milestones_context())
            context.update(build_upcoming_birthdays_context())
            context.update(build_upcoming_anniversaries_context())
            context.update(build_upcoming_events_context())

            subject = render_text(template.subject_template, context)
            body = render_text(template.body_template, context)

            try:
                send_email(email, subject, body)
                log_notification(
                    rule_id=rule.id,
                    member_id=reference_member_id,
                    recipient_email=email,
                    subject=subject,
                    body=body,
                    status="SENT",
                )
            except (smtplib.SMTPException, OSError, ValueError) as exc:
                db.session.rollback()
                log_notification(
                    rule_id=rule.id,
                    member_id=reference_member_id,
                    recipient_email=email,
                    subject=subject,
                    body=body,
                    status="FAILED",
                    error_message=str(exc),
                )

            if index < len(recipients) - 1:
                sleep_between_emails()


def process_working_hours_monthly_rule(
    rule: NotificationRule,
    template: NotificationTemplate,
    now_dt: datetime,
    trigger_code: str,
    trigger: TriggerType = None,
) -> None:
    """Send a monthly working-hours summary to every member on the 1st of the month."""
    # Only run on the 1st day of the month
    if now_dt.date().day != 1 and not (DEBUG or FORCE_WORKING_HOURS_MONTHLY):
        debug_log("  └─ SKIPPED: Working hours monthly trigger runs on day 1 only")
        return

    members = Member.query.filter(Member.active.is_(True)).all()
    debug_log(
        f"  └─ WORKING_HOURS_MONTHLY: {len(members)} member(s) to process")

    # Precompute global aggregates
    try:
        total_hours = db.session.query(
            func.sum(WorkingHoursLog.hours)).scalar() or 0
    except Exception:
        total_hours = 0
    try:
        year = date.today().year
        total_hours_year = (
            db.session.query(func.sum(WorkingHoursLog.hours))
            .filter(extract('year', WorkingHoursLog.date) == year)
            .scalar()
            or 0
        )
    except Exception:
        total_hours_year = 0

    for index, member in enumerate(members):
        if not member.email:
            continue

        recipient = member.email.strip()

        # Avoid duplicate sends within the same month/year
        recent = (
            NotificationLog.query.filter_by(
                rule_id=rule.id, member_id=member.id, recipient_email=recipient, status="SENT"
            )
            .filter(extract('year', NotificationLog.sent_at) == now_dt.year)
            .filter(extract('month', NotificationLog.sent_at) == now_dt.month)
            .first()
        )
        if recent:
            continue

        context = {"recipient_email": recipient}
        context.update(build_receiver_template_context(
            recipient, receiver_member=member))
        context.update(build_recipient_template_context(
            recipient, recipient_member=member))
        context.update(build_member_template_context(member))
        context.update(build_subject_template_context(member))
        context.update(build_anniversary_deprecated_context(member))
        context.update(build_trigger_template_context(rule, trigger))
        context.update(build_global_hours_context())
        context.update(build_participants_stats_context())
        context.update(build_birthdays_context())
        context.update(build_anniversaries_context())
        context.update(build_current_date_context())
        context.update(build_members_with_hours_context())
        context.update(build_members_without_hours_context())
        context.update(build_members_by_birthday_context())
        context.update(build_birthdays_milestones_context())
        context.update(build_anniversaries_milestones_context())
        context.update(build_upcoming_birthdays_context())
        context.update(build_upcoming_anniversaries_context())
        context.update(build_upcoming_events_context())

        subject = render_text(template.subject_template, context)
        body = render_text(template.body_template, context)

        try:
            send_email(recipient, subject, body)
            log_notification(
                rule_id=rule.id,
                member_id=member.id,
                recipient_email=recipient,
                subject=subject,
                body=body,
                status="SENT",
            )
        except (smtplib.SMTPException, OSError, ValueError) as exc:
            db.session.rollback()
            log_notification(
                rule_id=rule.id,
                member_id=member.id,
                recipient_email=recipient,
                subject=subject,
                body=body,
                status="FAILED",
                error_message=str(exc),
            )

        if index < len(members) - 1:
            sleep_between_emails()


def is_recurring_rule_due(rule: NotificationRule, now_dt: datetime) -> bool:
    """Check if a recurring rule is due today.

    Args:
        rule: The notification rule to check
        now_dt: The current datetime to check against

    Returns:
        True if the rule should be executed today, False otherwise
    """
    if not rule.recurrence_type:
        return False

    now_date = now_dt.date()

    # Respect optional end date
    if getattr(rule, 'recurrence_end_date', None):
        try:
            if now_date > rule.recurrence_end_date:
                return False
        except Exception:
            pass

    if rule.recurrence_type == "daily":
        interval = int(rule.recurrence_interval or 1)
        # Use rule.created_at as start anchor if available
        start_date = rule.created_at.date() if getattr(
            rule, 'created_at', None) else now_date
        days = (now_date - start_date).days
        return (days % interval) == 0

    if rule.recurrence_type == "weekly":
        # Weekly recurrence: check weekdays and optional interval
        weekdays = []
        if getattr(rule, 'recurrence_weekdays', None):
            try:
                weekdays = [int(x) for x in rule.recurrence_weekdays.split(
                    ',') if x is not None and str(x) != '']
            except Exception:
                weekdays = []
        if not weekdays:
            return False
        if now_date.weekday() not in weekdays:
            return False
        interval = int(rule.recurrence_interval or 1)
        start_date = rule.created_at.date() if getattr(
            rule, 'created_at', None) else now_date
        weeks = (now_date - start_date).days // 7
        return (weeks % interval) == 0

    if rule.recurrence_type == "monthly":
        # Monthly recurrence: check if today matches the configured day of month
        # Option A: day of month
        if getattr(rule, 'recurrence_day', None):
            # Handle months with fewer days (e.g., Feb 30 -> Feb 28)
            max_day = (now_date.replace(day=1) + timedelta(days=32)
                       ).replace(day=1) - timedelta(days=1)
            target_day = min(rule.recurrence_day, max_day.day)
            if now_date.day == target_day:
                return True
        # Option B: nth weekday of month (e.g., 2nd Tuesday)
        if getattr(rule, 'recurrence_monthly_week', None) and getattr(rule, 'recurrence_weekday', None) is not None:
            n = int(rule.recurrence_monthly_week)
            weekday = int(rule.recurrence_weekday)
            year = now_date.year
            month = now_date.month
            # compute nth weekday

            def nth_weekday(year, month, weekday, n):
                from datetime import date as _date
                # find first occurrence of weekday in month
                first = _date(year, month, 1)
                first_weekday = first.weekday()
                days_until = (weekday - first_weekday) % 7
                first_occurrence = first + timedelta(days=days_until)
                if n >= 1 and n <= 4:
                    candidate = first_occurrence + timedelta(days=7*(n-1))
                    if candidate.month == month:
                        return candidate
                # handle last occurrence
                # find last day
                last = (first.replace(day=1) + timedelta(days=32)
                        ).replace(day=1) - timedelta(days=1)
                # walk back to find last weekday
                days_back = (last.weekday() - weekday) % 7
                last_occurrence = last - timedelta(days=days_back)
                if n == 5:
                    return last_occurrence
                return None

            candidate = nth_weekday(year, month, weekday, n)
            if candidate and candidate == now_date:
                return True
        return False

    elif rule.recurrence_type == "yearly":
        # Yearly recurrence: check if today matches the configured month and day
        if rule.recurrence_month is None or rule.recurrence_day_yearly is None:
            return False
        # Handle leap year edge cases (e.g., Feb 29)
        try:
            target_date = now_date.replace(
                month=rule.recurrence_month, day=rule.recurrence_day_yearly)
        except ValueError:
            # Day doesn't exist in this month (e.g., Feb 30)
            max_day = (now_date.replace(day=1) + timedelta(days=32)
                       ).replace(day=1) - timedelta(days=1)
            target_date = now_date.replace(
                month=rule.recurrence_month, day=max(1, max_day.day))

        return now_date == target_date

    return False


def process_recurring_rule(rule: NotificationRule, template: NotificationTemplate,
                           now_dt: datetime) -> None:
    """Process a recurring notification rule (monthly or yearly).

    Args:
        rule: The notification rule to process
        template: The notification template to use
        now_dt: The current datetime
    """
    debug_log(
        f"Processing recurring rule: {rule.id} | Type: {rule.recurrence_type}")

    # Build recipient list
    recipients = []
    for receiver in rule.receivers:
        if receiver.receiver_type == "group" and receiver.group_id:
            group = db.session.get(Group, receiver.group_id)
            if group and group.members:
                recipients.extend(
                    [m.email for m in group.members if m.email and m.active])
        elif receiver.receiver_type == "custom_email" and receiver.custom_email:
            recipients.append(receiver.custom_email)

    if not recipients:
        debug_log(f"  └─ SKIPPED: No recipients configured")
        return

    # Build template context for recurring rules
    context = {
        "current_date": now_dt.date(),
        "current_time": now_dt.time(),
        "rule_name": rule.name,
    }

    # Render subject and body
    subject = render_text(template.subject_template, context)
    body = render_text(template.body_template, context)

    # Send to all recipients
    for index, recipient in enumerate(recipients):
        try:
            send_email(recipient, subject, body)
            log_notification(
                rule_id=rule.id,
                recipient_email=recipient,
                subject=subject,
                body=body,
                status="SENT",
            )
            debug_log(f"  └─ Email sent to {recipient}")
        except (smtplib.SMTPException, OSError, ValueError) as exc:
            db.session.rollback()
            log_notification(
                rule_id=rule.id,
                recipient_email=recipient,
                subject=subject,
                body=body,
                status="FAILED",
                error_message=str(exc),
            )
            debug_log(f"  └─ Failed to send to {recipient}: {exc}")

        if index < len(recipients) - 1:
            sleep_between_emails()


def process_rule(rule: NotificationRule, now_dt: datetime) -> None:
    """Process one rule if it is due at the configured send time."""
    debug_log(f"Processing rule: {rule.id} ({rule.name})")

    # Check if this is a recurring rule
    if rule.recurrence_type:
        send_time = rule.send_time or datetime.strptime(
            "08:00", "%H:%M").time()
        if now_dt.time() < send_time:
            debug_log(
                f"  └─ SKIPPED: Current time {now_dt.time()} < send_time {send_time}")
            return

        if is_recurring_rule_due(rule, now_dt):
            template = db.session.get(NotificationTemplate, rule.template_id)
            if not template:
                debug_log("  └─ SKIPPED: Template missing")
                return
            process_recurring_rule(rule, template, now_dt)
        else:
            debug_log(f"  └─ SKIPPED: Recurrence not due today")
        return

    # Standard trigger-based rules
    trigger = db.session.get(TriggerType, rule.trigger_type)
    template = db.session.get(NotificationTemplate, rule.template_id)
    if not trigger or not template:
        debug_log("  └─ SKIPPED: Trigger or template missing")
        return

    send_time = rule.send_time or datetime.strptime("08:00", "%H:%M").time()
    if now_dt.time() < send_time:
        debug_log(
            f"  └─ SKIPPED: Current time {now_dt.time()} < send_time {send_time}")
        return

    debug_log(
        f"  └─ Active at {now_dt.time()} >= {send_time}, trigger: {trigger.code}")
    trigger_code = (trigger.code or "").upper()
    # if trigger_code == "EVENT_START":
    #    process_event_start_rule(rule, template, now_dt)
    if trigger_code in ("BIRTHDAY", "MEMBER_ANNIVERSARY"):
        process_member_date_rule(rule, template, now_dt, trigger_code, trigger)
    elif trigger_code == "WORKING_HOURS_MONTHLY":
        process_working_hours_monthly_rule(
            rule, template, now_dt, trigger_code, trigger)
    else:
        process_event_start_rule(rule, template, now_dt, trigger_code, trigger)


def validate_environment() -> None:
    """Validate required SMTP environment values before running the job."""
    if SIMULATE:
        return

    required = {
        "SMTP_HOST": SMTP_HOST,
        "SMTP_USER": SMTP_USER,
        "SMTP_PASSWORD": SMTP_PASSWORD,
        "MAIL_FROM": MAIL_FROM,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}")


def run_service(now_dt: datetime = None) -> None:
    """Run one scheduled notification processing cycle."""
    validate_environment()
    now_dt = now_dt or datetime.now()

    if DEBUG:
        print(f"\n{'='*60}")
        print(f"Mail Service Diagnostic Run: {now_dt}")
        if SIMULATE:
            print("Mode: SIMULATE (no SMTP send, NotificationLog writes enabled)")
        print(f"{'='*60}\n")

    active_rules = NotificationRule.query.filter_by(active=True).all()
    debug_log(f"Found {len(active_rules)} active rule(s)")

    for rule in active_rules:
        process_rule(rule, now_dt)

    if DEBUG:
        print(f"\n{'='*60}")
        print("Diagnostic run complete.")
        print(f"{'='*60}\n")


if __name__ == '__main__':
    cron_app = build_runtime_app()
    with cron_app.app_context():
        print("Mail service is running...")
        if SIMULATE:
            print("SIMULATE mode enabled: no real emails will be sent; logs are saved.")
        run_service()
