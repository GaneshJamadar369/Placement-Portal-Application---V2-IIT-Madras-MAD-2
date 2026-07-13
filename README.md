# Placement Portal Application

## Tech Stack
- Backend: Flask, Flask-SQLAlchemy (SQLite), Jinja2 (page shell / CDN entry point)
- Frontend: Vue.js 3 (CDN, Options API) + Bootstrap 5 (CDN)
- Background jobs: Celery + Redis
- Auth: Flask session-based, role-based access control (Admin / Company / Student)

## Prerequisites
- Python 3.11+
- Redis server (via Docker, or a native Windows/WSL Redis build)

## Steps to run the application

### 1. Create a virtual environment
```bash
python -m venv venv
```

### 2. Activate the virtual environment
Windows:
```bash
venv\Scripts\activate
```
macOS/Linux:
```bash
source venv/bin/activate
```

### 3. Install all required packages
```bash
pip install -r requirements.txt
```

### 4. Start Redis
Using Docker (recommended):
```bash
docker run -d --name placement-redis -p 6379:6379 redis:7-alpine
```

### 5. Seed the admin account (run once)
```bash
python seed_admin.py
```
Default admin login: `admin@placement.com` / `admin123`
(The database and all tables are created automatically the first time `app.py` runs — no manual database setup is needed.)

### 6. Start the application
You need **3 terminals** running at the same time (all from the project root, with the virtual environment activated):

**Terminal 1 — Flask app**
```bash
python app.py
```
Visit **http://127.0.0.1:5000/**

**Terminal 2 — Celery worker** (handles the async CSV export job)
```bash
celery -A tasks.celery worker --loglevel=info --pool=solo
```
(`--pool=solo` is required on Windows.)

**Terminal 3 — Celery beat** (triggers the scheduled daily/monthly jobs)
```bash
celery -A tasks.celery beat --loglevel=info
```

## Background Jobs
- **Daily reminders** (9:00 AM): emails students about drives whose deadline is the next day, if they haven't applied yet and are eligible.
- **Monthly report** (1st of month, 8:00 AM): emails the admin a summary of drives/applications/selections from the previous month.
- **CSV export** (on-demand): triggered from the student dashboard "Export as CSV" button; runs async via Celery, emails the student when done.

Emails are captured via Flask-Mail with `MAIL_SUPPRESS_SEND=True` (no real SMTP server needed for local/demo use) — the message is fully constructed and would be sent if a real mail server were configured in `config.py`.

**Note on Flask-Mail:** the project spec's mandatory stack list (Flask, Vue.js, Jinja2, Bootstrap, SQLite, Redis, Celery) names the core architectural frameworks. Flask-Mail is a thin, officially-maintained Flask *extension* (same category as Flask-SQLAlchemy) that wraps Python's built-in `smtplib` — it introduces no new architectural pattern and is used only because the spec's own background-jobs section explicitly requires email delivery ("Email, SMS, or Google Chat Webhook") for the reminder and report jobs. All notification delivery is also mirrored in-app via the Notification/bell system, which uses no external library at all.

## Redis Caching
The approved-drives list (`/student/drives`) is cached in Redis for 60 seconds to reduce repeated database queries, and is invalidated automatically whenever the admin approves or closes a drive. Redis connection failures are handled gracefully — the app falls back to a direct database query rather than crashing if Redis is unavailable.

## Test Accounts
- Admin: `admin@placement.com` / `admin123`
- Register your own Student / Company accounts via the homepage.
