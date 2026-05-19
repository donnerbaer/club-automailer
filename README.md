# EMail Notification Tool

Python tool for sending Email notifications for Clubs

## Supported Languages

The following languages are currently supported.

+ de german
+ en english

## Setup

1. Open a command line/terminal.
2. Navigate to the project folder.

3. Create a virtual environment:

    ```sh
    python -m venv venv
    ```

4. Activate the virtual environment:

    - **Windows:**

      ```sh
      venv\Scripts\activate
      ```

    - **Mac/Linux:**

      ```sh
      source venv/bin/activate
      ```

5. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

6. Create a `.env` file:
    1. Add the following content:
        ```sh
        DATABASE_URL=sqlite:///database.db
        SECRET_KEY=mysecretkey

        SMTP_HOST=smtp.example.org
        SMTP_PORT=587
        SMTP_USER=user@example.org
        SMTP_PASSWORD=YourPassword
        MAIL_FROM=Your.Name <mail.example.org>

        ```
    2. Provide your secret key.
    3. Set your database path.

7. Set up the database with standard groups, roles, and permissions by running:

The application has run at least once. This is required for create the database tables.

```sh
python setup.py
```

8. Start the application

```sh
python main.py
```


# Start the application

1. Start the webserver:
    - Navigate to the `/` folder and run `main.py`:
    
    ```sh
    python main.py
    ```

2. Open your web browser and visit the URL you have configured for the website.

3. Log in with the default credentials:

+ username: `admin`
+ password' `Starten1!` 

# Run the mailing service

```sh
python mail-service.py
```