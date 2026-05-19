""" This module is the entry point for the Flask application.
    It initializes the app, sets up the database, and runs the server.
"""

from app import create_app, db
from app.model.model import ensure_notification_log_event_title_column

app = create_app()

with app.app_context():
    db.create_all()
    ensure_notification_log_event_title_column()


if __name__ == '__main__':
    # app.run(debug=True, host='', port=80)
    app.run(debug=True)
