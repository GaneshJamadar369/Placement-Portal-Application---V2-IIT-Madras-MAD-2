class Config:
    SECRET_KEY = "dev-secret-key-change-later"
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = "placement-portal@example.com"
    ADMIN_EMAIL = "admin@placement.com"

    UPLOAD_FOLDER = "uploads"
    EXPORT_FOLDER = "exports"
