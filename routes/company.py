import os
from flask import Blueprint, request, session, send_from_directory
from extensions import db
from models import CompanyProfile, PlacementDrive, Application, StudentProfile, User
from routes.decorator import login_required
from datetime import datetime
from notifications import notify_all_admins, notify_user

company_bp = Blueprint("company", __name__, url_prefix="/company")

def get_company_profile():
    return CompanyProfile.query.filter_by(user_id=session["user_id"]).first()

@company_bp.route("/profile", methods=["GET"])
@login_required(role="company")
def get_profile():
    company = get_company_profile()
    if not company:
        return {"error": "Company profile not found, please log in again"}, 401
    return {
        "id": company.id,
        "company_name": company.company_name,
        "hr_name": company.hr_name,
        "website": company.website,
        "approval_status": company.approval_status
    }

@company_bp.route("/drives", methods=["POST"])
@login_required(role="company")
def create_drive():
    company = get_company_profile()
    if not company:
        return {"error": "Company profile not found, please log in again"}, 401

    if company.approval_status != "Approved":
        return {"error": "Company not approved yet"}, 403

    data = request.get_json()
    drive = PlacementDrive(
        company_id=company.id,
        title=data["title"],
        description=data.get("description"),
        package=data.get("package"),
        location=data.get("location"),
        eligibility_branch=data.get("eligibility_branch"),
        eligibility_min_cgpa=data.get("eligibility_min_cgpa"),
        deadline=datetime.strptime(data["deadline"], "%Y-%m-%d").date() if data.get("deadline") else None

    )
    db.session.add(drive)
    db.session.commit()

    notify_all_admins(f"New drive '{drive.title}' from {company.company_name} is pending approval")

    return {"message": "Drive created, pending admin approval"}

@company_bp.route("/drives", methods=["GET"])
@login_required(role="company")
def get_my_drives():
    company = get_company_profile()
    if not company:
        return {"error": "Company profile not found, please log in again"}, 401
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()

    result = []
    for d in drives:
        result.append({
            "id": d.id,
            "title": d.title,
            "status": d.status,
            "package": d.package,
            "deadline": str(d.deadline) if d.deadline else None
        })
    return result

@company_bp.route("/drives/<int:drive_id>/applications", methods=["GET"])
@login_required(role="company")
def get_drive_applications(drive_id):
    company = get_company_profile()
    if not company:
        return {"error": "Company profile not found, please log in again"}, 401
    drive = PlacementDrive.query.get(drive_id)

    if not drive or drive.company_id != company.id:
        return {"error": "Drive not found"}, 404

    applications = Application.query.filter_by(drive_id=drive_id).all()
    result = []
    for a in applications:
        student = StudentProfile.query.get(a.student_id)
        user = User.query.get(student.user_id)
        result.append({
            "application_id": a.id,
            "student_id": student.id,
            "name": user.name,
            "email": user.email,
            "branch": student.branch,
            "cgpa": student.cgpa,
            "resume": student.resume,
            "applied_at": str(a.applied_at),
            "status": a.status
        })
    return result

@company_bp.route("/applications/<int:application_id>/resume", methods=["GET"])
@login_required(role="company")
def download_applicant_resume(application_id):
    company = get_company_profile()
    if not company:
        return {"error": "Company profile not found, please log in again"}, 401

    application = Application.query.get(application_id)
    if not application:
        return {"error": "Application not found"}, 404

    drive = PlacementDrive.query.get(application.drive_id)
    if not drive or drive.company_id != company.id:
        return {"error": "Forbidden"}, 403

    student = StudentProfile.query.get(application.student_id)
    if not student or not student.resume:
        return {"error": "No resume uploaded by this student"}, 404

    directory = os.path.dirname(os.path.abspath(student.resume))
    filename = os.path.basename(student.resume)
    return send_from_directory(directory, filename, as_attachment=True)

@company_bp.route("/applications/<int:application_id>/status", methods=["PATCH"])
@login_required(role="company")
def update_application_status(application_id):
    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ("Shortlisted", "Selected", "Rejected"):
        return {"error": "Invalid status"}, 400

    application = Application.query.get(application_id)
    if not application:
        return {"error": "Application not found"}, 404

    drive = PlacementDrive.query.get(application.drive_id)
    company = get_company_profile()
    if not company or drive.company_id != company.id:
        return {"error": "Forbidden"}, 403

    application.status = new_status
    db.session.commit()

    student = StudentProfile.query.get(application.student_id)
    if student:
        notify_user(student.user_id, f"Your application for '{drive.title}' was marked as {new_status}.")

    return {"message": f"Application marked as {new_status}"}
