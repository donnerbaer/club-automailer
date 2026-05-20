""" Flask-WTF forms. """

from typing import List
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    FileField,
    BooleanField,
    IntegerField,
    SelectField,
    RadioField,
    TextAreaField,
    DateField,
    DateTimeField,
    TimeField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    NumberRange,
)
from flask_babel import lazy_gettext as _l, gettext as _
from app.model.model import (
    User,
    Member,
    Group,
    Event,
    NotificationTemplate,
    TriggerType,
    AuthRole,
    AuthPermission,
)


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    submit = SubmitField(_l('Login'))


class SearchForm(FlaskForm):
    """Form for searching items."""
    query = StringField(
        _l('Search'),
        validators=[
            DataRequired(), Length(max=4095)
        ]
    )
    submit = SubmitField(_l('Search'))


class RegistrationForm(FlaskForm):
    """Form for user registration."""
    username = StringField(
        _l('Username'),
        validators=[DataRequired(), Length(min=3, max=64)]
    )
    email = StringField(
        _l('Email'),
        validators=[DataRequired(), Email(), Length(min=6, max=120)]
    )
    password = PasswordField(
        _l('Password'),
        validators=[
            DataRequired(),
            Length(min=12, message=_l(
                'Password must be at least 12 characters long')),
        ]
    )
    confirm_password = PasswordField(
        _l('Confirm Password'),
        validators=[DataRequired(), EqualTo(
            'password', message=_l('Passwords must match'))
        ]
    )
    first_name = StringField(
        _l('First Name'),
        validators=[Optional(), Length(max=64)]
    )
    last_name = StringField(
        _l('Last Name'),
        validators=[Optional(), Length(max=64)]
    )
    submit = SubmitField(_l('Create Account'))


class UserUpdateForm(FlaskForm):
    """Form for updating user profile."""
    username = StringField(
        _l('Username'),
        validators=[
            Optional(), Length(min=3, max=64)
        ]
    )
    email = StringField(
        _l('Email'),
        validators=[
            Optional(), Email(), Length(min=6, max=120)
        ]
    )
    first_name = StringField(
        _l('First Name'),
        validators=[
            Optional(), Length(max=64)
        ]
    )
    last_name = StringField(
        _l('Last Name'),
        validators=[
            Optional(), Length(max=64)
        ]
    )
    image = FileField(
        _l('Profile Image Filename'),
        validators=[
            Optional()
        ]
    )  # For user profile image
    delete_image = BooleanField(
        _l('Delete Profile Image'),
        default=False,
        validators=[
            Optional()
        ]
    )
    old_password = PasswordField(
        _l('Old Password'),
        validators=[
            DataRequired(), Length(min=8)
        ]
    )
    new_password = PasswordField(
        _l('New Password'),
        validators=[
            Optional(), Length(min=8)
        ]
    )
    confirm_password = PasswordField(
        _l('Confirm Password'),
        validators=[
            Optional(), EqualTo('new_password')
        ]
    )
    submit = SubmitField(_l('Save Changes'))


class AuthRoleCreateForm(FlaskForm):
    """Form for creating a new role."""
    name = StringField(_l('Role Name'), validators=[
                       DataRequired(), Length(max=50)])
    description = TextAreaField(_l('Description'), validators=[
                                Optional(), Length(max=255)])
    submit = SubmitField(_l('Create Role'))


class AuthRoleUpdateForm(FlaskForm):
    """Form for updating an existing role."""
    name = StringField(_l('Role Name'), validators=[
                       DataRequired(), Length(max=50)])
    description = TextAreaField(_l('Description'), validators=[
                                Optional(), Length(max=255)])
    submit = SubmitField(_l('Update Role'))


class AuthGroupCreateForm(FlaskForm):
    """Form for creating a new group."""
    name = StringField(_l('Group Name'), validators=[
                       DataRequired(), Length(max=50)])
    description = TextAreaField(_l('Description'), validators=[
                                Optional(), Length(max=255)])
    submit = SubmitField(_l('Create Group'))


class AuthGroupUpdateForm(FlaskForm):
    """Form for updating an existing group."""
    name = StringField(_l('Group Name'), validators=[
                       DataRequired(), Length(max=50)])
    description = TextAreaField(_l('Description'), validators=[
                                Optional(), Length(max=255)])
    submit = SubmitField(_l('Update Group'))


def build_auth_role_permission_form(role: AuthRole, permissions: List[AuthPermission]) -> FlaskForm:
    """ Builds a dynamic form for role permissions.

    This function creates a FlaskForm subclass with radio fields for each permission
    associated with a role. Each permission can be set to 'Allow' or 'Deny'.

    Args:
        role (Role): The role for which permissions are being managed.
        permissions (list): A list of Permission objects to create fields for.
    """
    class DynamicRolePermissionForm(FlaskForm):
        """Dynamically generated form for role permissions.

        This form contains radio fields for each permission, allowing the user
        to set permissions for the specified role.

        Attributes:
            submit (SubmitField): A submit button to update permissions.
        """
        submit = SubmitField(_l('Update Permissions'))

    # Dynamically add fields for each permission
    for perm in permissions:
        field_name = f'perm_{perm.id}'
        default_value = 'allow' if perm in role.permissions else 'deny'

        field = RadioField(
            label=perm.name,
            choices=[
                ('allow', _l('Allow')),
                ('deny', _l('Deny'))
            ],
            default=default_value
        )

        # Set the name attribute for the field, which is used in the template.
        setattr(DynamicRolePermissionForm, field_name, field)

    return DynamicRolePermissionForm()


class AuthGroupMembershipForm(FlaskForm):
    """Form for managing group membership."""
    user = SelectField(_l('Choose an user'), choices=[],
                       coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Add to Group'))

    def __init__(self, *args, group_id=None, **kwargs):
        """Initialize the form with dynamic user choices.
        Args:
            group_id (int): The ID of the group to filter users.
        """
        super().__init__(*args, **kwargs)
        choices = [(0, _l('-- Please Choose --'))]
        if group_id:
            users = User.query.filter(~User.groups.any(id=group_id)).all()
        else:
            users = User.query.all()
        choices += [(user.id, user.username) for user in users]
        self.user.choices = choices


class AuthGroupAssignRoleForm(FlaskForm):
    """Form for assigning roles to a group."""
    role = SelectField(_l('Choose a role'), choices=[],
                       coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Assign Role'))

    def __init__(self, *args, group_id=None, **kwargs):
        """Initialize the form with dynamic role choices.
        Args:
            group_id (int): The ID of the group to filter roles.
        """
        super().__init__(*args, **kwargs)
        choices = [(0, _l('-- Please Choose --'))]
        if group_id:
            roles = AuthRole.query.filter(
                ~AuthRole.groups.any(id=group_id)).all()
        else:
            roles = AuthRole.query.all()
        choices += [(role.id, role.name) for role in roles]
        self.role.choices = choices


class NotificationGroupMembershipForm(FlaskForm):
    """Form for managing notification group membership."""
    member = SelectField(_l('Choose a member'), choices=[],
                         coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Add to Group'))

    def __init__(self, *args, group_id=None, **kwargs):
        """Initialize the form with dynamic member choices.
        Args:
            group_id (int): The ID of the group to filter members.
        """
        super().__init__(*args, **kwargs)
        choices = [(0, _l('-- Please Choose --'))]
        if group_id:
            members = Member.query.filter(
                ~Member.groups.any(id=group_id)).all()
        else:
            members = Member.query.all()
        choices += [(
            member.id,
            f"{member.first_name} {member.last_name} ({member.member_number})"
            if member.member_number else f"{member.first_name} {member.last_name}"
        ) for member in members]
        self.member.choices = choices


class NotificationMemberGroupForm(FlaskForm):
    """Form for assigning a notification group to a member."""
    group = SelectField(_l('Choose a group'), choices=[],
                        coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Add to Group'))

    def __init__(self, *args, member_id=None, **kwargs):
        """Initialize the form with dynamic group choices.

        Args:
            member_id (int): The ID of the member to filter groups.
        """
        super().__init__(*args, **kwargs)
        choices = [(0, _l('-- Please Choose --'))]
        if member_id:
            groups = Group.query.filter(~Group.members.any(id=member_id)).all()
        else:
            groups = Group.query.all()
        choices += [(group.id, group.name) for group in groups]
        self.group.choices = choices


class EventForm(FlaskForm):
    """Form for creating or updating an event."""
    title = StringField(_l('Title'), validators=[
                        DataRequired(), Length(max=255)])
    event_type = SelectField(
        _l('Trigger Type'),
        choices=[],
        validators=[DataRequired()],
    )
    description = TextAreaField(_l('Description'), validators=[
                                Optional(), Length(max=5000)])
    start_at = DateTimeField(
        _l('Start At'),
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()],
    )
    end_at = DateTimeField(
        _l('End At'),
        format='%Y-%m-%dT%H:%M',
        validators=[Optional()],
    )
    location = StringField(_l('Location'), validators=[
                           Optional(), Length(max=255)])
    is_recurring = BooleanField(_l('Recurring Event'), default=False)
    recurrence_pattern = SelectField(
        _l('Pattern'),
        choices=[
            ('DAILY', _l('Daily')),
            ('WEEKLY', _l('Weekly')),
            ('MONTHLY', _l('Monthly')),
        ],
        validators=[Optional()],
    )
    recurrence_weekday = SelectField(
        _l('Weekday'),
        choices=[
            ('0', _l('Monday')),
            ('1', _l('Tuesday')),
            ('2', _l('Wednesday')),
            ('3', _l('Thursday')),
            ('4', _l('Friday')),
            ('5', _l('Saturday')),
            ('6', _l('Sunday')),
        ],
        validators=[Optional()],
    )
    recurrence_count = IntegerField(_l('Number of Occurrences'), validators=[
                                    Optional(), NumberRange(min=1, max=52)])
    submit = SubmitField(_l('Save Event'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        trigger_choices = [(0, _l('-- Please Choose --'))]
        trigger_choices += [
            (trigger.code, trigger.description or trigger.code)
            for trigger in TriggerType.query.order_by(TriggerType.code.asc()).all()
        ]
        self.event_type.choices = trigger_choices


class EventCleanupForm(FlaskForm):
    """Form for deleting events older than a selected age."""
    age_value = IntegerField(_l('Age'), validators=[
        DataRequired(), NumberRange(min=1, max=1000)
    ])
    age_unit = SelectField(
        _l('Unit'),
        choices=[
            ('days', _l('Days')),
            ('months', _l('Months')),
            ('years', _l('Years')),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField(_l('Delete Old Events'))


class NotificationEventParticipantForm(FlaskForm):
    """Form for assigning a member to an event."""
    member = SelectField(_l('Choose a member'), choices=[],
                         coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Add to Event'))

    def __init__(self, *args, event_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(0, _l('-- Please Choose --'))]
        members = Member.query.all()
        if event_id:
            event = Event.query.get(event_id)
            if event is not None:
                participant_ids = {
                    participant.member_id for participant in event.participants}
                members = [
                    member for member in members if member.id not in participant_ids]
        choices += [(member.id, f'{member.first_name} {member.last_name}')
                    for member in members]
        self.member.choices = choices


class NotificationTemplateForm(FlaskForm):
    """Form for creating or updating notification templates."""
    code = StringField(_l('Code'), validators=[
                       DataRequired(), Length(max=100)])
    subject_template = TextAreaField(_l('Subject Template'), validators=[
                                     DataRequired(), Length(max=5000)])
    body_template = TextAreaField(_l('Body Template'), validators=[
                                  DataRequired(), Length(max=20000)])
    submit = SubmitField(_l('Save Template'))


class TriggerTypeForm(FlaskForm):
    """Form for creating or updating trigger types."""
    code = StringField(_l('Code'), validators=[DataRequired(), Length(max=50)])
    description = TextAreaField(_l('Description'), validators=[
                                Optional(), Length(max=5000)])
    submit = SubmitField(_l('Save Trigger Type'))


class NotificationRuleForm(FlaskForm):
    """Form for creating or updating notification rules."""
    name = StringField(_l('Name'), validators=[
                       DataRequired(), Length(max=255)])
    trigger_type = SelectField(
        _l('Trigger Type'), choices=[], coerce=int, validators=[DataRequired()])
    days_before = IntegerField(_l('Days Before'), validators=[
                               Optional(), NumberRange(min=0)])
    send_time = TimeField(_l('Send Time'), format='%H:%M',
                          validators=[DataRequired()])
    trigger_value = IntegerField(_l('Years'), validators=[
                                 Optional(), NumberRange(min=0)])
    template_id = SelectField(
        _l('Template'), choices=[], coerce=int, validators=[DataRequired()])
    active = BooleanField(_l('Active'), default=True)
    submit = SubmitField(_l('Save Rule'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        trigger_choices = [(0, _l('-- Please Choose --'))]
        trigger_choices += [
            (trigger.id, trigger.code)
            for trigger in TriggerType.query.order_by(TriggerType.code.asc()).all()
        ]
        self.trigger_type.choices = trigger_choices

        template_choices = [(0, _l('-- Please Choose --'))]
        template_choices += [
            (template.id, template.code)
            for template in NotificationTemplate.query.order_by(NotificationTemplate.code.asc()).all()
        ]
        self.template_id.choices = template_choices


class NotificationRuleReceiverForm(FlaskForm):
    """Form for adding receivers to a notification rule."""
    receiver_type = SelectField(
        _l('Receiver Type'),
        choices=[('group', _l('Group')), ('email', _l('Custom Email'))],
        validators=[DataRequired()],
    )
    group_id = SelectField(_l('Group'), choices=[],
                           coerce=int, validators=[Optional()])
    custom_email = StringField(_l('Custom Email'), validators=[
                               Optional(), Email(), Length(max=255)])
    submit = SubmitField(_l('Add Receiver'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group_choices = [(0, _l('-- Please Choose --'))]
        group_choices += [(group.id, group.name)
                          for group in Group.query.order_by(Group.name.asc()).all()]
        self.group_id.choices = group_choices


class MemberForm(FlaskForm):
    """Form for creating or updating a member."""
    member_number = StringField(
        _l('Member Number'),
        validators=[DataRequired(), Length(max=50)]
    )
    first_name = StringField(
        _l('First Name'),
        validators=[
            DataRequired(), Length(max=64)]
    )
    last_name = StringField(
        _l('Last Name'),
        validators=[DataRequired(), Length(max=64)]
    )
    email = StringField(
        _l('Email'),
        validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField(
        _l('Phone Number'),
        validators=[Optional(), Length(max=20)]
    )
    birth_date = DateField(
        _l('Birth Date'),
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    join_date = DateField(
        _l('Join Date'),
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    active = BooleanField(_l('Active'), default=True)
    submit = SubmitField(_l('Save Member'))


class NotificationLogCleanupForm(FlaskForm):
    """Form for deleting notification logs older than a selected age."""
    age_value = IntegerField(_l('Age'), validators=[
        DataRequired(), NumberRange(min=1, max=10000)
    ])
    age_unit = SelectField(
        _l('Unit'),
        choices=[
            ('days', _l('Days')),
            ('weeks', _l('Weeks')),
            ('months', _l('Months')),
            ('years', _l('Years')),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField(_l('Delete Old Logs'))


class NotificationLogClearForm(FlaskForm):
    """Form for clearing notification logs."""
    submit = SubmitField(_l('Clear Logs'))


class NotificationFailedLogClearForm(FlaskForm):
    """Form for clearing failed notification logs."""
    submit = SubmitField(_l('Clear Failed Logs'))
