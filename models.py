from extensions import db

class Student(db.Model):
    __tablename__="students"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email=db.Column(db.String(100), unique=True, nullable=False)
    password=db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    
    resume=db.Column(db.String(255))

    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Company(db.Model):

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(100), nullable=False)

    hr_name = db.Column(db.String(100))

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    website = db.Column(db.String(255))

    approved = db.Column(db.Boolean, default=False)


class PlacementDrive(db.Model):

    __tablename__ = "placement_drives"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100))

    description = db.Column(db.Text)

    package = db.Column(db.Float)

    deadline = db.Column(db.Date)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id")
    )

class Application(db.Model):

    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id")
    )

    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drives.id")
    )

    status = db.Column(
        db.String(30),
        default="Applied"
    )

