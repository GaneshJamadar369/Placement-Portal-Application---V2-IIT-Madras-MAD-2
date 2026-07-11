from flask import Blueprint, request, session
from extensions import db
from models import User, StudentProfile, CompanyProfile
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    role = data.get("role")

    if role not in ("student", "company"):
        return {"error": "Invalid role"}, 400

    if User.query.filter_by(email=data["email"]).first():
        return {"error": "Email already registered"}, 400

    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        role=role
    )
    db.session.add(user)
    db.session.commit()

    if role == "student":
        profile = StudentProfile(
            user_id=user.id,
            branch=data["branch"],
            cgpa=data["cgpa"]
        )
    else:
        profile = CompanyProfile(
            user_id=user.id,
            company_name=data["company_name"],
            hr_name=data.get("hr_name"),
            website=data.get("website")
        )

    db.session.add(profile)
    db.session.commit()

    return {"message": "Registered successfully"}


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(user.password_hash, data["password"]):
        return {"error": "Invalid email or password"}, 401

    if user.status != "Active":
        return {"error": "Account is not active"}, 403

    session["user_id"] = user.id
    session["role"] = user.role
    user.last_login = datetime.utcnow()
    db.session.commit()

    return {"message": "Logged in", "role": user.role}


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return {"message": "Logged out"}
