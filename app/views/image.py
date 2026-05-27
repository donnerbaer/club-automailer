""" This module handles the image routes of the application.
It provides functionality to serve images for items, current users, and others images.
It also includes checks to ensure that the current user is logged in before accessing these routes.
"""

import os
import re
from flask import Blueprint, send_from_directory, abort
from flask import redirect
from flask_login import login_required, current_user
from app import db
from app.model.model import User
from app.utils.image import is_image_name_valid, get_default_user_image


def validate_filename(filename):
    """Validate filename to prevent path traversal attacks.
    
    Args:
        filename (str): The filename to validate.
        
    Raises:
        ValueError: If the filename contains path traversal attempts.
        
    Returns:
        bool: True if the filename is valid.
    """
    # Only allow alphanumeric, dots, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
        return False
    # Prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    return True


image_bp = Blueprint('image', __name__)


@image_bp.route('/img/item/<path:filename>')
@login_required
def serve_item_image(filename):
    """Serve an image from the filesystem.

    Args:
        filename (str): The name of the image file to serve.

    Returns:
        Response: The image file served from the specified directory.
        
    Raises:
        400: If filename contains invalid characters or path traversal attempts.
    """
    # Validate filename to prevent path traversal attacks
    if not validate_filename(filename):
        abort(400)  # Bad request
    image_dir = os.path.join(os.getcwd(), 'img', 'item')
    return send_from_directory(image_dir, filename)


@image_bp.route('/img/current_user', methods=['GET'])
@login_required
def serve_current_user_image():
    """Serve the current user's image.

    Returns:
        Redirect: Redirects to the user's image URL.
    """
    user = db.session.query(User).filter_by(id=current_user.id).first_or_404()
    if not is_image_name_valid(user.image_filename):
        user.image_filename = get_default_user_image()
    return redirect(f'/img/user/{user.image_filename}')


@image_bp.route('/img/user/<path:filename>')
@login_required
def serve_user_image(filename):
    """Serve an image from the filesystem.

    Args:
        filename (str): The name of the image file to serve.

    Returns:
        Response: The image file served from the specified directory.
    """
    image_dir = os.path.join(os.getcwd(), 'img', 'user')
    return send_from_directory(image_dir, filename)


@image_bp.route('/img/storage/<path:filename>')
@login_required
def serve_storage_image(filename):
    """Serve an image from the filesystem.

    Args:
        filename (str): The name of the image file to serve.

    Returns:
        Response: The image file served from the specified directory.
    """
    image_dir = os.path.join(os.getcwd(), 'img', 'storage')
    return send_from_directory(image_dir, filename)
