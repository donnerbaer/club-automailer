""" Decorators for Flask routes to manage user access and permissions. """
# app/utils/decorators.py

import logging
from typing import List
from flask import redirect, url_for, abort
from flask_login import current_user
from functools import wraps

logger = logging.getLogger(__name__)


def anonymous_required(f) -> callable:
    """ Decorator to restrict access to anonymous users only.
        If the user is authenticated, they will be redirected to the main page.
        This is useful for login or registration routes where authenticated users should not access them.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """ Check if the user is authenticated. If so, redirect to the main page. """
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def check_permissions(required_permissions: List[str]) -> callable:
    """Decorator to check if the user has the required permissions.
    This decorator can be applied to Flask route functions to ensure that the user has the necessary permissions
    before allowing access to the route.

    Args:
        required_permissions (List[str]): A list of permission names that the user must have.

    Returns:
        callable: A decorator that checks user permissions before executing the route function.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                logger.warning(f"Authentication required. User ID: {current_user.id if current_user.is_authenticated else 'anonymous'}")
                return redirect(url_for('auth.login'))

            for required_permission in required_permissions:
                if not current_user.has_permission(required_permission):
                    logger.warning(
                        f"Permission denied for user ID {current_user.id}: {required_permission}")
                    abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_own_or_has_permissions(required_permissions: List[str]) -> callable:
    """ Decorator to check if the user is accessing their own resource or has the required permissions.
    This is useful for routes where users can only access their own data or need specific permissions to access certain resources.

    Args:
        required_permissions (List[str]): A list of permission names that the user must have.

    kwargs:
        user_id (int): The ID of the user whose resource is being accessed.
                If this is provided and matches the current user's ID, access is granted regardless of permissions.

    Returns:
        callable: A decorator that checks if the user is accessing their own resource or has the required permissions.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = kwargs.get('user_id')
            if user_id is not None and current_user.id == user_id:
                return f(*args, **kwargs)

            for required_permission in required_permissions:
                if not current_user.has_permission(required_permission):
                    logger.warning(
                        f"Permission denied for user ID {current_user.id}: {required_permission}")
                    abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
