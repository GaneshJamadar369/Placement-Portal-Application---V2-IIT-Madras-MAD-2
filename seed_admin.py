from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    existing = User.query.filter_by(role="admin").first()
    if existing:
        print("Admin already exists:", existing.email)
    else:
        admin = User(
            name="Placement Admin",
            email="admin@placement.com",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created:", admin.email)
