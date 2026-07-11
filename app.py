from flask import Flask, request
from extensions import db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

from models import Student, Company
@app.route("/")
def home():
    return "Placement portal backend"

@app.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()
    result = []

    for s in students:
        result.append({
            "id": s.id,
            "name": s.name,
            "cgpa": s.cgpa,
            "branch": s.branch
        })


    return result

@app.route("/companies", methods=["POST"])
def create_company():

    data = request.get_json()

    company = Company(
        company_name=data["company_name"],
        hr_name=data["hr_name"],
        email=data["email"],
        password=data["password"],
        website=data["website"]
    )

    db.session.add(company)
    db.session.commit()

    return {
        "message": "Company Registered"
    }

@app.route("/companies", methods=["GET"])
def get_companies():
    companies = Company.query.all()
    result = []
    for c in companies:
        result.append({
            "id":c.id,
            "company_name":c.company_name,
            "email":c.email,
            "website": c.website,
            "approved": c.approved
        })

    return result



@app.route("/drive/<int:drive_id>")
def drive(drive_id):
    return f"Placment drive {drive_id}"
@app.route("/admin")
def admin():
    return "admin dashh.."

@app.route("/about")
def about():
    return "Placemmnt portal version 1.0"
@app.route("/contact")
def contact():
    return "placemnt@iitm.ac.in"

@app.route("/create_student", methods=["POST"])
def create_student():
    data = request.get_json()
    student = Student(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        cgpa=data["cgpa"],
        branch=data["branch"]
    )
    db.session.add(student)
    db.session.commit()

    return {
        "message": "Student Created successfully",
    }
with app.app_context():
    db.create_all()
app.run(debug=True)
