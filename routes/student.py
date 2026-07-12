import os
from flask import Blueprint, request, session
from werkzeug.utils import secure_filename
from extensions import db
from models import StudentProfile, PlacementDrive, Application, CompanyProfile
from routes.decorator import login_required
from sqlalchemy.exc import IntegrityError


student_bp = Blueprint("student", __name__, url_prefix="/student")

def get_student_profile():
    return StudentProfile.query.filter_by(user_id=session["user_id"]).first()

@student_bp.route("/profile", methods=["GET"])
@login_required(role="student")
def get_profile():
    student = get_student_profile()
    return {
        "id": student.id,
        "branch": student.branch,
        "cgpa": student.cgpa,
        "resume": student.resume
    }

@student_bp.route("/profile", methods=["PUT"])
@login_required(role="student")
def update_profile():
    student = get_student_profile()
    data = request.get_json()

    if "branch" in data:
        student.branch = data["branch"]
    if "cgpa" in data:
        student.cgpa = data["cgpa"]

    db.session.commit()
    return {"message": "Profile updated"}

@student_bp.route("/drives", methods=["GET"])
@login_required(role="student")
def get_eligible_drives():
    student = get_student_profile()

    drives = PlacementDrive.query.filter_by(status="Approved").all()
    result = []
    for d in drives:
        if d.eligibility_min_cgpa and student.cgpa < d.eligibility_min_cgpa:
            continue
        if d.eligibility_branch and d.eligibility_branch != student.branch:
            continue

        company = CompanyProfile.query.get(d.company_id)
        result.append({
            "id": d.id,
            "title": d.title,
            "company_name": company.company_name,
            "package": d.package,
            "location": d.location,
            "deadline": str(d.deadline) if d.deadline else None
        })
    return result

@student_bp.route("/applications", methods=["POST"])
@login_required(role="student")
def apply_to_drive():
    student = get_student_profile()
    data = request.get_json()
    drive_id = data.get("drive_id")

    drive = PlacementDrive.query.get(drive_id)
    if not drive or drive.status != "Approved":
        return {"error": "Drive not available"}, 404

    application = Application(student_id=student.id, drive_id=drive_id)
    db.session.add(application)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "You already applied to this drive"}, 400

    return {"message": "Applied successfully"}

@student_bp.route("/applications", methods=["GET"])
@login_required(role="student")
def get_my_applications():
    student = get_student_profile()
    applications = Application.query.filter_by(student_id=student.id).all()

    result = []
    for a in applications:
        drive = PlacementDrive.query.get(a.drive_id)
        company = CompanyProfile.query.get(drive.company_id)
        result.append({
            "application_id": a.id,
            "drive_title": drive.title,
            "company_name": company.company_name,
            "status": a.status,
            "applied_at": str(a.applied_at)
        })
    return result

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route("/resume", methods=["POST"])
@login_required(role="student")
def upload_resume():
    student = get_student_profile()

    if "resume" not in request.files:
        return {"error": "No file provided"}, 400

    file = request.files["resume"]

    if file.filename == "":
        return {"error": "No file selected"}, 400

    if not allowed_file(file.filename):
        return {"error": "Only PDF/DOC/DOCX allowed"}, 400

    filename = secure_filename(f"student_{student.id}_{file.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    student.resume = filepath
    db.session.commit()

    return {"message": "Resume uploaded", "path": filepath}

