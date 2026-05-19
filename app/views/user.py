""" This module handles the user views of the application."""

import os
from uuid import uuid4
from flask import Blueprint, render_template, url_for
from flask import redirect, flash, request
from flask_babel import gettext as _, lazy_gettext
from flask_login import login_required, current_user
from app import db
from app.forms import UserUpdateForm
from app.model.model import User
from app.utils.image import is_image_name_valid, get_default_user_image
from app.utils.decorators import check_permissions, check_own_or_has_permissions


user_bp = Blueprint('user', __name__)


@user_bp.route('/users', methods=['GET'])
@login_required
def users_view():
    """ Render the users page.

    Returns:
        Rendered template for the users page with a list of users.
    """
    users = db.session.query(User).all()
    return render_template('site.users.html',
                           current_user=current_user,
                           users=users
                           )


@user_bp.route('/users', methods=['POST'])
@login_required
@check_permissions([
    'admin.user.create'
])
def create_user():
    """ Handle the creation of a new user, for already logged-in users.
    This function checks if the passwords match, if the username and email are unique,
    and then creates a new user in the database.
    If any validation fails, it flashes an error message and redirects to the users page.

    Returns:
        Redirect to the users page after successful creation.
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash(lazy_gettext('Passwords do not match'))
            return redirect(url_for('user.users_view'))
        if db.session.query(User).filter_by(username=form.username.data).first():
            flash(lazy_gettext('Username already exists'))
            return redirect(url_for('user.users_view'))
        if db.session.query(User).filter_by(email=form.email.data).first():
            flash(lazy_gettext('Email already exists'))
            return redirect(url_for('user.users_view'))

        user = User(username=form.username.data,
                    email=form.email.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data
                    )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(lazy_gettext('Registration successful! Please log in.'))

    return redirect(url_for('user.users_view'))


@user_bp.route('/users/<int:user_id>/delete', methods=['GET'])
@login_required
@check_own_or_has_permissions([
    'admin.user.delete'
])
def delete_user(user_id):
    """ Handle the deletion of a user.

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        Redirect to the users page after deletion.
    """
    user = db.session.query(User).filter_by(id=user_id).first_or_404()
    delete_current_user = False
    if user.id == current_user.id:
        delete_current_user = True
    if user.image_filename and user.image_filename != get_default_user_image():
        image_path = os.path.join('img', 'user', user.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(user)
    db.session.commit()
    if delete_current_user:
        redirect(url_for('auth.logout'))

    return redirect(url_for('user.users_view'))


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@check_own_or_has_permissions([
    'admin.user.read'
])
def user_view(user_id):
    """ Render the users page

    Args:
        user_id (int): The ID of the user to display.

    Returns:
        Rendered template for the user page.
    """
    user = db.session.query(User).filter_by(id=user_id).first_or_404()
    if not is_image_name_valid(user.image_filename):
        user.image_filename = get_default_user_image()
    return render_template('site.user.html', current_user=current_user, user=user)


@user_bp.route('/users/<int:user_id>/update', methods=['GET', 'POST'])
@login_required
@check_own_or_has_permissions([
    'admin.user.update'
])
def update_user(user_id):
    """ Update user information

    Args:
        user_id (int): The ID of the user to update.

    Returns:
        Rendered template for the user update page or redirects to the user page after successful update.

    """
    user = db.session.query(User).filter_by(id=user_id).first_or_404()
    form = UserUpdateForm(obj=user)

    if form.validate_on_submit():
        if not user:
            flash(_('User not found.'))
            return redirect(url_for('user.users_view'))
        if not user.check_password(form.old_password.data):
            flash(_('Old password is incorrect.'))
            return render_template('site.user.update.html', current_user=current_user, user=user, form=form)

        form.populate_obj(user)
        # * image handling
        # remove old image if exists
        if form.delete_image.data or form.image.data:
            if user.image_filename and user.image_filename != get_default_user_image():
                old_image_path = os.path.join(
                    'img', 'user', user.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            user.image_filename = None

        # save new image
        if form.image.data:
            image = form.image.data
            filename = image.filename
            ext = os.path.splitext(filename)[1]
            unique_name = f"{uuid4()}{ext}"
            image_path = os.path.join('img', 'user', unique_name)
            # Ensure directory exists
            image.save(image_path)
            user.image_filename = unique_name
        db.session.add(user)
        db.session.commit()
        return redirect(f'/users/{user.id}')

    if not is_image_name_valid(user.image_filename):
        user.image_filename = get_default_user_image()

    return render_template('site.user.update.html', current_user=current_user, user=user, form=form)
