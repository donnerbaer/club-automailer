"""Seed demo data focused on placeholder coverage.

This script creates English-language test data for members, events, working
hours, templates, notification rules, and logs so the placeholder contexts in
``mail-service.py`` can be exercised with realistic sample records.
"""

from calendar import monthrange
from datetime import date, datetime, time, timedelta
from textwrap import dedent

from app import create_app, db
from app.model.model import (
    Event,
    EventParticipant,
    Group,
    Member,
    NotificationLog,
    NotificationRule,
    NotificationRuleReceiver,
    NotificationTemplate,
    TriggerType,
    User,
    WorkingHoursLog,
)


EVENT_TEMPLATE_CODE = "DEMO_EVENT_PLACEHOLDER_OVERVIEW"
MEMBER_TEMPLATE_CODE = "DEMO_MEMBER_PLACEHOLDER_OVERVIEW"


def add_months(base_day: date, months: int) -> date:
    """Shift a date by whole months while keeping the day valid."""
    month_index = base_day.month - 1 + months
    year = base_day.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base_day.day, monthrange(year, month)[1])
    return date(year, month, day)


def years_ago(base_day: date, years: int) -> date:
    """Return the same calendar day ``years`` years earlier."""
    try:
        return base_day.replace(year=base_day.year - years)
    except ValueError:
        return base_day.replace(year=base_day.year - years, month=2, day=28)


def ensure_user(username: str, email: str, first_name: str, last_name: str, password: str) -> User:
    """Create or update a user used by the demo data."""
    with db.session.no_autoflush:
        user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username, email=email,
                    first_name=first_name, last_name=last_name)
        user.set_password(password)
        db.session.add(user)
    else:
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
    return user


def ensure_trigger_type(code: str, description: str) -> TriggerType:
    """Create or update a notification trigger type."""
    with db.session.no_autoflush:
        trigger_type = TriggerType.query.filter_by(code=code).first()
    if not trigger_type:
        trigger_type = TriggerType(code=code, description=description)
        db.session.add(trigger_type)
    else:
        trigger_type.description = description
    return trigger_type


def ensure_member(spec: dict) -> Member:
    """Create or update a member from a seed specification."""
    with db.session.no_autoflush:
        member = Member.query.filter_by(
            member_number=spec["member_number"]).first()
    if not member:
        member = Member(member_number=spec["member_number"])
        db.session.add(member)

    member.first_name = spec["first_name"]
    member.last_name = spec["last_name"]
    member.email = spec["email"]
    member.phone = spec.get("phone")
    member.birth_date = spec.get("birth_date")
    member.join_date = spec.get("join_date")
    member.active = spec.get("active", True)
    member.required_hours = spec.get("required_hours", 0)
    return member


def ensure_group(name: str, description: str) -> Group:
    """Create or update a notification group."""
    with db.session.no_autoflush:
        group = Group.query.filter_by(name=name).first()
    if not group:
        group = Group(name=name, description=description)
        db.session.add(group)
    else:
        group.description = description
    return group


def ensure_template(code: str, subject_template: str, body_template: str) -> NotificationTemplate:
    """Create or update a notification template."""
    with db.session.no_autoflush:
        template = NotificationTemplate.query.filter_by(code=code).first()
    if not template:
        template = NotificationTemplate(
            code=code,
            subject_template=subject_template,
            body_template=body_template,
        )
        db.session.add(template)
    else:
        template.subject_template = subject_template
        template.body_template = body_template
    return template


def ensure_rule(name: str, trigger_type: TriggerType, template: NotificationTemplate, days_before: int = 0) -> NotificationRule:
    """Create or update a notification rule."""
    trigger_type_id = trigger_type.id if trigger_type else None
    template_id = template.id if template else None

    with db.session.no_autoflush:
        rule = NotificationRule.query.filter_by(name=name).first()
    if not rule:
        rule = NotificationRule(name=name)
        db.session.add(rule)

    rule.trigger_type = trigger_type_id
    rule.days_before = days_before
    rule.template_id = template_id
    rule.send_time = time(8, 0)
    rule.active = True
    rule.description = f"Demo rule for {name.lower()}"
    return rule


def ensure_rule_receiver(rule: NotificationRule, receiver_type: str, group: Group = None, email: str = None) -> NotificationRuleReceiver:
    """Create or update a rule receiver."""
    lookup = {"rule_id": rule.id, "receiver_type": receiver_type}
    if group is not None:
        lookup["group_id"] = group.id
    if email is not None:
        lookup["custom_email"] = email

    with db.session.no_autoflush:
        receiver = NotificationRuleReceiver.query.filter_by(**lookup).first()
    if not receiver:
        receiver = NotificationRuleReceiver(**lookup)
        db.session.add(receiver)
    return receiver


def ensure_event(title: str, event_type: str, start_at: datetime, end_at: datetime, location: str, created_by: int, description: str = "", is_recurring: bool = False, recurrence_pattern: str = None, recurrence_weekday: int = None, recurrence_count: int = None) -> Event:
    """Create or update an event."""
    with db.session.no_autoflush:
        event = Event.query.filter_by(title=title, start_at=start_at).first()
    if not event:
        event = Event(title=title, start_at=start_at)
        db.session.add(event)

    event.event_type = event_type
    event.description = description
    event.end_at = end_at
    event.location = location
    event.created_by = created_by
    event.is_recurring = is_recurring
    event.recurrence_pattern = recurrence_pattern
    event.recurrence_weekday = recurrence_weekday
    event.recurrence_count = recurrence_count
    return event


def ensure_participant(event: Event, member: Member, status: str = "accepted") -> EventParticipant:
    """Create or update an event participant row."""
    with db.session.no_autoflush:
        participant = EventParticipant.query.filter_by(
            event_id=event.id, member_id=member.id).first()
    if not participant:
        participant = EventParticipant(
            event_id=event.id, member_id=member.id, status=status)
        db.session.add(participant)
    else:
        participant.status = status
    return participant


def ensure_working_hours(member: Member, entry_date: date, hours: float, created_by: int) -> WorkingHoursLog:
    """Create or update a working-hours entry."""
    with db.session.no_autoflush:
        log = WorkingHoursLog.query.filter_by(
            member_id=member.id, date=entry_date, hours=hours).first()
    if not log:
        log = WorkingHoursLog(
            member_id=member.id, date=entry_date, hours=hours, created_by=created_by)
        db.session.add(log)
    else:
        log.created_by = created_by
    return log


def ensure_log(rule: NotificationRule, recipient_email: str, status: str, subject: str, body: str, event: Event = None, member: Member = None, error_message: str = None) -> NotificationLog:
    """Create or update a notification log."""
    lookup = {
        "rule_id": rule.id,
        "recipient_email": recipient_email,
        "status": status,
        "subject": subject,
    }
    if event is not None:
        lookup["event_id"] = event.id
    if member is not None:
        lookup["member_id"] = member.id

    with db.session.no_autoflush:
        log = NotificationLog.query.filter_by(**lookup).first()
    if not log:
        log = NotificationLog(
            rule_id=rule.id,
            recipient_email=recipient_email,
            status=status,
            subject=subject,
            body=body,
            event_id=event.id if event else None,
            event_title=event.title if event else None,
            member_id=member.id if member else None,
            error_message=error_message,
        )
        db.session.add(log)
    else:
        log.body = body
        log.error_message = error_message
    return log


def build_demo_members(today: date) -> list[dict]:
    """Return a mix of birthday, anniversary, and working-hours test members."""
    next_month = add_months(today, 1)
    this_week = today + timedelta(days=3)
    next_week = today + timedelta(days=8)
    tomorrow = today + timedelta(days=1)

    return [
        {
            "member_number": "M-1001",
            "first_name": "Alice",
            "last_name": "Carter",
            "email": "alice.carter@example.org",
            "phone": "+1-555-0101",
            "birth_date": years_ago(today, 40),
            "join_date": years_ago(today, 10),
            "required_hours": 12,
        },
        {
            "member_number": "M-1002",
            "first_name": "Benjamin",
            "last_name": "Reed",
            "email": "benjamin.reed@example.org",
            "phone": "+1-555-0102",
            "birth_date": years_ago(today, 50),
            "join_date": years_ago(today, 25),
            "required_hours": 8,
        },
        {
            "member_number": "M-1003",
            "first_name": "Chloe",
            "last_name": "Morgan",
            "email": "chloe.morgan@example.org",
            "phone": "+1-555-0103",
            "birth_date": years_ago(today, 60),
            "join_date": years_ago(today, 50),
            "required_hours": 6,
        },
        {
            "member_number": "M-1004",
            "first_name": "Daniel",
            "last_name": "Foster",
            "email": "daniel.foster@example.org",
            "phone": "+1-555-0104",
            "birth_date": years_ago(tomorrow, 34),
            "join_date": years_ago(tomorrow, 5),
            "required_hours": 4,
        },
        {
            "member_number": "M-1005",
            "first_name": "Emma",
            "last_name": "Hughes",
            "email": "emma.hughes@example.org",
            "phone": "+1-555-0105",
            "birth_date": years_ago(this_week, 28),
            "join_date": years_ago(this_week, 3),
            "required_hours": 10,
        },
        {
            "member_number": "M-1006",
            "first_name": "Felix",
            "last_name": "Lawson",
            "email": "felix.lawson@example.org",
            "phone": "+1-555-0106",
            "birth_date": years_ago(next_week, 70),
            "join_date": years_ago(next_week, 15),
            "required_hours": 8,
        },
        {
            "member_number": "M-1007",
            "first_name": "Grace",
            "last_name": "Parker",
            "email": "grace.parker@example.org",
            "phone": "+1-555-0107",
            "birth_date": years_ago(next_month, 80),
            "join_date": years_ago(next_month, 12),
            "required_hours": 6,
        },
        {
            "member_number": "M-1008",
            "first_name": "Hannah",
            "last_name": "Scott",
            "email": "hannah.scott@example.org",
            "phone": "+1-555-0108",
            "birth_date": years_ago(tomorrow, 29),
            "join_date": years_ago(today, 2),
            "required_hours": 5,
        },
        {
            "member_number": "M-1009",
            "first_name": "Ian",
            "last_name": "Turner",
            "email": "ian.turner@example.org",
            "phone": "+1-555-0109",
            "birth_date": years_ago(this_week, 45),
            "join_date": years_ago(today, 18),
            "required_hours": 9,
        },
        {
            "member_number": "M-1010",
            "first_name": "Julia",
            "last_name": "Ward",
            "email": "julia.ward@example.org",
            "phone": "+1-555-0110",
            "birth_date": years_ago(next_week, 55),
            "join_date": years_ago(tomorrow, 7),
            "required_hours": 7,
        },
        {
            "member_number": "M-1011",
            "first_name": "Kevin",
            "last_name": "Blake",
            "email": "kevin.blake@example.org",
            "phone": "+1-555-0111",
            "birth_date": years_ago(next_month, 31),
            "join_date": years_ago(next_month, 4),
            "required_hours": 4,
            "active": False,
        },
        {
            "member_number": "M-1012",
            "first_name": "Laura",
            "last_name": "Young",
            "email": "laura.young@example.org",
            "phone": "+1-555-0112",
            "birth_date": years_ago(today, 90),
            "join_date": years_ago(today, 100),
            "required_hours": 3,
        },
        {
            "member_number": "M-1013",
            "first_name": "Mason",
            "last_name": "Stone",
            "email": "mason.stone@example.org",
            "phone": "+1-555-0113",
            "birth_date": years_ago(today, 100),
            "join_date": years_ago(today, 50),
            "required_hours": 2,
        },
        {
            "member_number": "M-1014",
            "first_name": "Natalie",
            "last_name": "Cole",
            "email": "natalie.cole@example.org",
            "phone": "+1-555-0114",
            "birth_date": years_ago(today, 33),
            "join_date": years_ago(today, 75),
            "required_hours": 12,
        },
        {
            "member_number": "M-1015",
            "first_name": "Oliver",
            "last_name": "Brooks",
            "email": "oliver.brooks@example.org",
            "phone": "+1-555-0115",
            "birth_date": years_ago(today, 41),
            "join_date": years_ago(today, 100),
            "required_hours": 11,
        },
        {
            "member_number": "M-1016",
            "first_name": "Paige",
            "last_name": "Harris",
            "email": "paige.harris@example.org",
            "phone": "+1-555-0116",
            "birth_date": years_ago(today, 27),
            "join_date": years_ago(today, 30),
            "required_hours": 0,
            "active": True,
        },
        {
            "member_number": "M-1017",
            "first_name": "Quentin",
            "last_name": "Adams",
            "email": "quentin.adams@example.org",
            "phone": "+1-555-0117",
            "birth_date": years_ago(today, 70),
            "join_date": years_ago(today, 25),
            "required_hours": 1,
        },
    ]


def build_demo_event_templates() -> tuple[str, str]:
    """Return subject/body templates that exercise event placeholders."""
    subject = "[Demo Event] {{trigger.name}} | {{event.title}} | {{current.date}}"
    body = dedent(
        """
        Hello {{recipient.fullname}},

        This is the demo event digest for {{event.title}}.

        Recipient
        - First name: {{recipient.first_name}}
        - Last name: {{recipient.last_name}}
        - Full name: {{recipient.fullname}}
        - Email: {{recipient.email}}
        - Phone: {{recipient.phone}}
        - Member number: {{recipient.member_number}}
        - Birth date: {{recipient.birth_date}}
        - Join date: {{recipient.join_date}}
        - Age: {{recipient.age}}

        Trigger
        - Name: {{trigger.name}}
        - Description: {{trigger.description}}
        - Code: {{trigger.code}}
        - Days before: {{trigger.days_before}}

        Event
        - Title: {{event.title}}
        - Description: {{event.description}}
        - Location: {{event.location}}
        - Start at: {{event.start_at}}
        - End at: {{event.end_at}}
        - Start date: {{event.start_date}}
        - Start time: {{event.start_time}}
        - End date: {{event.end_date}}
        - End time: {{event.end_time}}
        - Duration hours: {{event.duration_hours}}
        - Participants count: {{event.participants_count}}
        - Participant names: {{event_participants_names}}
        - Participant emails: {{event_participants_emails}}
        - Calendar Google link: {{event_calendar_google}}
        - Calendar Outlook link: {{event_calendar_outlook}}

        Participants
        {% for participant in event.participants %}
        - {{participant.name}} ({{participant.email}})
        {% endfor %}

        Current date
        - Date: {{current.date}}
        - Time: {{current.time}}
        - Month: {{current.month}} / {{current.month_number}}
        - Year: {{current.year}}
        - Previous month: {{previous.month}} / {{previous.month_number}}
        - Next month: {{next.month}} / {{next.month_number}}

        Global hours
        - Total: {{hours.total}}
        - This year: {{hours.this_year}}
        - This month: {{hours.this_month}}
        - Last month: {{hours.last_month}}

        Participant statistics
        - Total members: {{participants.total.count}}
        - Active members: {{participants.active.count}}
        - Worked this month: {{participants.worked.this_month.count}}
        - Worked last month: {{participants.worked.last_month.count}}
        - Worked this year: {{participants.worked.this_year.count}}

        Birthdays
        - Today: {{birthdays.count.today}}
        - This week: {{birthdays.count.this_week}}
        - Current month: {{birthdays.count.current_month}}
        {% for person in birthdays_today %}
        - Today birthday: {{person.first_name}} {{person.last_name}} ({{person.birth_date}})
        {% endfor %}
        {% for person in birthdays_tomorrow %}
        - Tomorrow birthday: {{person.first_name}} {{person.last_name}} ({{person.birth_date}})
        {% endfor %}
        {% for person in birthdays_this_week %}
        - This week birthday: {{person.first_name}} {{person.last_name}} ({{person.birth_date}})
        {% endfor %}
        {% for person in birthdays_next_week %}
        - Next week birthday: {{person.first_name}} {{person.last_name}} ({{person.birth_date}})
        {% endfor %}
        {% for person in birthdays_current_month %}
        - Current month birthday: {{person.first_name}} {{person.last_name}} ({{person.birth_date}})
        {% endfor %}
        {% for person in birthdays_next_month %}
        - Next month birthday: {{person.first_name}} {{person.last_name}} ({{person.birth_date}})
        {% endfor %}

        Membership anniversaries
        - Current month: {{membership.anniversaries.count.current_month}}
        - Next month: {{membership.anniversaries.count.next_month}}
        {% for person in membership_anniversaries_current_month %}
        - Current month anniversary: {{person.first_name}} {{person.last_name}} ({{person.join_date}})
        {% endfor %}
        {% for person in membership_anniversaries_next_month %}
        - Next month anniversary: {{person.first_name}} {{person.last_name}} ({{person.join_date}})
        {% endfor %}

        Upcoming birthdays
        {% for person in upcoming_birthdays.current.today %}
        - Today: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays.current.this_week %}
        - This week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays.next.tomorrow %}
        - Tomorrow: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays.next.week %}
        - Next week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays.next.month %}
        - Next month: {{person.first_name}} {{person.last_name}}
        {% endfor %}

        Upcoming anniversaries
        {% for person in upcoming_anniversaries.current.today %}
        - Today: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries.current.this_week %}
        - This week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries.next.tomorrow %}
        - Tomorrow: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries.next.week %}
        - Next week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries.next.month %}
        - Next month: {{person.first_name}} {{person.last_name}}
        {% endfor %}

        Upcoming events
        {% for item in upcoming_events.current.today %}
        - Today: {{item.title}} on {{item.start_at}}
        {% endfor %}
        {% for item in upcoming_events.current.this_week %}
        - This week: {{item.title}} on {{item.start_at}}
        {% endfor %}
        {% for item in upcoming_events.next.tomorrow %}
        - Tomorrow: {{item.title}} on {{item.start_at}}
        {% endfor %}
        {% for item in upcoming_events.next.week %}
        - Next week: {{item.title}} on {{item.start_at}}
        {% endfor %}
        {% for item in upcoming_events.next.month %}
        - Next month: {{item.title}} on {{item.start_at}}
        {% endfor %}
        """
    ).strip()
    return subject, body


def build_demo_member_templates() -> tuple[str, str]:
    """Return subject/body templates that exercise member placeholders."""
    subject = "[Demo Member] {{trigger.name}} | {{subject.fullname}} | {{current.date}}"
    body = dedent(
        """
        Hello {{recipient.fullname}},

        This demo template focuses on member, subject, and anniversary placeholders.

        Recipient
        - First name: {{recipient.first_name}}
        - Last name: {{recipient.last_name}}
        - Full name: {{recipient.fullname}}
        - Email: {{recipient.email}}
        - Phone: {{recipient.phone}}
        - Member number: {{recipient.member_number}}
        - Birth date: {{recipient.birth_date}}
        - Join date: {{recipient.join_date}}
        - Age: {{recipient.age}}

        Member
        - First name: {{member.first_name}}
        - Last name: {{member.last_name}}
        - Full name: {{member.fullname}}
        - Email: {{member.email}}
        - Phone: {{member.phone}}
        - Member number: {{member.member_number}}
        - Birth date: {{member.birth_date}}
        - Join date: {{member.join_date}}
        - Age: {{member.age}}
        - Required hours: {{member.required_hours}}
        - All hours: {{member.all_hours}}
        - This year hours: {{member.hours.this_year}}
        - Today hours: {{member.hours.today}}
        - Yesterday hours: {{member.hours.yesterday}}
        - This week hours: {{member.hours.this_week}}
        - Last week hours: {{member.hours.last_week}}
        - This month hours: {{member.hours.this_month}}
        - Last month hours: {{member.hours.last_month}}
        - Last year hours: {{member.hours.last_year}}
        - Membership duration: {{member.membership_duration}}
        - Active: {{member.active}}

        Subject
        - First name: {{subject.first_name}}
        - Last name: {{subject.last_name}}
        - Full name: {{subject.fullname}}
        - Email: {{subject.email}}
        - Phone: {{subject.phone}}
        - Member number: {{subject.member_number}}
        - Birth date: {{subject.birth_date}}
        - Join date: {{subject.join_date}}
        - Age: {{subject.age}}
        - Required hours: {{subject.required_hours}}
        - All hours: {{subject.all_hours}}
        - Membership duration: {{subject.membership_duration}}
        - Active: {{subject.active}}

        Deprecated anniversary placeholders
        - First name: {{anniversary.firstname}}
        - Last name: {{anniversary.lastname}}
        - Full name: {{anniversary.fullname}}
        - Years: {{anniversary.years}}
        - Member since: {{anniversary.member_since}}

        Trigger
        - Name: {{trigger.name}}
        - Description: {{trigger.description}}
        - Code: {{trigger.code}}
        - Days before: {{trigger.days_before}}

        Current date
        - Date: {{current.date}}
        - Time: {{current.time}}
        - Month: {{current.month}} / {{current.month_number}}
        - Year: {{current.year}}

        Global hours
        - Total: {{hours.total}}
        - This year: {{hours.this_year}}
        - This month: {{hours.this_month}}
        - Last month: {{hours.last_month}}

        Participant statistics
        - Total members: {{participants.total.count}}
        - Active members: {{participants.active.count}}
        - Worked this month: {{participants.worked.this_month.count}}
        - Worked last month: {{participants.worked.last_month.count}}
        - Worked this year: {{participants.worked.this_year.count}}

        Members with hours
        - This week: {{members.with_hours.current.week|length}}
        - This month: {{members.with_hours.current.month|length}}
        - This year: {{members.with_hours.current.year|length}}
        - Last week: {{members.with_hours.last.week|length}}
        - Last month: {{members.with_hours.last.month|length}}
        - Last year: {{members.with_hours.last.year|length}}
        {% for person in members_with_hours_this_week %}
        - Hours this week: {{person.first_name}} {{person.last_name}}
        {% endfor %}

        Members without hours
        - This week: {{members.without_hours.current.week|length}}
        - This month: {{members.without_hours.current.month|length}}
        - This year: {{members.without_hours.current.year|length}}
        - Last week: {{members.without_hours.last.week|length}}
        - Last month: {{members.without_hours.last.month|length}}
        - Last year: {{members.without_hours.last.year|length}}
        {% for person in members_without_hours_this_week %}
        - No hours this week: {{person.first_name}} {{person.last_name}}
        {% endfor %}

        Members with birthdays in the current month
        {% for person in members.birthday.current_month %}
        - {{person.first_name}} {{person.last_name}} ({{person.birth_date}})
        {% endfor %}

        Birthday milestones
        {% for person in birthdays_milestone_40 %}
        - 40 years old: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in birthdays_milestone_50 %}
        - 50 years old: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in birthdays_milestone_60 %}
        - 60 years old: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in birthdays_milestone_70 %}
        - 70 years old: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in birthdays_milestone_80 %}
        - 80 years old: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in birthdays_milestone_90 %}
        - 90 years old: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in birthdays_milestone_100 %}
        - 100 years old: {{person.first_name}} {{person.last_name}}
        {% endfor %}

        Membership milestones
        {% for person in membership_anniversaries_milestone_10 %}
        - 10 years: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in membership_anniversaries_milestone_25 %}
        - 25 years: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in membership_anniversaries_milestone_50 %}
        - 50 years: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in membership_anniversaries_milestone_75 %}
        - 75 years: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in membership_anniversaries_milestone_100 %}
        - 100 years: {{person.first_name}} {{person.last_name}}
        {% endfor %}

        Upcoming birthdays
        {% for person in upcoming_birthdays_today %}
        - Today: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays_tomorrow %}
        - Tomorrow: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays_this_week %}
        - This week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays_next_week %}
        - Next week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_birthdays_next_month %}
        - Next month: {{person.first_name}} {{person.last_name}}
        {% endfor %}

        Upcoming anniversaries
        {% for person in upcoming_anniversaries_today %}
        - Today: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries_tomorrow %}
        - Tomorrow: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries_this_week %}
        - This week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries_next_week %}
        - Next week: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        {% for person in upcoming_anniversaries_next_month %}
        - Next month: {{person.first_name}} {{person.last_name}}
        {% endfor %}
        """
    ).strip()
    return subject, body


def seed_demo_data() -> None:
    """Populate the database with demo records."""
    today = date.today()

    admin_user = ensure_user(
        username="admin",
        email="admin@example.org",
        first_name="Admin",
        last_name="User",
        password="Starten1!",
    )
    demo_user = ensure_user(
        username="demo.editor",
        email="demo.editor@example.org",
        first_name="Demo",
        last_name="Editor",
        password="DemoEditor123!",
    )

    trigger_default = ensure_trigger_type("DEFAULT", "Default")
    trigger_birthday = ensure_trigger_type("BIRTHDAY", "Member Birthday")
    trigger_anniversary = ensure_trigger_type(
        "MEMBER_ANNIVERSARY", "Member Anniversary")
    trigger_hours = ensure_trigger_type(
        "WORKING_HOURS_MONTHLY", "Monthly working hours report")
    db.session.flush()

    north_team = ensure_group(
        "North Team", "Demo notification group for the northern region")
    south_team = ensure_group(
        "South Team", "Demo notification group for the southern region")

    members = [ensure_member(spec) for spec in build_demo_members(today)]
    db.session.flush()

    for index, member in enumerate(members):
        target_group = north_team if index % 2 == 0 else south_team
        if member not in target_group.members:
            target_group.members.append(member)

    db.session.commit()

    event_subject, event_body = build_demo_event_templates()
    member_subject, member_body = build_demo_member_templates()

    event_template = ensure_template(
        EVENT_TEMPLATE_CODE, event_subject, event_body)
    member_template = ensure_template(
        MEMBER_TEMPLATE_CODE, member_subject, member_body)
    db.session.commit()
    db.session.flush()

    event_start = datetime.combine(today + timedelta(days=1), time(18, 30))
    event_end = event_start + timedelta(hours=2, minutes=15)
    event_followup_start = datetime.combine(add_months(today, 1), time(19, 0))
    event_followup_end = event_followup_start + timedelta(hours=1, minutes=30)

    kickoff_event = ensure_event(
        title="Demo Kickoff Session",
        event_type="DEFAULT",
        start_at=event_start,
        end_at=event_end,
        location="Community Hall",
        created_by=admin_user.id,
        description="An English-language demo event that exercises the placeholder context.",
        is_recurring=False,
    )
    followup_event = ensure_event(
        title="Demo Monthly Review",
        event_type="DEFAULT",
        start_at=event_followup_start,
        end_at=event_followup_end,
        location="Conference Room B",
        created_by=demo_user.id,
        description="A second demo event scheduled for next month.",
        is_recurring=True,
        recurrence_pattern="MONTHLY",
        recurrence_count=6,
    )
    db.session.flush()

    for member in (members[0], members[1], members[3], members[4], members[8]):
        ensure_participant(kickoff_event, member)
    for member in (members[2], members[5], members[6], members[12], members[14]):
        ensure_participant(followup_event, member)

    db.session.commit()

    current_week_hours = [
        (members[0], today, 6.0),
        (members[0], today - timedelta(days=1), 2.0),
        (members[1], today - timedelta(days=today.weekday()), 4.5),
        (members[2], today - timedelta(days=8), 5.0),
        (members[3], today - timedelta(days=2), 3.0),
        (members[4], add_months(today, -1), 7.5),
        (members[5], date(today.year - 1, today.month, min(today.day,
         monthrange(today.year - 1, today.month)[1])), 8.0),
        (members[6], today - timedelta(days=14), 1.0),
        (members[7], today, 4.0),
        (members[8], today - timedelta(days=3), 6.5),
        (members[9], add_months(today, -1), 2.5),
    ]
    for member, entry_date, hours in current_week_hours:
        ensure_working_hours(member, entry_date, hours, admin_user.id)
    db.session.commit()

    event_subject_text = "[Demo Event] Demo Kickoff Session | placeholder coverage"
    event_body_text = "Demo event log entry used to validate the notification log view."
    member_subject_text = "[Demo Member] Placeholder coverage for demo members"
    member_body_text = "Demo member log entry used to validate the notification log view."

    event_rule = ensure_rule("Demo Event Reminder",
                             trigger_default, event_template, days_before=1)
    birthday_rule = ensure_rule(
        "Demo Birthday Reminder", trigger_birthday, member_template, days_before=0)
    anniversary_rule = ensure_rule(
        "Demo Anniversary Reminder", trigger_anniversary, member_template, days_before=0)
    hours_rule = ensure_rule("Demo Working Hours Report",
                             trigger_hours, member_template, days_before=0)
    db.session.flush()

    ensure_rule_receiver(event_rule, "group", group=north_team)
    ensure_rule_receiver(event_rule, "email", email="events@example.org")
    ensure_rule_receiver(birthday_rule, "group", group=south_team)
    ensure_rule_receiver(anniversary_rule, "email",
                         email="anniversaries@example.org")
    ensure_rule_receiver(hours_rule, "group", group=north_team)
    db.session.commit()

    ensure_log(
        event_rule,
        recipient_email="alice.carter@example.org",
        status="SENT",
        subject=event_subject_text,
        body=event_body_text,
        event=kickoff_event,
        member=members[0],
    )
    ensure_log(
        birthday_rule,
        recipient_email="benjamin.reed@example.org",
        status="PENDING",
        subject=member_subject_text,
        body=member_body_text,
        member=members[1],
    )
    ensure_log(
        anniversary_rule,
        recipient_email="natalie.cole@example.org",
        status="FAILED",
        subject=member_subject_text,
        body=member_body_text,
        member=members[13],
        error_message="SMTP connection timed out in demo mode.",
    )
    ensure_log(
        hours_rule,
        recipient_email="demo.editor@example.org",
        status="SENT",
        subject=member_subject_text,
        body=member_body_text,
        member=members[15],
    )
    db.session.commit()


def main() -> None:
    """Run the seed inside a Flask application context."""
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_demo_data()
        print("Demo placeholder seed data created successfully.")


if __name__ == "__main__":
    main()
