""" This module handles user authentication, including login, registration, and logout."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_babel import lazy_gettext as _l
from flask_login import login_user, logout_user, login_required
from app import db
from app.forms import LoginForm, RegistrationForm
from app.model.model import User
from app.utils.decorators import anonymous_required


auth_bp = Blueprint('auth', __name__)


@auth_bp.app_context_processor
def inject_auth_form():
    """Injects the login and registration forms into the template context.
        This allows the forms to be accessible in all templates rendered
        within this blueprint.
    """
    return {
        'nav_login_form': LoginForm(),
        'nav_signup_form': RegistrationForm()
    }


@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    """ Handles user login."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if request.args.get('next'):
                return redirect(request.args.get('next', "/"))
        flash(_l('Invalid username or password'))
        return redirect(url_for('main.dashboard'))
    return render_template(
        'site.login.html',
        nav_login_form=form,
        next=request.args.get('next', "/")
    )


@auth_bp.route('/logout')
@login_required
def logout():
    """ Handles user logout."""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """ Handles user registration."""
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash(_l('Username already exists'))
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=form.email.data).first():
            flash(_l('Email already registered'))
            return redirect(url_for('auth.register'))
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_l('Account created successfully. Please log in.'))
        return redirect(url_for('auth.login'))
    return render_template('site.register.html', form=form)
