from flask import Blueprint, request
from extensions import db
from models import User, CompanyProfile, PlacementDrive, StudentProfile
from routes.decorator import login_required

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
    return {"message": "Company approved"}

@admin_bp.route("/companies/<int:company_id>/reject", methods=["PATCH"])
@login_required(role="admin")
def reject_company(company_id):
    company = CompanyProfile.query.get(company_id)
    if not company:
        return {"error": "Company not found"}, 404
    company.approval_status = "Rejected"
    db.session.commit()
    return {"message": "Company rejected"}
