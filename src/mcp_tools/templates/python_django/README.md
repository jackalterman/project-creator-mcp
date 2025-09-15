# Django Project

This is a basic Django project template.

## Setup

1.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Apply migrations:
    ```bash
    python manage.py migrate
    ```
4.  Run the development server:
    ```bash
    python manage.py runserver
    ```

## Project Structure

-   `manage.py`: Django's command-line utility.
-   `{{project_name}}/`: The main project package.
    -   `settings.py`: Project settings.
    -   `urls.py`: Project URL declarations.
    -   `wsgi.py`: WSGI configuration for deployment.
    -   `asgi.py`: ASGI configuration for deployment.
    -   `__init__.py`: Makes `{{project_name}}` a Python package.