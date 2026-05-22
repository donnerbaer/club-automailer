""" This module is the entry point for the Flask application.
    It initializes the app, sets up the database, and runs the server.
"""

from app import create_app, db


app = create_app()

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    import os
    # Debug mode should only be enabled for development via environment variable
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    # app.run(debug=debug_mode, host='', port=80)
    app.run(debug=debug_mode)
