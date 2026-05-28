"""Scheduled mail service for automated notification delivery.

This script is intended to be executed by cron. It reads active notification
rules from the same database used by the Flask web application, resolves due
targets (events or members), sends emails, and writes audit logs.

Usage:
  python mail-service.py          # Normal cron mode (silent unless errors)
  python mail-service.py --debug  # Verbose diagnostic output
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
from jinja2 import Undefined
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
FORCE_WORKING_HOURS_MONTHLY = (
    "--force-working-hours-monthly" in sys.argv
    or os.getenv("FORCE_WORKING_HOURS_MONTHLY", "") == "1"
)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
TEMPLATE_ENV = SandboxedEnvironment(autoescape=False, undefined=Undefined)


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
    time.sleep(random.randint(1, 10))


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
        except (SecurityError, TemplateSyntaxError, UndefinedError):
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
    birth_date = member.birth_date if member else None
    join_date = member.join_date if member else None

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": resolved_email,
        "member_number": member_number,
        "birth_date": birth_date,
        "_birth_date": format_template_value(birth_date),
        "join_date": join_date,
        "_join_date": format_template_value(join_date),
        "active": member.active if member else False,
    }


def build_named_template_context(name: str, person_context: dict) -> dict:
    """Expose a person context both nested and as flat aliases."""
    return {
        name: person_context,
        f"{name}_first_name": person_context["first_name"],
        f"{name}_last_name": person_context["last_name"],
        f"{name}_email": person_context["email"],
        f"{name}_member_number": person_context["member_number"],
        f"{name}_birth_date": person_context["birth_date"],
        f"{name}_join_date": person_context["join_date"],
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
    current_year = date.today().year
    for log in getattr(member, "working_hours_logs", []) or []:
        try:
            h = float(getattr(log, "hours", 0) or 0)
        except Exception:
            h = 0.0
        all_hours += h
        if getattr(log, "date", None) and getattr(log, "date").year == current_year:
            hours_this_year += h

    # Add aggregated fields to the nested person context
    person_ctx.update(
        {
            "required_hours": required_hours,
            "all_hours": all_hours,
            "hours_this_year": hours_this_year,
        }
    )

    # Build named context and also expose flat aliases for the new fields
    ctx = build_named_template_context("member", person_ctx)
    ctx.update(
        {
            "member_required_hours": required_hours,
            "member_all_hours": all_hours,
            "member_hours_this_year": hours_this_year,
        }
    )

    return ctx


def build_receiver_template_context(recipient_email: str, receiver_member: Member = None) -> dict:
    """Build a nested and flat template context for the email receiver."""
    return build_named_template_context(
        "receiver",
        build_person_template_context(receiver_member, email=recipient_email),
    )


def build_event_template_context(event: Event, days_before: int) -> dict:
    """Build a nested and flat template context for an event."""
    event_context = {
        "title": event.title,
        "description": event.description or "",
        "start_at": format_template_value(event.start_at),
        "end_at": format_template_value(event.end_at),
        "start_date": format_template_value(event.start_at),
        "end_date": format_template_value(event.end_at),
        "location": event.location or "",
    }

    # Generate calendar import links
    calendar_links = {
        "google": generate_google_calendar_link(event),
        "outlook": generate_outlook_calendar_link(event),
    }

    return {
        "event": event_context,
        "event_title": event_context["title"],
        "event_description": event_context["description"],
        "event_start": event_context["start_at"],
        "event_end": event_context["end_at"],
        "event_start_date": event_context["start_date"],
        "event_end_date": event_context["end_date"],
        "event_location": event_context["location"],
        "days_before": days_before,
        "calendar_links": calendar_links,
        "event_calendar_google": calendar_links["google"],
        "event_calendar_outlook": calendar_links["outlook"],
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
            context.update(build_event_template_context(
                event, rule.days_before or 0))
            # Global working hours placeholders
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
            context.update(
                {
                    "all_working_hours": float(total_hours),
                    "all_working_hours_this_year": float(total_hours_year),
                }
            )
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
            context.update(build_member_template_context(member))
            # Global working hours placeholders
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
            context.update(
                {
                    "all_working_hours": float(total_hours),
                    "all_working_hours_this_year": float(total_hours_year),
                }
            )
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
        context.update(build_member_template_context(member))
        context.update(
            {
                "all_working_hours": float(total_hours),
                "all_working_hours_this_year": float(total_hours_year),
            }
        )

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


def process_rule(rule: NotificationRule, now_dt: datetime) -> None:
    """Process one rule if it is due at the configured send time."""
    debug_log(f"Processing rule: {rule.id} ({rule.name})")

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
        process_member_date_rule(rule, template, now_dt, trigger_code)
    elif trigger_code == "WORKING_HOURS_MONTHLY":
        process_working_hours_monthly_rule(
            rule, template, now_dt, trigger_code)
    else:
        process_event_start_rule(rule, template, now_dt, trigger_code)


def validate_environment() -> None:
    """Validate required SMTP environment values before running the job."""
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
        run_service()
