# Placement Portal Application

## Tech Stack
- Backend: Flask, Flask-SQLAlchemy (SQLite)
- Frontend: Vue.js 3 (CDN) + Bootstrap 5 (CDN)
- Background jobs: Celery + Redis
- Auth: Flask session-based, role-based access control (Admin / Company / Student)

## Prerequisites
- Python 3.11+
- Redis server (via Docker, or a native Windows/WSL Redis build)

## Setup

```bash
pip install -r requirements.txt
```

## Start Redis

Using Docker (recommended):
```bash
docker run -d --name placement-redis -p 6379:6379 redis:7-alpine
```

## Seed the admin account (run once)

```bash
python seed_admin.py
```
Default admin login: `admin@placement.com` / `admin123`

## Run the application

You need **3 terminals** running at the same time:

**Terminal 1 - Flask app**
```bash
python app.py
```
Visit http://127.0.0.1:5000/app

**Terminal 2 - Celery worker** (handles the async CSV export job)
```bash
celery -A tasks.celery worker --loglevel=info --pool=solo
```
(`--pool=solo` is required on Windows.)

**Terminal 3 - Celery beat** (triggers the scheduled daily/monthly jobs)
```bash
celery -A tasks.celery beat --loglevel=info
```

## Background Jobs
- **Daily reminders** (9:00 AM): emails students about drives whose deadline is the next day, if they haven't applied yet and are eligible.
- **Monthly report** (1st of month, 8:00 AM): emails the admin a summary of drives/applications/selections from the previous month.
- **CSV export** (on-demand): triggered from the student dashboard "Export as CSV" button; runs async via Celery, emails the student when done.

Emails are captured via Flask-Mail with `MAIL_SUPPRESS_SEND=True` (no real SMTP server needed for local/demo use) - the message is fully constructed and would be sent if a real mail server were configured in `config.py`.

## Redis Caching
The approved-drives list (`/student/drives`) is cached in Redis for 60 seconds to reduce repeated database queries, and is invalidated automatically whenever the admin approves or closes a drive.

## Test Accounts
- Admin: `admin@placement.com` / `admin123`
- Register your own Student / Company accounts via the `/app` frontend.
