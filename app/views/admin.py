from app.utils.decorators import check_permissions
from flask import Blueprint, render_template
from flask import redirect, url_for, request
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.model.model import User
from app.forms import (
    AuthGroupCreateForm,
    AuthGroupUpdateForm,
    AuthGroupMembershipForm,
    AuthGroupAssignRoleForm,
    build_auth_role_permission_form,
    AuthRoleCreateForm,
    AuthRoleUpdateForm
)
from app.model.model import (
    User,
    AuthRole,
    AuthGroup,
    AuthPermission
)


admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin',
    template_folder='templates/admin'
)


@admin_bp.route('/', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access'
])
def admin_view():
    """Render the admin site.

    Args:
        None

    Returns:
        Rendered template for the admin site.
    """
    return render_template('admin/site.index.html', current_user=current_user)


### * Roles Management ###


@admin_bp.route('/roles', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.roles.read'
])
def roles_view():
    """Render the roles management page.

    Args:
        None

    Returns:
        Rendered template for roles management.
    """
    roles = db.session.query(AuthRole).all()
    form_create_role = AuthRoleCreateForm()

    return render_template('admin/site.roles.html',
                           current_user=current_user,
                           roles=roles,
                           form_create_role=form_create_role
                           )


@admin_bp.route('/roles', methods=['POST'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.role.create'
])
def role_post():
    """Create a new role.

    Args:
        None

    Returns:
        Redirect to the roles management page.
    """
    form_create_role = AuthRoleCreateForm(request.form)
    if form_create_role.validate_on_submit():
        if not AuthRole.query.filter_by(name=form_create_role.name.data).first():
            new_role = AuthRole(
                name=form_create_role.name.data,
                description=form_create_role.description.data if form_create_role.description.data else None
            )
            db.session.add(new_role)
            db.session.commit()
        else:
            form_create_role.name.errors.append(_('Role name already exists.'))
    return redirect(url_for('admin.roles_view'))


@admin_bp.route('/roles/<int:role_id>', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.role.read'
])
def role_view(role_id):
    """ Render the role view page.

    Args:
        role_id (int): The ID of the role to be viewed.

    Returns:
        Rendered template for the role view.
    """
    role = AuthRole.query.get_or_404(role_id)
    permissions = db.session.query(AuthPermission).all()
    form_role_permissions = build_auth_role_permission_form(role, permissions)
    form_update_role = AuthRoleUpdateForm(obj=role)

    return render_template('admin/site.role.html',
                           current_user=current_user,
                           role=role,
                           permissions=permissions,
                           form_role_permissions=form_role_permissions,
                           form_update_role=form_update_role,
                           getattr=getattr
                           )


@admin_bp.route('/roles/<int:role_id>/add_permission', methods=['POST'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.role.update_permission'
])
def add_permission_to_role(role_id: int):
    """Add a permission to a role.

    Args:
        role_id (int): The ID of the role to which the permission will be added.

    Returns:
        Redirect to the role view page.
    """
    role = AuthRole.query.get_or_404(role_id)
    permissions = db.session.query(AuthPermission).all()
    form_role_permissions = build_auth_role_permission_form(role, permissions)

    if form_role_permissions.validate_on_submit():
        for permission in permissions:
            field_name = f'perm_{permission.id}'
            field_value = getattr(form_role_permissions, field_name).data
            if field_value == 'allow' and not permission.id in (perm.id for perm in role.permissions):
                role.add_permission(permission)
            elif field_value == 'deny' and permission.id in (perm.id for perm in role.permissions):
                role.remove_permission(permission)

        db.session.commit()

    return redirect(url_for('admin.role_view', role_id=role.id))


@admin_bp.route('/roles/<int:role_id>/update', methods=['POST'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.role.update'
])
def update_role(role_id):
    """ Update an existing role.

    Args:
        role_id (int): The ID of the role to be updated.

    Returns:
        Redirect to the role view page.
    """
    role = AuthRole.query.get_or_404(role_id)
    form_update_role = AuthRoleUpdateForm(request.form)

    if form_update_role.validate_on_submit():
        role.name = form_update_role.name.data
        role.description = form_update_role.description.data if form_update_role.description.data != '' else None

        db.session.add(role)
        db.session.commit()

    return redirect(url_for('admin.role_view', role_id=role.id))


@admin_bp.route('/roles/<int:role_id>/delete', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.role.delete'
])
def delete_role(role_id: int):
    """Delete a role by its ID.

    Args:
        role_id (int): The ID of the role to be deleted.

    Returns:
        Redirect to the roles management page.
    """
    role = AuthRole.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    return redirect(url_for('admin.roles_view'))


### * Groups Management ###


@admin_bp.route('/groups', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.groups.read'
])
def groups_view():
    """ Render the groups management page.

    Args:
        None

    Returns:
        Rendered template for groups management.
    """
    groups = db.session.query(AuthGroup).all()
    form_create_group = AuthGroupCreateForm(request.form)
    return render_template(
        'admin/site.groups.html',
        current_user=current_user,
        groups=groups,
        form_create_group=form_create_group
    )


@admin_bp.route('/groups', methods=['POST'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.group.create'
])
def create_group():
    """Create a new group.

    Args:
        None

    Returns:
        Redirect to the groups management page.
    """
    form = AuthGroupCreateForm(request.form)
    if not form.validate_on_submit():
        return redirect(url_for('admin.groups_view'))

    if not AuthGroup.query.filter_by(name=form.name.data).first():
        new_group = AuthGroup(
            name=form.name.data,
            description=form.description.data if form.description.data and form.description != '' else None
        )
        db.session.add(new_group)
        db.session.commit()
    return redirect(url_for('admin.groups_view'))


@admin_bp.route('/groups/<int:group_id>', methods=['GET', 'POST'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.group.read'
])
def group_view(group_id):
    """ Render the group view page.

    Args:
        group_id (int): The ID of the group to be viewed.

    Returns:
        Rendered template for the group view.
    """
    group = AuthGroup.query.get_or_404(group_id)
    form_update_group = AuthGroupUpdateForm(obj=group)
    form_membership = AuthGroupMembershipForm(group_id=group.id)
    form_assign_role = AuthGroupAssignRoleForm(group_id=group.id)

    if current_user.has_permission('admin.group.update'):
        if form_update_group.validate_on_submit():
            if AuthGroup.query.filter(AuthGroup.id != group.id, AuthGroup.name == form_update_group.name.data).first():
                form_update_group.name.errors.append(
                    _('Group name already exists.'))
            else:
                form_update_group.populate_obj(group)
                db.session.add(group)
                db.session.commit()

    return render_template('admin/site.group.html',
                           current_user=current_user,
                           group=group,
                           form_update_group=form_update_group,
                           form_membership=form_membership,
                           form_assign_role=form_assign_role
                           )


@admin_bp.route('/groups/<int:group_id>/delete', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.group.delete'
])
def delete_group(group_id: int):
    """Delete a group by its ID.

    Args:
        group_id (int): The ID of the group to be deleted.

    Returns:
        Redirect to the groups management page.
    """
    group = AuthGroup.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('admin.groups_view'))


@admin_bp.route('/groups/<int:group_id>/assign_role', methods=['POST'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.group.assign_role'
])
def assign_role_to_group(group_id: int):
    """Add a role to a group.

    Args:
        group_id (int): The ID of the group to which the role will be added.

    Returns:
        Redirect to the group view page.
    """
    group = AuthGroup.query.get_or_404(group_id)
    role = AuthRole.query.get_or_404(request.form.get('role'))
    group.add_role(role)
    return redirect(url_for('admin.group_view', group_id=group.id))


@admin_bp.route('/groups/<int:group_id>/remove_role/<int:role_id>', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.group.remove_role'
])
def remove_role_from_group(group_id: int, role_id: int):
    """Remove a role from a group.

    Args:
        group_id (int): The ID of the group from which the role will be removed.
        role_id (int): The ID of the role to be removed from the group. 

    Returns:
        Redirect to the group view page.
    """
    group = AuthGroup.query.get_or_404(group_id)
    role = AuthRole.query.get_or_404(role_id)
    group.remove_role(role)
    return redirect(url_for('admin.group_view', group_id=group.id))


@admin_bp.route('/groups/<int:group_id>/add_user', methods=['POST'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.membership.assign'
])
def add_user_to_group(group_id: int):
    """Add a user to a group.

    Args:
        group_id (int): The ID of the group to which the user will be added.

    Returns:
        Redirect to the group view page.
    """
    form = AuthGroupMembershipForm()
    if form.validate_on_submit():
        user_id = (int)(form.user.data)
        if user_id == 0 or user_id == '0':
            form.user.errors.append(
                _('Please select a user to add to the group.'))
            return redirect(url_for('admin.group_view', group_id=group_id))
        user = User.query.get_or_404(user_id)
        group = AuthGroup.query.get_or_404(group_id)
        group.users.append(user)
        db.session.add(group)
        db.session.commit()
    return redirect(url_for('admin.group_view', group_id=group_id))


@admin_bp.route('/groups/<int:group_id>/remove_user/<int:user_id>', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.membership.remove'
])
def remove_user_from_group(group_id: int, user_id: int):
    """Remove a user from a group.

    Args:
        group_id (int): The ID of the group from which the user will be removed.
        user_id (int): The ID of the user to be removed from the group.

    Returns:
        Redirect to the group view page.
    """
    group = AuthGroup.query.get_or_404(group_id)
    user = User.query.get_or_404(user_id)
    if user in group.users:
        group.users.remove(user)
        db.session.commit()
    return redirect(url_for('admin.group_view', group_id=group.id))


@admin_bp.route('/users', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access',
    'admin.users.read'
])
def view_users():
    """View all users.

    Args:
        None

    Returns:
        Rendered template with the list of users.
    """
    users = User.query.all()
    return render_template('admin/site.users.html', users=users)


@admin_bp.route('/check_version', methods=['GET'])
@login_required
@check_permissions([
    'admin.backend.access'
])
def check_version():
    """Check for updates to the application version.

    Args:
        None

    Returns:
        Redirect to the admin view page with a message indicating the version check.
    """
    from packaging import version
    import requests
    from version import get_version

    response = requests.get(
        "https://api.github.com/repos/donnerbaer/email-notificator-tool/releases/latest"
    )
    current_version = version.parse(get_version())
    latest_version = version.parse(response.json().get("tag_name"))

    version_info = {
        'current_version': current_version,
        'latest_version': latest_version,
        'update_available': current_version < latest_version
    }

    return render_template(
        'admin/site.index.html',
        current_user=current_user,
        version_info=version_info
    )
