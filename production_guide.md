# Learnova production guide: PythonAnywhere

This project is a Django application. PythonAnywhere serves it through a WSGI
configuration and a separate static-files mapping; do not use Django's
development server as the public production server.

## 1. Upload and install

1. Upload the project to PythonAnywhere or clone the repository into your home
   directory.
2. Open a Bash console and create a virtual environment using the Python
   version selected for the web app:

   ```bash
   cd ~/learnova
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Set environment variables in the PythonAnywhere web app configuration. Start
   with `.env.example`; never commit `.env`, SMTP passwords, or `SECRET_KEY`.
   `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` must contain the exact
   `yourusername.pythonanywhere.com` hostname.

## 2. Database and static files

From the project directory with the virtual environment activated:

```bash
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
```

SQLite is supported by the current project. Back up `db.sqlite3` and the
`media/` directory regularly. For a high-traffic site, move the database to a
managed PostgreSQL/MySQL service after planning that migration separately.

In the PythonAnywhere **Web** tab, add:

| URL | Directory |
| --- | --- |
| `/static/` | `/home/yourusername/learnova/staticfiles/` |
| `/media/` | `/home/yourusername/learnova/media/` |

## 3. WSGI configuration

Edit the generated WSGI file and use the equivalent of:

```python
import os
import sys

project_home = '/home/yourusername/learnova'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learnova.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Select the virtualenv at:
`/home/yourusername/learnova/.venv`.

Reload the web app after every code or environment-variable change.

## 4. Email

Set `EMAIL_BACKEND` to Django's SMTP backend and provide the SMTP host,
port, TLS/SSL mode, username, app password, and a verified
`DEFAULT_FROM_EMAIL`. Do not use a normal Gmail password; use an app password
or a transactional email provider's SMTP credentials. `CONTACT_EMAIL` receives
contact-form messages. The app stores contact messages before attempting email,
so an SMTP outage does not lose the submission, and failures are logged.

Verify email from the Django shell:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings
send_mail('Learnova test', 'SMTP is working.', settings.DEFAULT_FROM_EMAIL, ['you@example.com'])
```

## 5. Admin and contributor workflow

Create an admin account with `python manage.py createsuperuser`. Review
contributor topic proposals and lessons through the staff review pages before
publishing. Topic icons accept Font Awesome snippets or inline SVG, but the
application sanitizes the markup and constrains it to its container so a
contributor cannot inject scripts or break the admin layout.

Before launch, confirm:

- `DEBUG=False`
- a unique production `SECRET_KEY` is configured
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` match the live hostname
- HTTPS is active before enabling `SECURE_SSL_REDIRECT=True`
- static and media mappings work
- contact, newsletter welcome, and admin test emails arrive
- database and uploaded-media backups exist