""" This script seeds the database with initial data for permissions, roles, groups, and users. """

from app import create_app, db
from app.model.model import AuthPermission, AuthRole, AuthGroup, User, TriggerType


PERMISSIONS = [
    # * Admin Permissions
    {"name": "admin.backend.access", "description": "Access admin backend"},

    {"name": "admin.roles.read", "description": "Read roles"},
    {"name": "admin.role.read", "description": "Read role"},
    {"name": "admin.role.create", "description": "Create role"},
    {"name": "admin.role.update", "description": "Update role"},
    {"name": "admin.role.delete", "description": "Delete role"},
    {"name": "admin.role.update_permission",
        "description": "Grant and revoke permissions to role"},

    {"name": "admin.groups.read", "description": "Read groups"},
    {"name": "admin.group.read", "description": "Read group"},
    {"name": "admin.group.create", "description": "Create group"},
    {"name": "admin.group.update", "description": "Update group"},
    {"name": "admin.group.delete", "description": "Delete group"},
    {"name": "admin.group.assign_role", "description": "Assign role to group"},
    {"name": "admin.group.remove_role", "description": "Remove role from group"},

    {"name": "admin.users.read", "description": "Read users"},
    {"name": "admin.user.read", "description": "Read user"},
    {"name": "admin.user.create", "description": "Create user"},
    {"name": "admin.user.update", "description": "Update user"},
    {"name": "admin.user.delete", "description": "Delete user"},
    {"name": "admin.user.password.change", "description": "Change user password"},
    {"name": "admin.membership.assign", "description": "Assign user to group"},
    {"name": "admin.membership.remove", "description": "Remove user from group"},

    {"name": "admin.permissions.grant", "description": "Grant permissions to user"},
    {"name": "admin.permissions.revoke",
        "description": "Revoke permissions from user"},
    {"name": "admin.permissions.view", "description": "View user permissions"},



    {"name": "notification.view", "description": "View notifications"},
    {"name": "notification.members.read",
        "description": "Read notification members"},
    {"name": "notification.member.read", "description": "Read notification member"},
    {"name": "notification.member.create",
        "description": "Create notification member"},
    {"name": "notification.member.update",
        "description": "Update notification member"},
    {"name": "notification.member.delete",
        "description": "Delete notification member"},

    {"name": "notification.groups.view", "description": "Read notification groups"},
    {"name": "notification.group.read", "description": "View notification groups"},
    {"name": "notification.group.create",
        "description": "Create notification group"},
    {"name": "notification.group.update",
        "description": "Update notification group"},
    {"name": "notification.group.delete",
        "description": "Delete notification group"},

    {"name": "notification.templates.view",
        "description": "View notification templates"},
    {"name": "notification.template.read",
        "description": "Read notification template"},
    {"name": "notification.template.create",
        "description": "Create notification template"},
    {"name": "notification.template.update",
        "description": "Update notification template"},
    {"name": "notification.template.delete",
        "description": "Delete notification template"},

    {"name": "notification.events.view", "description": "View notification events"},
    {"name": "notification.event.read", "description": "Read notification event"},
    {"name": "notification.event.create",
        "description": "Create notification event"},
    {"name": "notification.event.update",
        "description": "Update notification event"},
    {"name": "notification.event.delete",
        "description": "Delete notification event"},

    {"name": "notification.logs.read", "description": "View notification logs"},
    {"name": "notification.logs.delete", "description": "Delete notification logs"},

    {"name": "notification.rules.view", "description": "View notification rules"},
    {"name": "notification.rule.read", "description": "Read notification rule"},
    {"name": "notification.rule.create", "description": "Create notification rule"},
    {"name": "notification.rule.update", "description": "Update notification rule"},
    {"name": "notification.rule.delete", "description": "Delete notification rule"},

]


ROLES = [
    {
        "name": "admin",
        "description": "Administrator role [DO NOT DELETE]",
        "permissions": [
            "admin.backend.access",

            "admin.roles.read",
            "admin.role.read",
            "admin.role.create",
            "admin.role.update",
            "admin.role.delete",
            "admin.role.update_permission",

            "admin.groups.read",
            "admin.group.read",
            "admin.group.create",
            "admin.group.update",
            "admin.group.delete",
            "admin.group.assign_role",
            "admin.group.remove_role",

            "admin.users.read",
            "admin.user.read",
            "admin.user.create",
            "admin.user.update",
            "admin.user.delete",
            "admin.user.password.change",
            "admin.membership.assign",
            "admin.membership.remove",

            "admin.permissions.grant",
            "admin.permissions.revoke",
            "admin.permissions.view",

            "notification.view",
            "notification.members.read",
            "notification.member.read",
            "notification.member.create",
            "notification.member.update",
            "notification.member.delete",

            "notification.groups.view",
            "notification.group.read",
            "notification.group.create",
            "notification.group.update",
            "notification.group.delete",

            "notification.templates.view",
            "notification.template.read",
            "notification.template.create",
            "notification.template.update",
            "notification.template.delete",

            "notification.events.view",
            "notification.event.read",
            "notification.event.create",
            "notification.event.update",
            "notification.event.delete",

            "notification.logs.read",
            "notification.logs.delete",

            "notification.rules.view",
            "notification.rule.read",
            "notification.rule.create",
            "notification.rule.update",
            "notification.rule.delete",
        ]
    },
    {
        "name": "user",
        "description": "Standard user role [DO NOT DELETE]",
        "permissions": [

        ]
    }
]

GROUPS = [
    {
        "name": "Admin",
        "description": "Administrative group [DO NOT DELETE]",
        "roles": ["admin"]
    },
    {
        "name": "User",
        "description": "Standard user group [DO NOT DELETE]",
        "roles": ["user"]
    }
]

USERS = [
    {
        "username": "admin",
        "password": "Starten1!",
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.org"
    }
]

CATEGORY_COLORS = [
    {"name": "Blue",        "color": "primary"},
    {"name": "Gray",        "color": "secondary"},
    {"name": "Green",       "color": "success"},
    {"name": "Red",         "color": "danger"},
    {"name": "Yellow",      "color": "warning"},
    {"name": "Light Blue",  "color": "info"},
    {"name": "Black",       "color": "dark"}
]

CATEGORIES = [
]

TRIGGER_TYPES = [
    {
        "code": "EVENT_START",
        "description": "Zeit vor dem Termin",
    },
    {
        "code": "BIRTHDAY",
        "description": "Geburtstag",
    },
    {
        "code": "MEMBER_ANNIVERSARY",
        "description": "Mitgliedszeit",
    },
]


def seed_permissions():
    """ Seed the database with initial permissions. """
    for perm_data in PERMISSIONS:
        if not AuthPermission.query.filter_by(name=perm_data["name"]).first():
            p = AuthPermission(**perm_data)
            db.session.add(p)
    db.session.commit()


def seed_roles():
    """ Seed the database with initial roles and assign permissions to them. """
    for role_data in ROLES:
        role = AuthRole.query.filter_by(name=role_data["name"]).first()
        if not role:
            role = AuthRole(name=role_data["name"],
                            description=role_data["description"])
            db.session.add(role)
            db.session.commit()

        # Berechtigungen zuweisen
        for perm_name in role_data["permissions"]:
            perm = AuthPermission.query.filter_by(name=perm_name).first()
            if perm and perm not in role.permissions:
                role.permissions.append(perm)
        db.session.commit()


def seed_groups():
    """ Seed the database with initial groups and assign roles to them. """
    for group_data in GROUPS:
        group = AuthGroup.query.filter_by(name=group_data["name"]).first()
        if not group:
            group = AuthGroup(name=group_data["name"],
                              description=group_data["description"])
            db.session.add(group)
            db.session.commit()

        for role_name in group_data["roles"]:
            role = AuthRole.query.filter_by(name=role_name).first()
            if role and role not in group.roles:
                group.roles.append(role)
        db.session.commit()


def seed_trigger_types():
    """Seed the database with the built-in notification trigger types."""
    for trigger_data in TRIGGER_TYPES:
        trigger_type = TriggerType.query.filter_by(
            code=trigger_data["code"]).first()
        if not trigger_type:
            trigger_type = TriggerType(**trigger_data)
            db.session.add(trigger_type)
        else:
            trigger_type.description = trigger_data["description"]
        db.session.commit()


def seed_users():
    """ Seed the database with initial users and assign them to groups. """
    for user_data in USERS:
        user = User.query.filter_by(username=user_data["username"]).first()
        if not user:
            user = User(username=user_data["username"],
                        email=user_data["email"],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name']
                        )
            user.set_password(user_data["password"])
            db.session.add(user)
            db.session.commit()

        admin_group = AuthGroup.query.filter_by(name="Admin").first()
        if admin_group and user not in admin_group.users:
            admin_group.users.append(user)
            db.session.commit()


def run_seeding():
    """ Run all seeding functions to populate the database with initial data. """
    print("Seeding permissions...")
    seed_permissions()
    print("Seeding roles...")
    seed_roles()
    print("Seeding groups...")
    seed_groups()
    print("Seeding trigger types...")
    seed_trigger_types()
    print("Seeding users...")
    seed_users()


app = create_app()


with app.app_context():
    db.create_all()
    run_seeding()
