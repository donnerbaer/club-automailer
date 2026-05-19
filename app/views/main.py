""" This module handles the main views of the application, including the index, dashboard, and error pages."""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.forms import SearchForm
from app.model.model import User


main_bp = Blueprint('main', __name__)


@main_bp.app_context_processor
def inject_search_form():
    """Injects the search form into the template context.

    This allows the search form to be accessible in all templates rendered within this blueprint.
    """
    return {
        'navbar_search_form': SearchForm(),
    }


@main_bp.route('/')
def index():
    """ Render the index page

    Returns:
        Rendered template for the index page.
    """
    return render_template('site.index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """ Render the dashboard page for authenticated users.

    Returns:
        Rendered template for the dashboard page.
    """
    return render_template('site.dashboard.html')


@main_bp.route('/search')
@login_required
def search_view():
    """ Render the search page for authenticated users.

    Returns:
        Rendered template for the search page.
    """
    return "Not implemented yet"


@main_bp.app_errorhandler(403)
def page_not_found_403(e):
    """ Render the 403 error page.

    Args:
        e: The error that occurred.

    Returns:
        Rendered template for the 403 error page.
    """
    return render_template('error/403.html', current_user=current_user), 403


@main_bp.app_errorhandler(404)
def page_not_found_404(e):
    """ Render the 404 error page.

    Args:
        e: The error that occurred.

    Returns:
        Rendered template for the 404 error page.
    """
    return render_template('error/404.html', current_user=current_user), 404


@main_bp.app_errorhandler(500)
def internal_server_error_500(e):
    """ Render the 500 error page.

    Args:
        e: The error that occurred.

    Returns:
        Rendered template for the 500 error page.
    """
    return render_template('error/500.html', current_user=current_user), 500
