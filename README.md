# Club Automailer

Web application and mail service for club notifications.

## Features

- Manage members, groups, roles, and permissions
- Create notification rules and templates
- Send automated email notifications
- Import events, members, and working hours
- Generate calendar links and ICS attachments

## Supported Languages

- `en` English
- `de` Deutsch ~70¼

## Requirements

- Python 3.14.5
- SMTP access for outgoing mail

Older Python versions may also work, but are not officially tested.

## Setup

1. Create and activate a virtual environment.

    ```sh
    python -m venv venv
    source venv/bin/activate
    ```

    On Windows, use `venv\Scripts\activate` instead.

2. Install dependencies.

    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the project root.

    ```sh
    SECRET_KEY=change-me
    SQLALCHEMY_DATABASE_URI=sqlite:///database.db
    EVENT_DOMAIN=example.org

    SMTP_HOST=smtp.example.org
    SMTP_PORT=587
    SMTP_USER=user@example.org
    SMTP_PASSWORD=YourPassword
    MAIL_FROM=Your Name <mail@example.org>
    ```

    The application requires `SECRET_KEY`. The database URI is read from `SQLALCHEMY_DATABASE_URI`. Other databases may require some changes.

4. Start the web application once so the database tables are created.

    ```sh
    python main.py
    ```

5. Populate the default roles, groups, permissions, and admin user.

    ```sh
    python setup.py
    ```

6. Optional: load demo data for testing.

    ```sh
    python seed_test_data.py
    ```

7. Optional: verify the SMTP configuration.

    ```sh
    python test_smtp.py
    ```

## Run the Web App

Start the application with:

```sh
python main.py
```

Then open the web interface in your browser. By default, Flask serves the app on `http://127.0.0.1:5000/`.

Default login credentials:

- Username: `admin`
- Password: `Starten1!`

Change the password after the first login.

## Run the Mail Service

The mail service is intended to run separately, for example via cron:

```sh
python mail-service.py
```

Useful flags:

- `--debug` for verbose output
- `--simulate` for dry runs without sending mail
- `--force-working-hours-monthly` to force the monthly working-hours mail

## Notes

- The web app and the mail service use the same `.env` configuration.
- If you use SQLite, make sure the target directory exists.
- The repository also contains `TRANSLATION.md` for localization notes.
