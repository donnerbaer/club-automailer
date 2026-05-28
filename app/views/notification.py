""" This module handles the main views of the application, including the index, dashboard, and error pages."""

import csv
import io
from collections import defaultdict
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, request, Response, flash
from flask_babel import gettext as _
from flask_login import login_required, current_user
from jinja2 import Undefined
from jinja2.exceptions import SecurityError, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import func, or_, extract, case, and_

from app import db
from app.forms import (
    AuthGroupCreateForm,
    AuthGroupUpdateForm,
    EventForm,
    EventCleanupForm,
    NotificationEventParticipantForm,
    NotificationRuleForm,
    NotificationRuleReceiverForm,
    NotificationTemplateForm,
    TriggerTypeForm,
    MemberForm,
    WorkingHoursForm,
    WorkingHoursImportForm,
    NotificationMemberGroupForm,
    NotificationGroupMembershipForm,
    NotificationLogClearForm,
    ICSImportForm,
    MemberImportForm,
    EventImportForm,
)
from app.model.model import (
    Event,
    EventParticipant,
    Group,
    Member,
    WorkingHoursLog,
    NotificationLog,
    NotificationRule,
    NotificationRuleReceiver,
    NotificationTemplate,
    TriggerType,
)
from icalendar import Calendar
import re
from app.utils.decorators import check_permissions


notification_bp = Blueprint(
    'notification',
    __name__,
    url_prefix='/notification',
    template_folder='templates/notification'
)

EVENT_TITLE_ENV = SandboxedEnvironment(autoescape=False, undefined=Undefined)


def _add_months(base_date, month_count):
    """Return a datetime shifted forward by a number of calendar months."""
    month_index = base_date.month - 1 + month_count
    year = base_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return base_date.replace(year=year, month=month, day=day)


def _build_recurrence_start(base_start, recurrence_pattern, occurrence_index):
    """Calculate the start datetime for a recurring occurrence."""
    if recurrence_pattern == 'DAILY':
        return base_start + timedelta(days=occurrence_index)
    if recurrence_pattern == 'MONTHLY':
        return _add_months(base_start, occurrence_index)
    return base_start + timedelta(weeks=occurrence_index)


def _format_event_title_value(value):
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.isoformat(sep=' ')
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


def _build_event_title_context(event):
    return {
        'event': {
            'description': event.description or '',
            'start_at': _format_event_title_value(event.start_at),
            'end_at': _format_event_title_value(event.end_at),
            'start_date': _format_event_title_value(event.start_at),
            'end_date': _format_event_title_value(event.end_at),
            'location': event.location or '',
        },
        'event_title': event.title,
        'event_description': event.description or '',
        'event_start': _format_event_title_value(event.start_at),
        'event_end': _format_event_title_value(event.end_at),
        'event_start_date': _format_event_title_value(event.start_at),
        'event_end_date': _format_event_title_value(event.end_at),
        'event_location': event.location or '',
    }


def _render_event_title(event):
    title_template = event.title or ''
    if '{{' not in title_template and '{%' not in title_template:
        return title_template

    try:
        return EVENT_TITLE_ENV.from_string(title_template).render(
            _build_event_title_context(event)
        )
    except (SecurityError, TemplateSyntaxError, UndefinedError):
        return title_template


def _attach_rendered_event_title(event):
    event.rendered_title = _render_event_title(event)
    return event


def _parse_member_import_date(value):
    if value is None:
        return None

    value = str(value).strip()
    if not value:
        return None

    for date_format in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _parse_member_import_required_hours(value):
    if value is None:
        return None

    value = str(value).strip()
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def _parse_member_import_status(value):
    if value is None:
        return True

    normalized_value = str(value).strip().lower()
    if not normalized_value:
        return True

    if normalized_value in {'1', 'true', 'yes', 'y', 'active', 'enabled', 'on'}:
        return True
    if normalized_value in {'0', 'false', 'no', 'n', 'inactive', 'disabled', 'off'}:
        return False
    return True


def _normalize_csv_header(value):
    return str(value).strip().lower().replace(' ', '_') if value is not None else ''


def _normalize_csv_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def _parse_event_import_datetime(value):
    """Parse a datetime value with multiple format support."""
    if value is None:
        return None

    value = str(value).strip()
    if not value:
        return None

    # Try common formats
    for date_format in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S',
                        '%d.%m.%Y %H:%M', '%d.%m.%Y %H:%M:%S',
                        '%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S',
                        '%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M:%S'):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    # Try ISO format
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_event_import_participants(value):
    """Parse participant member numbers from a separated string."""
    if value is None:
        return []

    value = str(value).strip()
    if not value:
        return []

    participant_values = []
    for item in re.split(r'[\s,;|]+', value):
        item = item.strip()
        if item:
            participant_values.append(item)

    return participant_values


def _decode_event_import_data(uploaded_file):
    """Decode uploaded event import text with common spreadsheet encodings."""
    raw_bytes = uploaded_file.read()
    for encoding in ('utf-8-sig', 'utf-16', 'cp1252', 'latin-1', 'utf-8'):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError('utf-8', raw_bytes, 0, 1,
                             'Unable to decode uploaded event import file')


def _build_event_import_template_csv():
    """Build a template CSV for event import."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    writer.writerow([
        'title',
        'description',
        'start_at',
        'end_at',
        'location',
        'participants',
    ])
    writer.writerow([
        "Mother's day",
        'Beschreibung..',
        '2027-05-01 11:00:00',
        '2027-05-01 16:00:00',
        'Clubhouse',
        '311,312,411',
    ])
    return output.getvalue()


def _build_member_import_template_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'member_number',
        'first_name',
        'last_name',
        'birth_date',
        'email',
        'phone',
        'member_since',
        'required_hours',
        'status',
    ])
    return output.getvalue()


def _build_working_hours_import_template_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'member_number',
        'date',
        'hours',
    ])
    return output.getvalue()


def _build_copied_rule_name(source_name):
    base_name = f'{source_name} (Copy)'
    max_length = 255
    candidate = base_name[:max_length]
    suffix = 2

    while NotificationRule.query.filter_by(name=candidate).first() is not None:
        suffix_text = f' (Copy {suffix})'
        prefix_length = max_length - len(suffix_text)
        candidate = f'{source_name[:prefix_length]}{suffix_text}'
        suffix += 1

    return candidate


@notification_bp.route('/manuel', methods=['GET'])
@login_required
def show_manuel():
    """ Show the manual page with instructions on how to use the club automailer."""
    return render_template('notification/site.manuel.html')


@notification_bp.route('/')
@login_required
@check_permissions(['notification.view'])
def index():
    return render_template('notification/site.index.html')


@notification_bp.route('/dashboard')
@login_required
@check_permissions(['notification.view'])
def dashboard():
    """Dashboard showing notification statistics with charts."""

    # Gather statistics
    total_members = Member.query.count()
    total_events = Event.query.count()
    total_rules = NotificationRule.query.count()
    active_rules = NotificationRule.query.filter_by(active=True).count()

    # Log statistics by status
    total_logs = NotificationLog.query.count()
    sent_logs = NotificationLog.query.filter_by(status='SENT').count()
    failed_logs = NotificationLog.query.filter_by(status='FAILED').count()
    pending_logs = NotificationLog.query.filter_by(status='PENDING').count()

    # Logs by trigger type
    logs_by_trigger = db.session.query(
        TriggerType.code,
        func.count(NotificationLog.id).label('count')
    ).join(
        NotificationRule, NotificationLog.rule_id == NotificationRule.id
    ).join(
        TriggerType, NotificationRule.trigger_type == TriggerType.id
    ).group_by(TriggerType.code).all()

    # Recent logs trend (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    logs_trend = db.session.query(
        func.date(NotificationLog.sent_at).label('date'),
        func.count(NotificationLog.id).label('count')
    ).filter(
        NotificationLog.sent_at >= seven_days_ago
    ).group_by(
        func.date(NotificationLog.sent_at)
    ).order_by('date').all()

    # Groups and members relationship
    total_groups = Group.query.count()

    return render_template(
        'notification/site.dashboard.html',
        total_members=total_members,
        total_events=total_events,
        total_rules=total_rules,
        active_rules=active_rules,
        total_groups=total_groups,
        total_logs=total_logs,
        sent_logs=sent_logs,
        failed_logs=failed_logs,
        pending_logs=pending_logs,
        logs_by_trigger=logs_by_trigger,
        logs_trend=logs_trend,
    )


@notification_bp.route('/templates')
@login_required
@check_permissions(['notification.templates.view'])
def templates_view():
    templates = NotificationTemplate.query.order_by(
        NotificationTemplate.code.asc()).all()
    template_form = NotificationTemplateForm()
    return render_template('notification/site.templates.html', templates=templates, template_form=template_form)


@notification_bp.route('/templates', methods=['POST'])
@login_required
@check_permissions(['notification.template.create'])
def template_post():
    template_form = NotificationTemplateForm()
    if template_form.validate_on_submit():
        duplicate_code = NotificationTemplate.query.filter_by(
            code=template_form.code.data).first()
        if duplicate_code is None:
            template = NotificationTemplate(
                code=template_form.code.data,
                subject_template=template_form.subject_template.data,
                body_template=template_form.body_template.data,
            )
            db.session.add(template)
            db.session.commit()
            return redirect(url_for('notification.template_detail', template_id=template.id))
        template_form.code.errors.append(_('Template code already exists.'))

    templates = NotificationTemplate.query.order_by(
        NotificationTemplate.code.asc()).all()
    return render_template('notification/site.templates.html', templates=templates, template_form=template_form)


@notification_bp.route('/templates/<int:template_id>')
@login_required
@check_permissions(['notification.template.read'])
def template_detail(template_id):
    template = NotificationTemplate.query.get_or_404(template_id)
    template_update_form = NotificationTemplateForm(obj=template)
    return render_template(
        'notification/site.template.html',
        template=template,
        template_update_form=template_update_form,
    )


@notification_bp.route('/templates/<int:template_id>/update', methods=['POST'])
@login_required
@check_permissions(['notification.template.update'])
def template_update(template_id):
    template = NotificationTemplate.query.get_or_404(template_id)
    template_update_form = NotificationTemplateForm()

    if template_update_form.validate_on_submit():
        duplicate_code = NotificationTemplate.query.filter(
            NotificationTemplate.id != template.id,
            NotificationTemplate.code == template_update_form.code.data,
        ).first()
        if duplicate_code is None:
            template.code = template_update_form.code.data
            template.subject_template = template_update_form.subject_template.data
            template.body_template = template_update_form.body_template.data
            db.session.add(template)
            db.session.commit()
            return redirect(url_for('notification.template_detail', template_id=template.id))
        template_update_form.code.errors.append(
            _('Template code already exists.'))

    return render_template(
        'notification/site.template.html',
        template=template,
        template_update_form=template_update_form,
    )


@notification_bp.route('/templates/<int:template_id>/delete', methods=['GET'])
@login_required
@check_permissions(['notification.template.delete'])
def template_delete(template_id):
    template = NotificationTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for('notification.templates_view'))


@notification_bp.route('/trigger-types')
@login_required
@check_permissions(['notification.rules.view'])
def trigger_types_view():
    trigger_types = TriggerType.query.order_by(TriggerType.code.asc()).all()
    trigger_type_form = TriggerTypeForm()
    return render_template('notification/site.trigger_types.html', trigger_types=trigger_types, trigger_type_form=trigger_type_form)


@notification_bp.route('/trigger-types', methods=['POST'])
@login_required
@check_permissions(['notification.rule.create'])
def trigger_type_post():
    trigger_type_form = TriggerTypeForm()
    if trigger_type_form.validate_on_submit():
        duplicate_code = TriggerType.query.filter_by(
            code=trigger_type_form.code.data).first()
        if duplicate_code is None:
            trigger_type = TriggerType(
                code=trigger_type_form.code.data,
                description=trigger_type_form.description.data or None,
            )
            db.session.add(trigger_type)
            db.session.commit()
            return redirect(url_for('notification.trigger_type_detail', trigger_type_id=trigger_type.id))
        trigger_type_form.code.errors.append(
            _('Trigger type code already exists.'))

    trigger_types = TriggerType.query.order_by(TriggerType.code.asc()).all()
    return render_template('notification/site.trigger_types.html', trigger_types=trigger_types, trigger_type_form=trigger_type_form)


@notification_bp.route('/trigger-types/<int:trigger_type_id>')
@login_required
@check_permissions(['notification.rule.read'])
def trigger_type_detail(trigger_type_id):
    trigger_type = TriggerType.query.get_or_404(trigger_type_id)
    trigger_type_update_form = TriggerTypeForm(obj=trigger_type)
    return render_template(
        'notification/site.trigger_type.html',
        trigger_type=trigger_type,
        trigger_type_update_form=trigger_type_update_form,
    )


@notification_bp.route('/trigger-types/<int:trigger_type_id>/update', methods=['POST'])
@login_required
@check_permissions(['notification.rule.update'])
def trigger_type_update(trigger_type_id):
    trigger_type = TriggerType.query.get_or_404(trigger_type_id)
    trigger_type_update_form = TriggerTypeForm()

    if trigger_type_update_form.validate_on_submit():
        duplicate_code = TriggerType.query.filter(
            TriggerType.id != trigger_type.id,
            TriggerType.code == trigger_type_update_form.code.data,
        ).first()
        if duplicate_code is None:
            trigger_type.code = trigger_type_update_form.code.data
            trigger_type.description = trigger_type_update_form.description.data or None
            db.session.add(trigger_type)
            db.session.commit()
            return redirect(url_for('notification.trigger_type_detail', trigger_type_id=trigger_type.id))
        trigger_type_update_form.code.errors.append(
            _('Trigger type code already exists.'))

    return render_template(
        'notification/site.trigger_type.html',
        trigger_type=trigger_type,
        trigger_type_update_form=trigger_type_update_form,
    )


@notification_bp.route('/trigger-types/<int:trigger_type_id>/delete', methods=['GET'])
@login_required
@check_permissions(['notification.rule.delete'])
def trigger_type_delete(trigger_type_id):
    trigger_type = TriggerType.query.get_or_404(trigger_type_id)
    db.session.delete(trigger_type)
    db.session.commit()
    return redirect(url_for('notification.trigger_types_view'))


@notification_bp.route('/rules')
@login_required
@check_permissions(['notification.rules.view'])
def rules_view():
    rules = NotificationRule.query.order_by(
        NotificationRule.created_at.desc()).all()
    copy_from_id = request.args.get('copy_from', type=int)
    rule_form = NotificationRuleForm()
    copied_rule = None

    if copy_from_id:
        copied_rule = NotificationRule.query.get_or_404(copy_from_id)
        rule_form.name.data = _build_copied_rule_name(copied_rule.name)
        rule_form.trigger_type.data = copied_rule.trigger_type or 0
        rule_form.days_before.data = copied_rule.days_before
        rule_form.trigger_value.data = copied_rule.trigger_value
        rule_form.send_time.data = copied_rule.send_time
        rule_form.template_id.data = copied_rule.template_id or 0
        rule_form.active.data = copied_rule.active

    trigger_type_map = {
        trigger.id: trigger for trigger in TriggerType.query.all()}
    template_map = {
        template.id: template for template in NotificationTemplate.query.all()}
    return render_template(
        'notification/site.rules.html',
        rules=rules,
        rule_form=rule_form,
        copied_rule=copied_rule,
        trigger_type_map=trigger_type_map,
        template_map=template_map,
    )


@notification_bp.route('/rules', methods=['POST'])
@login_required
@check_permissions(['notification.rule.create'])
def rule_post():
    rule_form = NotificationRuleForm()
    if rule_form.validate_on_submit():
        trigger_id = int(rule_form.trigger_type.data)
        template_id = int(rule_form.template_id.data)
        if trigger_id == 0:
            rule_form.trigger_type.errors.append(
                _('Please select a trigger type.'))
        if template_id == 0:
            rule_form.template_id.errors.append(_('Please select a template.'))
        if not rule_form.trigger_type.errors and not rule_form.template_id.errors:
            rule = NotificationRule(
                name=rule_form.name.data,
                trigger_type=trigger_id,
                days_before=rule_form.days_before.data,
                trigger_value=rule_form.trigger_value.data,
                send_time=rule_form.send_time.data,
                template_id=template_id,
                active=rule_form.active.data,
            )
            db.session.add(rule)
            db.session.commit()
            return redirect(url_for('notification.rule_detail', rule_id=rule.id))

    rules = NotificationRule.query.order_by(
        NotificationRule.created_at.desc()).all()
    trigger_type_map = {
        trigger.id: trigger for trigger in TriggerType.query.all()}
    template_map = {
        template.id: template for template in NotificationTemplate.query.all()}
    return render_template(
        'notification/site.rules.html',
        rules=rules,
        rule_form=rule_form,
        trigger_type_map=trigger_type_map,
        template_map=template_map,
    )


@notification_bp.route('/rules/<int:rule_id>')
@login_required
@check_permissions(['notification.rule.read'])
def rule_detail(rule_id):
    rule = NotificationRule.query.get_or_404(rule_id)
    rule_update_form = NotificationRuleForm(obj=rule)
    receiver_form = NotificationRuleReceiverForm()
    trigger = TriggerType.query.get(rule.trigger_type)
    template = NotificationTemplate.query.get(rule.template_id)
    group_map = {group.id: group for group in Group.query.all()}
    return render_template(
        'notification/site.rule.html',
        rule=rule,
        trigger=trigger,
        template=template,
        group_map=group_map,
        rule_update_form=rule_update_form,
        receiver_form=receiver_form,
    )


@notification_bp.route('/rules/<int:rule_id>/update', methods=['POST'])
@login_required
@check_permissions(['notification.rule.update'])
def rule_update(rule_id):
    rule = NotificationRule.query.get_or_404(rule_id)
    rule_update_form = NotificationRuleForm()

    if rule_update_form.validate_on_submit():
        trigger_id = int(rule_update_form.trigger_type.data)
        template_id = int(rule_update_form.template_id.data)
        if trigger_id == 0:
            rule_update_form.trigger_type.errors.append(
                _('Please select a trigger type.'))
        if template_id == 0:
            rule_update_form.template_id.errors.append(
                _('Please select a template.'))
        if not rule_update_form.trigger_type.errors and not rule_update_form.template_id.errors:
            rule.name = rule_update_form.name.data
            rule.trigger_type = trigger_id
            rule.days_before = rule_update_form.days_before.data
            rule.trigger_value = rule_update_form.trigger_value.data
            rule.send_time = rule_update_form.send_time.data
            rule.template_id = template_id
            rule.active = rule_update_form.active.data
            db.session.add(rule)
            db.session.commit()
            return redirect(url_for('notification.rule_detail', rule_id=rule.id))

    receiver_form = NotificationRuleReceiverForm()
    trigger = TriggerType.query.get(rule.trigger_type)
    template = NotificationTemplate.query.get(rule.template_id)
    group_map = {group.id: group for group in Group.query.all()}
    return render_template(
        'notification/site.rule.html',
        rule=rule,
        trigger=trigger,
        template=template,
        group_map=group_map,
        rule_update_form=rule_update_form,
        receiver_form=receiver_form,
    )


@notification_bp.route('/rules/<int:rule_id>/add_receiver', methods=['POST'])
@login_required
@check_permissions(['notification.rule.update'])
def add_receiver_to_rule(rule_id):
    rule = NotificationRule.query.get_or_404(rule_id)
    receiver_form = NotificationRuleReceiverForm()

    if receiver_form.validate_on_submit():
        receiver_type = receiver_form.receiver_type.data
        group_id = int(receiver_form.group_id.data or 0)
        custom_email = receiver_form.custom_email.data.strip(
        ) if receiver_form.custom_email.data else None

        if receiver_type == 'group':
            if group_id == 0:
                receiver_form.group_id.errors.append(
                    _('Please select a group.'))
            elif NotificationRuleReceiver.query.filter_by(rule_id=rule.id, receiver_type='group', group_id=group_id).first() is None:
                db.session.add(NotificationRuleReceiver(
                    rule_id=rule.id, receiver_type='group', group_id=group_id))
                db.session.commit()
                return redirect(url_for('notification.rule_detail', rule_id=rule.id))

        if receiver_type == 'email':
            if not custom_email:
                receiver_form.custom_email.errors.append(
                    _('Please enter a custom email.'))
            elif NotificationRuleReceiver.query.filter_by(rule_id=rule.id, receiver_type='email', custom_email=custom_email).first() is None:
                db.session.add(NotificationRuleReceiver(
                    rule_id=rule.id, receiver_type='email', custom_email=custom_email))
                db.session.commit()
                return redirect(url_for('notification.rule_detail', rule_id=rule.id))

    rule_update_form = NotificationRuleForm(obj=rule)
    trigger = TriggerType.query.get(rule.trigger_type)
    template = NotificationTemplate.query.get(rule.template_id)
    group_map = {group.id: group for group in Group.query.all()}
    return render_template(
        'notification/site.rule.html',
        rule=rule,
        trigger=trigger,
        template=template,
        group_map=group_map,
        rule_update_form=rule_update_form,
        receiver_form=receiver_form,
    )


@notification_bp.route('/rules/<int:rule_id>/remove_receiver/<int:receiver_id>', methods=['GET'])
@login_required
@check_permissions(['notification.rule.update'])
def remove_receiver_from_rule(rule_id, receiver_id):
    rule = NotificationRule.query.get_or_404(rule_id)
    receiver = NotificationRuleReceiver.query.filter_by(
        rule_id=rule.id, id=receiver_id).first_or_404()
    db.session.delete(receiver)
    db.session.commit()
    return redirect(url_for('notification.rule_detail', rule_id=rule.id))


@notification_bp.route('/rules/<int:rule_id>/delete', methods=['GET'])
@login_required
@check_permissions(['notification.rule.delete'])
def rule_delete(rule_id):
    rule = NotificationRule.query.get_or_404(rule_id)
    for receiver in list(rule.receivers):
        db.session.delete(receiver)
    db.session.delete(rule)
    db.session.commit()
    return redirect(url_for('notification.rules_view'))


@notification_bp.route('/logs')
@login_required
@check_permissions(['notification.logs.read'])
def logs_view():
    logs = NotificationLog.query.order_by(NotificationLog.sent_at.desc()).all()
    rule_map = {rule.id: rule for rule in NotificationRule.query.all()}
    member_map = {member.id: member for member in Member.query.all()}
    event_map = {event.id: event for event in Event.query.all()}
    clear_logs_form = NotificationLogClearForm()
    cleanup_result = {
        'count': request.args.get('count', type=int),
        'action': request.args.get('action'),
        'before_date': request.args.get('before_date'),
    }
    if cleanup_result['count'] is None:
        cleanup_result = None
    return render_template(
        'notification/site.logs.html',
        logs=logs,
        rule_map=rule_map,
        member_map=member_map,
        event_map=event_map,
        clear_logs_form=clear_logs_form,
        cleanup_result=cleanup_result,
    )


@notification_bp.route('/logs/clear', methods=['POST'])
@login_required
@check_permissions(['notification.logs.delete'])
def clear_logs():
    """Clear notification logs based on the selected action."""
    clear_logs_form = NotificationLogClearForm()

    if not clear_logs_form.validate_on_submit():
        return redirect(url_for('notification.logs_view'))

    # Verify password
    password = clear_logs_form.password.data
    if not current_user.check_password(password):
        clear_logs_form.password.errors.append(
            _('Invalid password. Please try again.'))
        logs = NotificationLog.query.order_by(
            NotificationLog.sent_at.desc()).all()
        rule_map = {rule.id: rule for rule in NotificationRule.query.all()}
        member_map = {member.id: member for member in Member.query.all()}
        event_map = {event.id: event for event in Event.query.all()}
        return render_template(
            'notification/site.logs.html',
            logs=logs,
            rule_map=rule_map,
            member_map=member_map,
            event_map=event_map,
            clear_logs_form=clear_logs_form,
            cleanup_result=None,
        )

    action = clear_logs_form.action.data
    count = 0
    before_date = None

    if action == 'all':
        # Delete all logs
        count = db.session.query(NotificationLog).delete(
            synchronize_session=False)
        db.session.commit()

    elif action == 'failed':
        # Delete only failed logs
        count = NotificationLog.query.filter_by(
            status='FAILED').delete(synchronize_session=False)
        db.session.commit()

    elif action == 'before_date':
        # Delete logs before the specified date
        before_date = clear_logs_form.before_date.data

        if not before_date:
            # Validation failed, redirect without changes
            return redirect(url_for('notification.logs_view'))

        count = db.session.query(NotificationLog).filter(
            NotificationLog.sent_at < before_date
        ).delete(synchronize_session=False)
        db.session.commit()

    return redirect(url_for(
        'notification.logs_view',
        count=count,
        action=action,
        before_date=before_date.isoformat() if before_date else None,
    ))


@notification_bp.route('/events')
@login_required
@check_permissions(['notification.events.view'])
def events_view():
    events = Event.query.order_by(Event.start_at.desc()).all()
    event_form = EventForm()
    cleanup_form = EventCleanupForm()
    trigger_type_map = {
        trigger.code: trigger for trigger in TriggerType.query.all()}
    cleanup_result = {
        'deleted_events': request.args.get('deleted_events', type=int),
        'deleted_logs': request.args.get('deleted_logs', type=int),
        'age_value': request.args.get('age_value', type=int),
        'age_unit': request.args.get('age_unit'),
    }
    if cleanup_result['deleted_events'] is None and cleanup_result['deleted_logs'] is None:
        cleanup_result = None
    # Detect recurrence series links for events (either from column or embedded token)
    for ev in events:
        _attach_rendered_event_title(ev)
        ev._recurrence_group_id = None
        if getattr(ev, 'recurrence_group_id', None):
            ev._recurrence_group_id = ev.recurrence_group_id
        else:
            # look for token like "#sym:recurrence_group_id 123" in title or description
            for text in (ev.title or '', ev.description or ''):
                m = re.search(r'#sym:recurrence_group_id\s*(\d+)', text)
                if m:
                    ev._recurrence_group_id = int(m.group(1))
                    break
        ev.recurrence_series_link = url_for(
            'notification.event_series_detail', group_id=ev._recurrence_group_id) if ev._recurrence_group_id else None
    return render_template(
        'notification/site.events.html',
        events=events,
        event_form=event_form,
        cleanup_form=cleanup_form,
        trigger_type_map=trigger_type_map,
        cleanup_result=cleanup_result,
    )


@notification_bp.route('/events/import-ics', methods=['GET', 'POST'])
@login_required
@check_permissions(['notification.event.create'])
def import_ics():
    """Import events from an uploaded .ics file."""
    form = ICSImportForm()

    if form.validate_on_submit():
        uploaded = request.files.get('ics_file')
        if not uploaded:
            form.ics_file.errors.append(_('No file uploaded.'))
        else:
            try:
                data = uploaded.read()
                cal = Calendar.from_ical(data)
            except Exception:
                form.ics_file.errors.append(_('Invalid ICS file.'))
                cal = None

            imported = 0
            if cal is not None:
                # determine trigger code to apply to all events (if selected)
                trigger_code = form.trigger_type.data or ''
                if trigger_code == '0' or trigger_code == 0:
                    trigger_code = ''

                for component in cal.walk():
                    if component.name != 'VEVENT':
                        continue

                    summary = component.get('SUMMARY')
                    dtstart = component.get('DTSTART')
                    dtend = component.get('DTEND')
                    description = component.get('DESCRIPTION')
                    location = component.get('LOCATION')

                    # extract python datetime/date
                    start_dt = getattr(dtstart, 'dt', None)
                    end_dt = getattr(dtend, 'dt', None) if dtend else None

                    # normalize dates to datetimes
                    if start_dt and not isinstance(start_dt, datetime):
                        start_dt = datetime.combine(
                            start_dt, datetime.min.time())
                    if end_dt and not isinstance(end_dt, datetime):
                        end_dt = datetime.combine(end_dt, datetime.min.time())

                    # if timezone-aware, convert to UTC and drop tzinfo
                    if isinstance(start_dt, datetime) and getattr(start_dt, 'tzinfo', None):
                        start_dt = start_dt.astimezone(
                            timezone.utc).replace(tzinfo=None)
                    if isinstance(end_dt, datetime) and getattr(end_dt, 'tzinfo', None):
                        end_dt = end_dt.astimezone(
                            timezone.utc).replace(tzinfo=None)

                    if not start_dt:
                        continue

                    event = Event(
                        title=str(summary) if summary else _('Untitled event'),
                        event_type=trigger_code or 'EVENT_START',
                        description=str(description) if description else None,
                        start_at=start_dt,
                        end_at=end_dt,
                        location=str(location) if location else None,
                        is_recurring=False,
                    )
                    db.session.add(event)
                    imported += 1

                db.session.commit()

            return redirect(url_for('notification.events_view', imported_count=imported))

    return render_template('notification/site.import_ics.html', form=form)


@notification_bp.route('/members/import', methods=['GET', 'POST'])
@login_required
@check_permissions([
    'notification.member.create',
    'notification.member.update',
    'notification.member.delete',
])
def import_members():
    """Import members from an uploaded CSV file and sync them by member number."""
    form = MemberImportForm()

    if form.validate_on_submit():
        uploaded = request.files.get('csv_file')
        if not uploaded:
            form.csv_file.errors.append(_('No file uploaded.'))
            return render_template('notification/site.import_members.html', form=form)

        try:
            raw_data = uploaded.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            form.csv_file.errors.append(
                _('Invalid CSV file encoding. Use UTF-8.'))
            return render_template('notification/site.import_members.html', form=form)

        if not raw_data.strip():
            form.csv_file.errors.append(_('The CSV file is empty.'))
            return render_template('notification/site.import_members.html', form=form)

        sample = raw_data[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(io.StringIO(raw_data), dialect=dialect)
        expected_fields = {
            'member_number',
            'first_name',
            'last_name',
            'birth_date',
            'email',
            'phone',
            'member_since',
            'required_hours',
            'status',
        }

        if not reader.fieldnames:
            form.csv_file.errors.append(
                _('The CSV file is missing a header row.'))
            return render_template('notification/site.import_members.html', form=form)

        normalized_fieldnames = {
            _normalize_csv_header(fieldname) for fieldname in reader.fieldnames
        }
        if not expected_fields.issubset(normalized_fieldnames):
            form.csv_file.errors.append(_(
                'The CSV file must contain the columns: member_number, first_name, last_name, birth_date, email, phone, member_since, required_hours, status.'
            ))
            return render_template('notification/site.import_members.html', form=form)

        rows_by_member_number = {}
        for row_number, row in enumerate(reader, start=2):
            normalized_row = {
                _normalize_csv_header(key): _normalize_csv_value(value)
                for key, value in row.items()
            }
            member_number = normalized_row.get('member_number')
            if not member_number:
                continue
            if not normalized_row.get('first_name') or not normalized_row.get('last_name') or not normalized_row.get('email'):
                form.csv_file.errors.append(_(
                    f'Row {row_number}: first_name, last_name, and email are required.'
                ))
                return render_template('notification/site.import_members.html', form=form)
            rows_by_member_number[member_number] = normalized_row

        if not rows_by_member_number:
            form.csv_file.errors.append(
                _('The CSV file does not contain any valid member rows.'))
            return render_template('notification/site.import_members.html', form=form)

        existing_members = {
            member.member_number: member
            for member in Member.query.filter(Member.member_number.isnot(None)).all()
        }

        imported_count = 0
        updated_count = 0
        seen_member_numbers = set()

        for member_number, row in rows_by_member_number.items():
            seen_member_numbers.add(member_number)
            member = existing_members.get(member_number)
            if member is None:
                member = Member(member_number=member_number)
                db.session.add(member)
                imported_count += 1
            else:
                updated_count += 1

            member.first_name = row.get('first_name')
            member.last_name = row.get('last_name')
            member.birth_date = _parse_member_import_date(
                row.get('birth_date'))
            member.email = row.get('email')
            member.phone = row.get('phone')
            member.join_date = _parse_member_import_date(
                row.get('member_since'))
            member.required_hours = _parse_member_import_required_hours(
                row.get('required_hours')) or 0
            member.active = _parse_member_import_status(row.get('status'))

        if seen_member_numbers:
            members_to_delete = Member.query.filter(
                or_(
                    Member.member_number.is_(None),
                    ~Member.member_number.in_(seen_member_numbers),
                )
            ).all()
        else:
            members_to_delete = Member.query.all()

        deleted_count = 0
        for member in members_to_delete:
            for event_participant in list(member.events):
                db.session.delete(event_participant)
            member.groups.clear()
            db.session.delete(member)
            deleted_count += 1

        db.session.commit()

        return redirect(url_for(
            'notification.members_view',
            imported_count=imported_count,
            updated_count=updated_count,
            deleted_count=deleted_count,
        ))

    return render_template('notification/site.import_members.html', form=form)


@notification_bp.route('/members/import/template', methods=['GET'])
@login_required
@check_permissions([
    'notification.member.create',
    'notification.member.update',
    'notification.member.delete',
])
def download_member_import_template():
    """Download an empty member import CSV with the required headers."""
    response = Response(
        _build_member_import_template_csv(),
        mimetype='text/csv; charset=utf-8',
    )
    response.headers['Content-Disposition'] = 'attachment; filename=member_import_template.csv'
    return response


@notification_bp.route('/events/import', methods=['GET', 'POST'])
@login_required
@check_permissions(['notification.event.create'])
def import_events():
    """Import events from an uploaded CSV/TSV file."""
    form = EventImportForm()

    if form.validate_on_submit():
        uploaded = request.files.get('csv_file')
        if not uploaded:
            form.csv_file.errors.append(_('No file uploaded.'))
            return render_template('notification/site.import_events.html', form=form)

        try:
            raw_data = _decode_event_import_data(uploaded)
        except UnicodeDecodeError:
            form.csv_file.errors.append(
                _('Invalid file encoding. Use UTF-8 or UTF-16.'))
            return render_template('notification/site.import_events.html', form=form)

        if not raw_data.strip():
            form.csv_file.errors.append(_('The file is empty.'))
            return render_template('notification/site.import_events.html', form=form)

        sample = raw_data[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        except csv.Error:
            dialect = csv.excel_tab

        reader = csv.DictReader(io.StringIO(raw_data), dialect=dialect)
        expected_fields = {
            'title',
            'description',
            'start_at',
            'end_at',
            'location',
            'participants',
        }

        if not reader.fieldnames:
            form.csv_file.errors.append(
                _('The file is missing a header row.'))
            return render_template('notification/site.import_events.html', form=form)

        normalized_fieldnames = {
            _normalize_csv_header(fieldname) for fieldname in reader.fieldnames
        }
        if not expected_fields.issubset(normalized_fieldnames):
            form.csv_file.errors.append(_(
                'The file must contain the columns: title, description, start_at, end_at, location, participants.'
            ))
            return render_template('notification/site.import_events.html', form=form)

        trigger_type = form.trigger_type.data or 'EVENT'

        rows = []
        for row_number, row in enumerate(reader, start=2):
            normalized_row = {
                _normalize_csv_header(key): _normalize_csv_value(value)
                for key, value in row.items()
            }

            title = normalized_row.get('title')
            if not title:
                form.csv_file.errors.append(_(
                    f'Row {row_number}: title is required.'
                ))
                return render_template('notification/site.import_events.html', form=form)

            start_at = _parse_event_import_datetime(
                normalized_row.get('start_at'))
            if not start_at:
                form.csv_file.errors.append(_(
                    f'Row {row_number}: start_at must be a valid datetime (e.g., 2026-01-01 14:00).'
                ))
                return render_template('notification/site.import_events.html', form=form)

            end_at = _parse_event_import_datetime(normalized_row.get('end_at'))
            participants = _parse_event_import_participants(
                normalized_row.get('participants'))

            rows.append({
                'title': title,
                'description': normalized_row.get('description'),
                'start_at': start_at,
                'end_at': end_at,
                'location': normalized_row.get('location'),
                'participants': participants,
            })

        if not rows:
            form.csv_file.errors.append(
                _('The file does not contain any valid event rows.'))
            return render_template('notification/site.import_events.html', form=form)

        # Get all members for validation
        all_members_by_number = {
            member.member_number: member
            for member in Member.query.filter(Member.member_number.isnot(None)).all()
        }
        all_members_by_id = {
            member.id: member for member in Member.query.all()}

        imported_count = 0
        for row in rows:
            event = Event(
                title=row['title'],
                description=row['description'],
                event_type=trigger_type,
                start_at=row['start_at'],
                end_at=row['end_at'],
                location=row['location'],
                is_recurring=False,
            )
            db.session.add(event)
            db.session.flush()  # Get the ID

            # Add participants
            for participant_value in row['participants']:
                member = all_members_by_number.get(participant_value)
                if member is None and participant_value.isdigit():
                    member = all_members_by_id.get(int(participant_value))

                if member is not None:
                    participant = EventParticipant(
                        event_id=event.id,
                        member_id=member.id,
                        status='confirmed',
                    )
                    db.session.add(participant)

            imported_count += 1

        db.session.commit()

        flash(_(f'{imported_count} events imported successfully.'), 'success')
        return redirect(url_for('notification.events_view'))

    return render_template('notification/site.import_events.html', form=form)


@notification_bp.route('/events/import/template', methods=['GET'])
@login_required
@check_permissions(['notification.event.create'])
def download_event_import_template():
    """Download an empty event import TSV with the required headers."""
    response = Response(
        _build_event_import_template_csv(),
        mimetype='text/tab-separated-values; charset=utf-8',
    )
    response.headers['Content-Disposition'] = 'attachment; filename=event_import_template.tsv'
    return response


@notification_bp.route('/events/cleanup', methods=['POST'])
@login_required
@check_permissions(['notification.event.delete'])
def cleanup_old_events():
    cleanup_form = EventCleanupForm()
    if not cleanup_form.validate_on_submit():
        events = Event.query.order_by(Event.start_at.desc()).all()
        for event in events:
            _attach_rendered_event_title(event)
        event_form = EventForm()
        trigger_type_map = {
            trigger.code: trigger for trigger in TriggerType.query.all()}
        return render_template(
            'notification/site.events.html',
            events=events,
            event_form=event_form,
            cleanup_form=cleanup_form,
            trigger_type_map=trigger_type_map,
        )

    age_value = cleanup_form.age_value.data
    age_unit = cleanup_form.age_unit.data

    cutoff = datetime.utcnow()
    if age_unit == 'days':
        cutoff -= timedelta(days=age_value)
    elif age_unit == 'months':
        cutoff = _add_months(cutoff, -age_value)
    else:
        cutoff = _add_months(cutoff, -(age_value * 12))

    event_ids = [
        event_id for (event_id,) in db.session.query(Event.id).filter(
            Event.start_at < cutoff
        ).all()
    ]

    deleted_events = 0
    deleted_logs = 0
    if event_ids:
        db.session.query(EventParticipant).filter(
            EventParticipant.event_id.in_(event_ids)
        ).delete(synchronize_session=False)
        deleted_logs = db.session.query(NotificationLog).filter(
            NotificationLog.event_id.in_(event_ids)
        ).delete(synchronize_session=False)
        deleted_events = db.session.query(Event).filter(
            Event.id.in_(event_ids)
        ).delete(synchronize_session=False)
        db.session.commit()

    return redirect(url_for(
        'notification.events_view',
        deleted_events=deleted_events,
        deleted_logs=deleted_logs,
        age_value=age_value,
        age_unit=age_unit,
    ))


@notification_bp.route('/events', methods=['POST'])
@login_required
@check_permissions(['notification.event.create'])
def event_post():
    event_form = EventForm()
    if event_form.validate_on_submit():
        trigger_code = event_form.event_type.data or 'EVENT_START'
        is_recurring = event_form.is_recurring.data
        recurrence_pattern = event_form.recurrence_pattern.data or 'WEEKLY'
        recurrence_count = event_form.recurrence_count.data or 1

        # Create event(s)
        if is_recurring and recurrence_count > 1:
            # Create recurring events with a shared recurrence_group_id
            base_start = event_form.start_at.data
            base_end = event_form.end_at.data

            # Create placeholder to get the group ID
            placeholder = Event(
                title="placeholder",
                event_type=trigger_code,
                start_at=base_start,
            )
            db.session.add(placeholder)
            db.session.flush()  # Get the ID without committing
            recurrence_group_id = placeholder.id
            db.session.rollback()  # Undo placeholder

            # Create all events with the group ID
            created_events = []
            for i in range(recurrence_count):
                event_start = _build_recurrence_start(
                    base_start,
                    recurrence_pattern,
                    i,
                )
                if base_end:
                    duration = base_end - base_start
                    event_end = event_start + duration
                else:
                    event_end = None

                event = Event(
                    title=event_form.title.data,
                    event_type=trigger_code,
                    description=event_form.description.data or None,
                    start_at=event_start,
                    end_at=event_end,
                    location=event_form.location.data or None,
                    is_recurring=False,
                    recurrence_group_id=recurrence_group_id,
                )
                db.session.add(event)
                created_events.append(event)

            db.session.commit()

            # Update the recurrence_group_id to use the first event's ID
            recurrence_group_id = created_events[0].id
            for event in created_events:
                event.recurrence_group_id = recurrence_group_id
            db.session.commit()

            # Redirect to series overview
            return redirect(url_for('notification.event_series_detail', group_id=recurrence_group_id))
        else:
            # Create single event
            event = Event(
                title=event_form.title.data,
                event_type=trigger_code,
                description=event_form.description.data or None,
                start_at=event_form.start_at.data,
                end_at=event_form.end_at.data,
                location=event_form.location.data or None,
                is_recurring=False,
            )
            db.session.add(event)
            db.session.commit()
            return redirect(url_for('notification.event_detail', event_id=event.id))

    events = Event.query.order_by(Event.start_at.desc()).all()
    trigger_type_map = {
        trigger.code: trigger for trigger in TriggerType.query.all()}
    return render_template(
        'notification/site.events.html',
        events=events,
        event_form=event_form,
        trigger_type_map=trigger_type_map,
    )


@notification_bp.route('/events/<int:event_id>')
@login_required
@check_permissions(['notification.event.read'])
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    _attach_rendered_event_title(event)
    event_update_form = EventForm(obj=event)
    participant_form = NotificationEventParticipantForm(event_id=event.id)
    trigger = TriggerType.query.filter_by(code=event.event_type).first()
    # detect recurrence series link for this event
    event._recurrence_group_id = None
    if getattr(event, 'recurrence_group_id', None):
        event._recurrence_group_id = event.recurrence_group_id
    else:
        for text in (event.title or '', event.description or ''):
            m = re.search(r'#sym:recurrence_group_id\s*(\d+)', text)
            if m:
                event._recurrence_group_id = int(m.group(1))
                break
    event.recurrence_series_link = url_for(
        'notification.event_series_detail', group_id=event._recurrence_group_id) if event._recurrence_group_id else None
    return render_template(
        'notification/site.event.html',
        event=event,
        trigger=trigger,
        event_update_form=event_update_form,
        participant_form=participant_form,
    )


@notification_bp.route('/events/<int:event_id>/update', methods=['POST'])
@login_required
@check_permissions(['notification.event.update'])
def event_update(event_id):
    event = Event.query.get_or_404(event_id)
    event_update_form = EventForm()

    if event_update_form.validate_on_submit():
        trigger_code = event_update_form.event_type.data or 'EVENT_START'
        event.title = event_update_form.title.data
        event.event_type = trigger_code
        event.description = event_update_form.description.data or None
        event.start_at = event_update_form.start_at.data
        event.end_at = event_update_form.end_at.data
        event.location = event_update_form.location.data or None
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('notification.event_detail', event_id=event.id))

    participant_form = NotificationEventParticipantForm(event_id=event.id)
    trigger = TriggerType.query.filter_by(code=event.event_type).first()
    return render_template(
        'notification/site.event.html',
        event=event,
        trigger=trigger,
        event_update_form=event_update_form,
        participant_form=participant_form,
    )


@notification_bp.route('/events/<int:event_id>/add_member', methods=['POST'])
@login_required
@check_permissions(['notification.event.update'])
def add_member_to_event(event_id):
    event = Event.query.get_or_404(event_id)
    participant_form = NotificationEventParticipantForm(event_id=event.id)

    if participant_form.validate_on_submit():
        member_id = int(participant_form.member.data)
        if member_id == 0:
            participant_form.member.errors.append(
                _('Please select a member to add to the event.'))
        else:
            member = Member.query.get_or_404(member_id)
            existing_participant = EventParticipant.query.filter_by(
                event_id=event.id,
                member_id=member.id,
            ).first()
            if existing_participant is None:
                db.session.add(EventParticipant(
                    event_id=event.id, member_id=member.id, status='registered'))
                db.session.commit()
            return redirect(url_for('notification.event_detail', event_id=event.id))

    event_update_form = EventForm(obj=event)
    return render_template(
        'notification/site.event.html',
        event=event,
        event_update_form=event_update_form,
        participant_form=participant_form,
    )


@notification_bp.route('/events/<int:event_id>/remove_member/<int:member_id>', methods=['GET'])
@login_required
@check_permissions(['notification.event.update'])
def remove_member_from_event(event_id, member_id):
    event = Event.query.get_or_404(event_id)
    participant = EventParticipant.query.filter_by(
        event_id=event.id, member_id=member_id).first_or_404()
    db.session.delete(participant)
    db.session.commit()
    return redirect(url_for('notification.event_detail', event_id=event.id))


@notification_bp.route('/events/<int:event_id>/delete', methods=['GET'])
@login_required
@check_permissions(['notification.event.delete'])
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('notification.events_view'))


@notification_bp.route('/events/series/<int:group_id>')
@login_required
@check_permissions(['notification.events.view'])
def event_series_detail(group_id):
    """Show all events in a series and allow adding participants to each."""
    series_events = Event.query.filter_by(recurrence_group_id=group_id).order_by(
        Event.start_at.asc()).all()

    if not series_events:
        return redirect(url_for('notification.events_view'))

    for event in series_events:
        _attach_rendered_event_title(event)

    first_event = series_events[0]
    participant_forms = {
        first_event.id: NotificationEventParticipantForm(
            event_id=first_event.id)
    }
    for event in series_events[1:]:
        participant_forms[event.id] = NotificationEventParticipantForm(
            event_id=event.id)

    return render_template(
        'notification/site.event_series.html',
        series_events=series_events,
        participant_forms=participant_forms,
    )


@notification_bp.route('/groups')
@login_required
@check_permissions(['notification.groups.view'])
def groups_view():
    groups = Group.query.all()
    group_form = AuthGroupCreateForm()
    return render_template('notification/site.groups.html', groups=groups, group_form=group_form)


@notification_bp.route('/groups', methods=['POST'])
@login_required
@check_permissions(['notification.group.create'])
def group_post():
    group_form = AuthGroupCreateForm()
    if group_form.validate_on_submit():
        if Group.query.filter_by(name=group_form.name.data).first() is None:
            group = Group(
                name=group_form.name.data,
                description=group_form.description.data or None,
            )
            db.session.add(group)
            db.session.commit()
            return redirect(url_for('notification.groups_view'))
        group_form.name.errors.append(_('Group name already exists.'))

    groups = Group.query.all()
    return render_template('notification/site.groups.html', groups=groups, group_form=group_form)


@notification_bp.route('/groups/<int:group_id>')
@login_required
@check_permissions(['notification.group.read'])
def group_detail(group_id):
    group = Group.query.get_or_404(group_id)
    group_update_form = AuthGroupUpdateForm(obj=group)
    group_membership_form = NotificationGroupMembershipForm(group_id=group.id)
    return render_template(
        'notification/site.group.html',
        group=group,
        group_update_form=group_update_form,
        group_membership_form=group_membership_form,
    )


@notification_bp.route('/groups/<int:group_id>/update', methods=['POST'])
@login_required
@check_permissions(['notification.group.update'])
def group_update(group_id):
    group = Group.query.get_or_404(group_id)
    group_update_form = AuthGroupUpdateForm()

    if group_update_form.validate_on_submit():
        duplicate_group = Group.query.filter(
            Group.id != group.id,
            Group.name == group_update_form.name.data,
        ).first()
        if duplicate_group is None:
            group.name = group_update_form.name.data
            group.description = group_update_form.description.data or None
            db.session.add(group)
            db.session.commit()
            return redirect(url_for('notification.group_detail', group_id=group.id))
        group_update_form.name.errors.append(_('Group name already exists.'))

    group_membership_form = NotificationGroupMembershipForm(group_id=group.id)
    return render_template(
        'notification/site.group.html',
        group=group,
        group_update_form=group_update_form,
        group_membership_form=group_membership_form,
    )


@notification_bp.route('/groups/<int:group_id>/add_member', methods=['POST'])
@login_required
@check_permissions(['notification.group.update'])
def add_member_to_group(group_id):
    """Add a member to a notification group."""
    group = Group.query.get_or_404(group_id)
    group_membership_form = NotificationGroupMembershipForm(group_id=group.id)

    if group_membership_form.validate_on_submit():
        member_id = int(group_membership_form.member.data)
        if member_id == 0:
            group_membership_form.member.errors.append(
                _('Please select a member to add to the group.'))
        else:
            member = Member.query.get_or_404(member_id)
            if member not in group.members:
                group.members.append(member)
                db.session.add(group)
                db.session.commit()
            return redirect(url_for('notification.group_detail', group_id=group.id))

    group_update_form = AuthGroupUpdateForm(obj=group)
    return render_template(
        'notification/site.group.html',
        group=group,
        group_update_form=group_update_form,
        group_membership_form=group_membership_form,
    )


@notification_bp.route('/groups/<int:group_id>/remove_member/<int:member_id>', methods=['GET'])
@login_required
@check_permissions(['notification.group.update'])
def remove_member_from_group(group_id, member_id):
    """Remove a member from a notification group."""
    group = Group.query.get_or_404(group_id)
    member = Member.query.get_or_404(member_id)
    if member in group.members:
        group.members.remove(member)
        db.session.commit()
    return redirect(url_for('notification.group_detail', group_id=group.id))


@notification_bp.route('/groups/<int:group_id>/delete', methods=['GET'])
@login_required
@check_permissions(['notification.group.delete'])
def group_delete(group_id):
    group = Group.query.get_or_404(group_id)
    group.members.clear()
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('notification.groups_view'))


@notification_bp.route('/members')
@login_required
@check_permissions(['notification.members.read'])
def members_view():
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'id', type=str)
    sort_dir = request.args.get('dir', 'asc', type=str)
    per_page = request.args.get('per_page', 10, type=int)

    # Filter parameters
    search_name = request.args.get('search_name', '', type=str)
    search_number = request.args.get('search_number', '', type=str)
    filter_active = request.args.get('filter_active', '', type=str)
    filter_hours = request.args.get('filter_hours', '', type=str)
    filter_hours = request.args.get('filter_hours', '', type=str)

    # Build query and a subquery that contains the sum of hours per member for the current year
    current_year = datetime.utcnow().year
    hours_subq = db.session.query(
        WorkingHoursLog.member_id.label('member_id'),
        func.coalesce(func.sum(WorkingHoursLog.hours), 0).label('sum_hours'),
    ).filter(
        extract('year', WorkingHoursLog.date) == current_year
    ).group_by(WorkingHoursLog.member_id).subquery()

    query = db.session.query(Member).outerjoin(
        hours_subq, Member.id == hours_subq.c.member_id)

    # Apply filters
    if search_name:
        query = query.filter(
            or_(
                Member.first_name.ilike(f'%{search_name}%'),
                Member.last_name.ilike(f'%{search_name}%')
            )
        )

    if search_number:
        query = query.filter(Member.member_number.ilike(f'%{search_number}%'))

    if filter_active == 'true':
        query = query.filter(Member.active == True)
    elif filter_active == 'false':
        query = query.filter(Member.active == False)

    # Filter by hours fulfillment
    if filter_hours:
        sum_hours_expr = func.coalesce(hours_subq.c.sum_hours, 0)
        if filter_hours == 'met':
            query = query.filter(and_(Member.required_hours != 0, sum_hours_expr >= Member.required_hours))
        elif filter_hours == 'not_met':
            query = query.filter(and_(Member.required_hours != 0, sum_hours_expr < Member.required_hours))
        elif filter_hours == 'no_requirement':
            query = query.filter(Member.required_hours == 0)

    # Filter by hours fulfillment
    if filter_hours:
        sum_hours_expr = func.coalesce(hours_subq.c.sum_hours, 0)
        if filter_hours == 'met':
            query = query.filter(and_(Member.required_hours != 0, sum_hours_expr >= Member.required_hours))
        elif filter_hours == 'not_met':
            query = query.filter(and_(Member.required_hours != 0, sum_hours_expr < Member.required_hours))
        elif filter_hours == 'no_requirement':
            query = query.filter(Member.required_hours == 0)

    # Apply sorting — support sorting by aggregated numeric columns
    if sort_by == 'sum_hours_this_year':
        sort_expr = func.coalesce(hours_subq.c.sum_hours, 0)
    elif sort_by == 'hours_status':
        # If required_hours == 0 treat as very large to put them at the top when sorting desc
        sort_expr = case(
            (Member.required_hours == 0, 999999),
            else_=func.coalesce(hours_subq.c.sum_hours, 0) /
            func.nullif(Member.required_hours, 0),
        )
    else:
        sort_expr = getattr(Member, sort_by, Member.id)

    if sort_dir == 'desc':
        query = query.order_by(sort_expr.desc())
    else:
        query = query.order_by(sort_expr.asc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    members = pagination.items

    # Efficiently load sum of hours for members on this page
    member_ids = [m.id for m in members]
    if member_ids:
        sums = db.session.query(
            WorkingHoursLog.member_id,
            func.coalesce(func.sum(WorkingHoursLog.hours),
                          0).label('sum_hours'),
        ).filter(
            WorkingHoursLog.member_id.in_(member_ids),
            extract('year', WorkingHoursLog.date) == current_year,
        ).group_by(WorkingHoursLog.member_id).all()
        sums_map = {mid: s for (mid, s) in sums}
    else:
        sums_map = {}

    for member in members:
        member.sum_hours_this_year = sums_map.get(member.id, 0)

    member_form = MemberForm()
    return render_template(
        'notification/site.members.html',
        members=members,
        member_form=member_form,
        pagination=pagination,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search_name=search_name,
        search_number=search_number,
        filter_active=filter_active,
        filter_hours=filter_hours,
        per_page=per_page,
        max=max,
        min=min
    )


@notification_bp.route('/members', methods=['POST'])
@login_required
@check_permissions(['notification.member.create'])
def member_post():
    member_form = MemberForm()
    if member_form.validate_on_submit():
        member = Member(
            member_number=member_form.member_number.data,
            first_name=member_form.first_name.data,
            last_name=member_form.last_name.data,
            email=member_form.email.data,
            phone=member_form.phone.data,
            birth_date=member_form.birth_date.data,
            join_date=member_form.join_date.data,
            required_hours=member_form.required_hours.data or 0,
            active=member_form.active.data,
        )
        db.session.add(member)
        db.session.commit()
        return redirect(url_for('notification.member_detail', member_id=member.id))

    # Re-render with pagination when form fails validation
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'id', type=str)
    sort_dir = request.args.get('dir', 'asc', type=str)
    per_page = request.args.get('per_page', 10, type=int)

    search_name = request.args.get('search_name', '', type=str)
    search_number = request.args.get('search_number', '', type=str)
    filter_active = request.args.get('filter_active', '', type=str)
    filter_hours = request.args.get('filter_hours', '', type=str)

    # Build hours subquery for sorting and efficient lookup
    current_year = datetime.utcnow().year
    hours_subq = db.session.query(
        WorkingHoursLog.member_id.label('member_id'),
        func.coalesce(func.sum(WorkingHoursLog.hours), 0).label('sum_hours'),
    ).filter(
        extract('year', WorkingHoursLog.date) == current_year
    ).group_by(WorkingHoursLog.member_id).subquery()

    query = db.session.query(Member).outerjoin(
        hours_subq, Member.id == hours_subq.c.member_id)

    if search_name:
        query = query.filter(
            or_(
                Member.first_name.ilike(f'%{search_name}%'),
                Member.last_name.ilike(f'%{search_name}%')
            )
        )

    if search_number:
        query = query.filter(Member.member_number.ilike(f'%{search_number}%'))

    if filter_active == 'true':
        query = query.filter(Member.active == True)
    elif filter_active == 'false':
        query = query.filter(Member.active == False)

    # Sorting
    if sort_by == 'sum_hours_this_year':
        sort_expr = func.coalesce(hours_subq.c.sum_hours, 0)
    elif sort_by == 'hours_status':
        sort_expr = case(
            (Member.required_hours == 0, 999999),
            else_=func.coalesce(hours_subq.c.sum_hours, 0) /
            func.nullif(Member.required_hours, 0),
        )
    else:
        sort_expr = getattr(Member, sort_by, Member.id)

    if sort_dir == 'desc':
        query = query.order_by(sort_expr.desc())
    else:
        query = query.order_by(sort_expr.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    members = pagination.items

    # Efficient per-page sum lookup
    member_ids = [m.id for m in members]
    if member_ids:
        sums = db.session.query(
            WorkingHoursLog.member_id,
            func.coalesce(func.sum(WorkingHoursLog.hours),
                          0).label('sum_hours'),
        ).filter(
            WorkingHoursLog.member_id.in_(member_ids),
            extract('year', WorkingHoursLog.date) == current_year,
        ).group_by(WorkingHoursLog.member_id).all()
        sums_map = {mid: s for (mid, s) in sums}
    else:
        sums_map = {}

    for member in members:
        member.sum_hours_this_year = sums_map.get(member.id, 0)

    return render_template(
        'notification/site.members.html',
        members=members,
        member_form=member_form,
        pagination=pagination,
        sort_by=sort_by,
        sort_dir=sort_dir,
        search_name=search_name,
        search_number=search_number,
        filter_active=filter_active,
        filter_hours=filter_hours,
        per_page=per_page,
        max=max,
        min=min
    )


@notification_bp.route('/members/<int:member_id>')
@login_required
@check_permissions(['notification.member.read'])
def member_detail(member_id):
    member = Member.query.get_or_404(member_id)
    member_update_form = MemberForm(obj=member)
    member_group_form = NotificationMemberGroupForm(member_id=member.id)
    return render_template(
        'notification/site.member.html',
        member=member,
        member_update_form=member_update_form,
        member_group_form=member_group_form,
    )


@notification_bp.route('/members/<int:member_id>/update', methods=['POST'])
@login_required
@check_permissions(['notification.member.update'])
def member_update(member_id):
    member = Member.query.get_or_404(member_id)
    member_update_form = MemberForm()

    if member_update_form.validate_on_submit():
        member.member_number = member_update_form.member_number.data
        member.first_name = member_update_form.first_name.data
        member.last_name = member_update_form.last_name.data
        member.email = member_update_form.email.data
        member.phone = member_update_form.phone.data
        member.birth_date = member_update_form.birth_date.data
        member.join_date = member_update_form.join_date.data
        member.required_hours = member_update_form.required_hours.data or 0
        member.active = member_update_form.active.data
        db.session.add(member)
        db.session.commit()
        return redirect(url_for('notification.member_detail', member_id=member.id))

    return render_template(
        'notification/site.member.html',
        member=member,
        member_update_form=member_update_form,
    )


@notification_bp.route('/members/<int:member_id>/add_group', methods=['POST'])
@login_required
@check_permissions(['notification.member.update'])
def add_group_to_member(member_id):
    """Add a notification group to a member."""
    member = Member.query.get_or_404(member_id)
    member_group_form = NotificationMemberGroupForm(member_id=member.id)

    if member_group_form.validate_on_submit():
        group_id = int(member_group_form.group.data)
        if group_id == 0:
            member_group_form.group.errors.append(
                _('Please select a group to add to the member.'))
        else:
            group = Group.query.get_or_404(group_id)
            if group not in member.groups:
                member.groups.append(group)
                db.session.add(member)
                db.session.commit()
            return redirect(url_for('notification.member_detail', member_id=member.id))

    member_update_form = MemberForm(obj=member)
    return render_template(
        'notification/site.member.html',
        member=member,
        member_update_form=member_update_form,
        member_group_form=member_group_form,
    )


@notification_bp.route('/members/<int:member_id>/remove_group/<int:group_id>', methods=['GET'])
@login_required
@check_permissions(['notification.member.update'])
def remove_group_from_member(member_id, group_id):
    """Remove a notification group from a member."""
    member = Member.query.get_or_404(member_id)
    group = Group.query.get_or_404(group_id)
    if group in member.groups:
        member.groups.remove(group)
        db.session.commit()
    return redirect(url_for('notification.member_detail', member_id=member.id))


@notification_bp.route('/members/<int:member_id>/delete', methods=['GET'])
@login_required
@check_permissions(['notification.member.delete'])
def member_delete(member_id):
    member = Member.query.get_or_404(member_id)

    for event_participant in list(member.events):
        db.session.delete(event_participant)

    for event in Event.query.filter_by(created_by=member.id).all():
        event.created_by = None

    member.groups.clear()
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for('notification.members_view'))


@notification_bp.route('/working-hours')
@login_required
@check_permissions(['notification.workinghours.view'])
def working_hours_view():
    # Pagination parameters
    try:
        page = int(request.args.get('page', 1))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 25))
    except Exception:
        per_page = 25

    # Filters
    member_id = request.args.get('member_id', type=int)
    date_str = request.args.get('date')

    query = WorkingHoursLog.query
    if member_id:
        query = query.filter(WorkingHoursLog.member_id == member_id)
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(func.date(WorkingHoursLog.date) == date_obj)
        except Exception:
            # ignore invalid date filter
            pass

    pagination = query.order_by(WorkingHoursLog.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    logs = pagination.items

    form = WorkingHoursForm()
    members = Member.query.order_by(Member.last_name, Member.first_name).all()

    return render_template(
        'notification/site.working_hours.html',
        logs=logs,
        form=form,
        pagination=pagination,
        members=members,
        filters={
            'member_id': member_id,
            'date': date_str,
            'per_page': per_page,
        },
    )


@notification_bp.route('/working-hours/dashboard')
@login_required
@check_permissions(['notification.workinghours.view'])
def working_hours_dashboard():
    """Dashboard with working-hours statistics and trends."""
    now = datetime.utcnow()
    current_year = now.year
    current_month = now.month

    logs = WorkingHoursLog.query.order_by(WorkingHoursLog.date.desc()).all()

    total_entries = len(logs)
    total_hours = float(sum((log.hours or 0) for log in logs))
    total_hours_this_month = float(sum(
        (log.hours or 0)
        for log in logs
        if log.date.year == current_year and log.date.month == current_month
    ))
    total_hours_this_year = float(sum(
        (log.hours or 0)
        for log in logs
        if log.date.year == current_year
    ))
    average_hours_per_entry = float(
        total_hours / total_entries) if total_entries else 0.0
    unique_members = len(
        {log.member_id for log in logs if log.member_id is not None})

    hours_by_member = defaultdict(float)
    entries_by_member = defaultdict(int)
    for log in logs:
        if log.member:
            member_label = f'{log.member.first_name} {log.member.last_name}'
        else:
            member_label = _('Unknown member')
        hours_by_member[member_label] += float(log.hours or 0)
        entries_by_member[member_label] += 1

    top_members = sorted(
        hours_by_member.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:5]

    monthly_hours_map = {month: 0.0 for month in range(1, 13)}
    for log in logs:
        if log.date.year == current_year:
            monthly_hours_map[log.date.month] += float(log.hours or 0)

    month_labels = [
        datetime(current_year, month, 1).strftime('%b')
        for month in range(1, 13)
    ]
    monthly_hours = [float(monthly_hours_map[month]) for month in range(1, 13)]

    recent_logs = logs[:10]

    return render_template(
        'notification/site.working_hours.dashboard.html',
        total_entries=total_entries,
        total_hours=total_hours,
        total_hours_this_month=total_hours_this_month,
        total_hours_this_year=total_hours_this_year,
        average_hours_per_entry=average_hours_per_entry,
        unique_members=unique_members,
        top_members=top_members,
        month_labels=month_labels,
        monthly_hours=monthly_hours,
        recent_logs=recent_logs,
    )


@notification_bp.route('/working-hours/create', methods=['GET', 'POST'])
@login_required
@check_permissions(['notification.workinghours.create'])
def working_hours_create():
    form = WorkingHoursForm()
    if form.validate_on_submit():
        if form.member.data == 0:
            form.member.errors.append(_('Please select a member'))
        else:
            log = WorkingHoursLog(
                member_id=form.member.data,
                date=form.date.data,
                hours=form.hours.data,
                created_by=current_user.id,
            )
            db.session.add(log)
            db.session.commit()
            flash(_('Working hours entry created.'), 'success')
            return redirect(url_for('notification.working_hours_view'))

    return render_template('notification/site.working_hours.form.html', form=form)


@notification_bp.route('/working-hours/<int:log_id>/edit', methods=['GET', 'POST'])
@login_required
@check_permissions(['notification.workinghours.update'])
def working_hours_edit(log_id):
    log = WorkingHoursLog.query.get_or_404(log_id)
    form = WorkingHoursForm(obj=log)
    # set member field explicitly
    form.member.data = log.member_id

    if form.validate_on_submit():
        if form.member.data == 0:
            form.member.errors.append(_('Please select a member'))
        else:
            log.member_id = form.member.data
            log.date = form.date.data
            log.hours = form.hours.data
            db.session.add(log)
            db.session.commit()
            flash(_('Working hours entry updated.'), 'success')
            return redirect(url_for('notification.working_hours_view'))

    return render_template('notification/site.working_hours.form.html', form=form, log=log)


@notification_bp.route('/working-hours/<int:log_id>/delete', methods=['GET'])
@login_required
@check_permissions(['notification.workinghours.delete'])
def working_hours_delete(log_id):
    log = WorkingHoursLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash(_('Working hours entry deleted.'), 'success')
    return redirect(url_for('notification.working_hours_view'))


@notification_bp.route('/working-hours/import', methods=['GET', 'POST'])
@login_required
@check_permissions(['notification.workinghours.create'])
def import_working_hours():
    """Import working hours from an uploaded CSV file."""
    form = WorkingHoursImportForm()

    if form.validate_on_submit():
        uploaded = request.files.get('csv_file')
        if not uploaded:
            form.csv_file.errors.append(_('No file uploaded.'))
            return render_template('notification/site.import_working_hours.html', form=form)

        try:
            raw_data = uploaded.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            form.csv_file.errors.append(
                _('Invalid CSV file encoding. Use UTF-8.'))
            return render_template('notification/site.import_working_hours.html', form=form)

        if not raw_data.strip():
            form.csv_file.errors.append(_('The CSV file is empty.'))
            return render_template('notification/site.import_working_hours.html', form=form)

        sample = raw_data[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(io.StringIO(raw_data), dialect=dialect)
        expected_fields = {
            'member_number',
            'date',
            'hours',
        }

        if not reader.fieldnames:
            form.csv_file.errors.append(
                _('The CSV file is missing a header row.'))
            return render_template('notification/site.import_working_hours.html', form=form)

        normalized_fieldnames = {
            _normalize_csv_header(fieldname) for fieldname in reader.fieldnames
        }
        if not expected_fields.issubset(normalized_fieldnames):
            form.csv_file.errors.append(_(
                'The CSV file must contain the columns: member_number, date, and hours.'
            ))
            return render_template('notification/site.import_working_hours.html', form=form)

        members_by_number = {
            member.member_number: member
            for member in Member.query.filter(Member.member_number.isnot(None)).all()
        }

        imported_count = 0
        for row_number, row in enumerate(reader, start=2):
            normalized_row = {
                _normalize_csv_header(key): _normalize_csv_value(value)
                for key, value in row.items()
            }

            member_number = normalized_row.get('member_number')
            if not member_number:
                continue

            member = members_by_number.get(member_number)
            if member is None:
                form.csv_file.errors.append(_(
                    f'Row {row_number}: unknown member_number "{member_number}".'
                ))
                return render_template('notification/site.import_working_hours.html', form=form)

            date_value = _parse_member_import_date(normalized_row.get('date'))
            if date_value is None:
                form.csv_file.errors.append(_(
                    f'Row {row_number}: invalid date value.'
                ))
                return render_template('notification/site.import_working_hours.html', form=form)

            hours_value = _parse_member_import_required_hours(
                normalized_row.get('hours'))
            if hours_value is None:
                form.csv_file.errors.append(_(
                    f'Row {row_number}: invalid hours value.'
                ))
                return render_template('notification/site.import_working_hours.html', form=form)

            db.session.add(WorkingHoursLog(
                member_id=member.id,
                date=date_value,
                hours=hours_value,
                created_by=current_user.id,
            ))
            imported_count += 1

        if imported_count == 0:
            form.csv_file.errors.append(
                _('The CSV file does not contain any valid working hours rows.'))
            return render_template('notification/site.import_working_hours.html', form=form)

        db.session.commit()

        return redirect(url_for(
            'notification.working_hours_view',
            imported_count=imported_count,
        ))

    return render_template('notification/site.import_working_hours.html', form=form)


@notification_bp.route('/working-hours/import/template', methods=['GET'])
@login_required
@check_permissions(['notification.workinghours.create'])
def download_working_hours_import_template():
    """Download an empty working-hours import CSV with the required headers."""
    response = Response(
        _build_working_hours_import_template_csv(),
        mimetype='text/csv; charset=utf-8',
    )
    response.headers['Content-Disposition'] = 'attachment; filename=working_hours_import_template.csv'
    return response
