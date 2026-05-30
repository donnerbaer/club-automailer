"""ORM models used by the application.

This module defines the main data models (Member, User, Group, Role,
Permission, templates, etc.) and basic helper methods used across the app.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Time,
)
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """ User model for storing user information """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    # For user profile image
    image_filename = db.Column(db.String(256), nullable=True)

    def set_password(self, password) -> None:
        """ Set the user's password by hashing it.

        Args:
            password (str): The plaintext password to be hashed and stored.

        Returns:
            None
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """ Check if the provided password matches the stored password hash.

        Args:
            password (str): The plaintext password to check against the stored hash.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission_name: str) -> bool:
        """ Check if the user has a specific permission.
        This method checks if the user belongs to any group that has the specified permission.
        This is done by iterating through the user's groups and their roles to find the permission.

        Args:
            permission_name (str): The name of the permission to check.

        Returns:
            bool: True if the user has the permission, False otherwise.
        """
        for group in self.groups:
            for role in group.roles:
                if any(permission.name == permission_name for permission in role.permissions):
                    return True
        return False


# Association Tables
role_permission = db.Table(
    'role_permission',
    db.Column('role_id', db.Integer, db.ForeignKey(
        'auth_roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey(
        'auth_permissions.id'), primary_key=True)
)

group_role = db.Table(
    'group_role',
    db.Column('group_id', db.Integer, db.ForeignKey(
        'auth_groups.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey(
        'auth_roles.id'), primary_key=True)
)

group_user = db.Table(
    'group_user',
    db.Column('group_id', db.Integer, db.ForeignKey(
        'auth_groups.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey(
        'users.id'), primary_key=True)
)


class AuthPermission(db.Model):
    """ Model representing a permission in the system. """
    __tablename__ = 'auth_permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Permission #{self.id} {self.name}>"


class AuthRole(db.Model):
    """ Model representing a role in the system. """
    __tablename__ = 'auth_roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    permissions = db.relationship(
        'AuthPermission', secondary='role_permission', backref='roles')

    def __repr__(self):
        return f"<Role #{self.id} {self.name}>"

    def add_permission(self, permission: AuthPermission) -> None:
        """ Add a permission to the role.

        Args:
            permission (AuthPermission): The permission to be added to the role.

        Returns:
            None
        """
        self.permissions.append(permission)
        db.session.commit()

    def remove_permission(self, permission: AuthPermission) -> None:
        """ Remove a permission from the role.

        Args:
            permission (AuthPermission): The permission to be removed from the role.

        Returns:
            None
        """
        self.permissions.remove(permission)
        db.session.commit()

    def has_permission(self, permission_name: str) -> bool:
        """ Check if the role has a specific permission by name.
        This method checks if the role has a permission with the given name.

        Args:
            permission_name (str): The name of the permission to check.

        Returns:
            bool: True if the role has the permission, False otherwise.
        """
        return any(permission.name == permission_name for permission in self.permissions)

    def add_role(self, role: 'Role') -> None:
        """ Add a role to the group.
        This method checks if the role is already associated with the group before adding it.

        Args:
            role (Role): The role to be added to the group.

        Returns:
            None
        """
        if not self.has_role(role.name):
            self.roles.append(role)
            db.session.commit()

    def has_role(self, role_name: str) -> bool:
        """ Check if the group has a specific role by name.
        This method checks if the group has a role with the given name.

        Args:
            role_name (str): The name of the role to check.

        Returns:
            bool: True if the group has the role, False otherwise.
        """
        return any(role.name == role_name for role in self.roles)


class AuthGroup(db.Model):
    """ Model representing a group of users in the system. """
    __tablename__ = 'auth_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    roles = db.relationship(
        'AuthRole', secondary='group_role', backref='groups')
    users = db.relationship(
        'User', secondary='group_user', backref='groups')

    def __repr__(self):
        return f"<Group #{self.id} {self.name}>"

    def add_role(self, role: AuthRole) -> None:
        """ Add a role to the group.
        This method checks if the role is already associated with the group before adding it.

        Args:
            role (AuthRole): The role to be added to the group.

        Returns:
            None
        """
        if not self.has_role(role.name):
            self.roles.append(role)
            db.session.commit()

    def remove_role(self, role: AuthRole) -> None:
        """ Remove a role from the group.
        This method checks if the role is associated with the group before removing it.

        Args:
            role (AuthRole): The role to be removed from the group.

        Returns:
            None
        """
        if self.has_role(role.name):
            self.roles.remove(role)
            db.session.commit()

    def create(self, name: str) -> Optional['AuthGroup']:
        """ Create a new group with the given name.
        This method checks if a group with the same name already exists before creating a new one.

        Args:
            name (str): The name of the group to be created.

        Returns:
            Optional[AuthGroup]: The newly created group if it does not already exist, None
            otherwise.
        """
        if not self.is_group_exists(name):
            new_group = AuthGroup(name=name)
            db.session.add(new_group)
            db.session.commit()
            return new_group
        return None

    def has_role(self, role_name: str) -> bool:
        """ Check if the group has a specific role by name.

        Args:
            role_name (str): The name of the role to check.

        Returns:
            bool: True if the group has the role, False otherwise.
        """
        return any(role.name == role_name for role in self.roles)

    def is_group_exists(self, name: str) -> bool:
        """ Check if a group with the given name already exists.

        Args:
            name (str): The name of the group to check.

        Returns:
            bool: True if a group with the name exists, False otherwise.
        """
        return db.session.query(Group).filter_by(name=name).first() is not None

    def delete(self) -> None:
        """ Delete the group from the database.
        This method removes the group from the database and commits the changes.
        It does not check for any dependencies or associations before deletion, so use with caution.
        """
        db.session.delete(self)
        db.session.commit()


# Association table for members <-> groups
group_members = db.Table(
    "group_members",
    db.Column("group_id", db.Integer, db.ForeignKey(
        "groups.id"), primary_key=True),
    db.Column("member_id", db.Integer, db.ForeignKey(
        "members.id"), primary_key=True),
    db.Column("added_at", db.DateTime, default=datetime.utcnow),
)


class Member(db.Model):
    """ Model representing a member in the system. """
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    member_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    birth_date = Column(Date)
    join_date = Column(Date)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    required_hours = Column(Float, default=0)

    groups = relationship("Group", secondary=group_members,
                          back_populates="members")
    events = relationship("EventParticipant", back_populates="member")
    working_hours_logs = relationship(
        "WorkingHoursLog",
        back_populates="member",
        cascade="all, delete-orphan",
    )


class Group(db.Model):
    """ Model representing a group of members. """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    members = relationship(
        "Member", secondary=group_members, back_populates="groups")


class Event(db.Model):
    """ Model representing an event in the system. """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(String(50), nullable=False)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime)
    location = Column(String(255))
    created_by = Column(Integer, ForeignKey("members.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # For recurring events (e.g., every Tuesday 19:00)
    is_recurring = Column(Boolean, nullable=False, default=False)
    recurrence_pattern = Column(String(50))  # WEEKLY, MONTHLY, etc.
    recurrence_weekday = Column(Integer)  # 0=Monday, ..., 6=Sunday
    recurrence_count = Column(Integer)  # Number of occurrences
    recurrence_group_id = Column(Integer)  # Links events in a series together

    participants = relationship(
        "EventParticipant",
        back_populates="event",
        cascade="all, delete-orphan",
    )
    logs = relationship(
        "NotificationLog",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventParticipant(db.Model):
    """ Model representing the association between members and events,
    including their participation status.
    """
    __tablename__ = "event_participants"

    event_id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), primary_key=True)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    event = relationship("Event", back_populates="participants")
    member = relationship("Member", back_populates="events")


class NotificationTemplate(db.Model):
    """ Model representing a notification template used for sending emails. """
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True)
    code = Column(String(100), unique=True, nullable=False)
    subject_template = Column(Text, nullable=False)
    body_template = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class TriggerType(db.Model):
    """ Model representing a type of trigger for notifications, such as 'birthday'
    or 'work_assignment'.
    """
    __tablename__ = "trigger_types"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)


class NotificationRule(db.Model):
    """ Model representing a notification rule that defines when and how notifications
    should be sent.
    """
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    trigger_type = Column(Integer, ForeignKey("trigger_types.id"))
    days_before = Column(Integer)
    # For triggers that need a numeric parameter (e.g. age or membership years)
    trigger_value = Column(Integer)
    send_time = Column(Time, default="08:00")
    template_id = Column(Integer, ForeignKey("notification_templates.id"))
    # Recurring scheduling fields
    # None, "monthly", "yearly"
    recurrence_type = Column(String(50), nullable=True)
    # Day of month (1-31) for monthly recurrence
    recurrence_day = Column(Integer, nullable=True)
    # Month (1-12) for yearly recurrence
    recurrence_month = Column(Integer, nullable=True)
    # Day of month (1-31) for yearly recurrence
    recurrence_day_yearly = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    receivers = relationship("NotificationRuleReceiver", back_populates="rule")


class NotificationRuleReceiver(db.Model):
    """ Model representing the recipients of a notification rule, which can be groups or
    custom email addresses.
    """
    __tablename__ = "notification_rule_receivers"

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("notification_rules.id"))
    receiver_type = Column(String(50), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    custom_email = Column(String(255))

    rule = relationship("NotificationRule", back_populates="receivers")


class NotificationLog(db.Model):
    """ Model representing a log entry for sent notifications, including status
    and any error messages.
    """
    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("notification_rules.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    event_title = Column(String(255))
    recipient_email = Column(String(255), nullable=False)
    subject = Column(Text)
    body = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), nullable=False)
    error_message = Column(Text)

    event = relationship("Event", back_populates="logs")


class WorkingHoursLog(db.Model):
    """ Model representing a working hours entry for a member.
    Each entry represents one shift/assignment.
    """
    __tablename__ = "working_hours_log"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    date = Column(Date, nullable=False)
    hours = Column(Float, default=0)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    member = relationship("Member", back_populates="working_hours_logs")
    created_by_user = relationship("User")
