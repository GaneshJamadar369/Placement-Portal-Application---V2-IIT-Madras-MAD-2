import redis
from flask import Blueprint, request
from extensions import db, redis_client
from models import User, CompanyProfile, PlacementDrive, StudentProfile
from routes.decorator import login_required
from notifications import notify_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/companies/pending", methods=["GET"])
@login_required(role="admin")
def get_pending_companies():
    companies = CompanyProfile.query.filter_by(approval_status="Pending").all()
    result = []
    for c in companies:
        result.append({
            "id": c.id,
            "company_name": c.company_name,
            "hr_name": c.hr_name,
            "website": c.website
        })
    return result

@admin_bp.route("/companies/<int:company_id>/approve", methods=["PATCH"])
@login_required(role="admin")
def approve_company(company_id):
    company = CompanyProfile.query.get(company_id)
    if not company:
        return {"error": "Company not found"}, 404
    company.approval_status = "Approved"
    db.session.commit()
    notify_user(company.user_id, "Your company has been approved. You can now create placement drives.")
    return {"message": "Company approved"}

@admin_bp.route("/companies/<int:company_id>/reject", methods=["PATCH"])
@login_required(role="admin")
def reject_company(company_id):
    company = CompanyProfile.query.get(company_id)
    if not company:
        return {"error": "Company not found"}, 404
    company.approval_status = "Rejected"
    db.session.commit()
    notify_user(company.user_id, "Your company registration was rejected. Contact admin@placement.com for details.")
    return {"message": "Company rejected"}
@admin_bp.route("/drives/pending", methods=["GET"])
@login_required(role="admin")
def get_pending_drives():
    drives = PlacementDrive.query.filter_by(status="Pending").all()
    result = []
    for d in drives:
        result.append({
            "id": d.id,
            "title": d.title,
            "company_id": d.company_id,
            "package": d.package,
            "deadline": str(d.deadline) if d.deadline else None
        })
    return result

@admin_bp.route("/drives", methods=["GET"])
@login_required(role="admin")
def get_all_drives():
    search = request.args.get("search", "")
    query = PlacementDrive.query
    if search:
        query = query.filter(PlacementDrive.title.ilike(f"%{search}%"))

    drives = query.all()
    result = []
    for d in drives:
        company = CompanyProfile.query.get(d.company_id)
        result.append({
            "id": d.id,
            "title": d.title,
            "company_name": company.company_name if company else None,
            "status": d.status,
            "package": d.package,
            "deadline": str(d.deadline) if d.deadline else None
        })
    return result

@admin_bp.route("/drives/<int:drive_id>/approve", methods=["PATCH"])
@login_required(role="admin")
def approve_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return {"error": "Drive not found"}, 404
    drive.status = "Approved"
    db.session.commit()
    try:
        redis_client.delete("approved_drives")
    except redis.exceptions.RedisError:
        pass  # Cache invalidation is best-effort; the stale cache will expire via its TTL anyway

    company = CompanyProfile.query.get(drive.company_id)
    if company:
        notify_user(company.user_id, f"Your drive '{drive.title}' has been approved and is now visible to students.")

    return {"message": "Drive approved"}

@admin_bp.route("/drives/<int:drive_id>/reject", methods=["PATCH"])
@login_required(role="admin")
def reject_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return {"error": "Drive not found"}, 404
    drive.status = "Closed"
    db.session.commit()
    try:
        redis_client.delete("approved_drives")
    except redis.exceptions.RedisError:
        pass  # Cache invalidation is best-effort; the stale cache will expire via its TTL anyway

    company = CompanyProfile.query.get(drive.company_id)
    if company:
        notify_user(company.user_id, f"Your drive '{drive.title}' was rejected/closed by the admin.")

    return {"message": "Drive closed"}

@admin_bp.route("/stats", methods=["GET"])
@login_required(role="admin")
def get_stats():
    return {
        "total_students": StudentProfile.query.count(),
        "total_companies": CompanyProfile.query.count(),
        "total_drives": PlacementDrive.query.count()
    }

@admin_bp.route("/students", methods=["GET"])
@login_required(role="admin")
def get_all_students():
    search = request.args.get("search", "")
    query = User.query.filter_by(role="student")
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))

    users = query.all()
    result = []
    for u in users:
        profile = StudentProfile.query.filter_by(user_id=u.id).first()
        result.append({
            "user_id": u.id,
            "name": u.name,
            "email": u.email,
            "status": u.status,
            "branch": profile.branch if profile else None,
            "cgpa": profile.cgpa if profile else None
        })
    return result

@admin_bp.route("/companies", methods=["GET"])
@login_required(role="admin")
def get_all_companies():
    search = request.args.get("search", "")
    query = CompanyProfile.query
    if search:
        query = query.filter(CompanyProfile.company_name.ilike(f"%{search}%"))

    companies = query.all()
    result = []
    for c in companies:
        result.append({
            "id": c.id,
            "company_name": c.company_name,
            "approval_status": c.approval_status
        })
    return result

@admin_bp.route("/users/<int:user_id>/status", methods=["PATCH"])
@login_required(role="admin")
def update_user_status(user_id):
    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ("Active", "Blacklisted", "Deactivated"):
        return {"error": "Invalid status"}, 400

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    user.status = new_status
    db.session.commit()
    return {"message": f"User status set to {new_status}"}

