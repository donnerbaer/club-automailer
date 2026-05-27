# Translation Help

How to translate this project with flask-babel.


1. Navigate into the `/app`-directory


2. Extract the messages.

    ```shell
    pybabel extract -F babel.cfg -o messages.pot .
    ```


3. Initialize your wished language. (Example for german)
Use ISO-639-2 for the language
    ```shell
    pybabel init -i messages.pot -d translations -l de
    ```


4. Update the translation files
    ```shell
    pybabel update -i messages.pot -d translations
    ```


5. After finished with translation compile the translations
    ```shell
    pybabel compile -d translations
    ```