import os
import csv
from datetime import datetime, timedelta

from flask_mail import Message

from app import celery, mail, app
from extensions import db
from models import StudentProfile, CompanyProfile, PlacementDrive, Application, User


@celery.task(name="tasks.send_deadline_reminders")
def send_deadline_reminders():
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    drives = PlacementDrive.query.filter_by(status="Approved", deadline=tomorrow).all()

    sent_count = 0
    for drive in drives:
        applied_student_ids = {
            a.student_id for a in Application.query.filter_by(drive_id=drive.id).all()
        }
        eligible_students = StudentProfile.query.all()

        for student in eligible_students:
            if student.id in applied_student_ids:
                continue
            if drive.eligibility_min_cgpa and student.cgpa < drive.eligibility_min_cgpa:
                continue
            if drive.eligibility_branch and drive.eligibility_branch != student.branch:
                continue

            user = User.query.get(student.user_id)
            msg = Message(
                subject=f"Reminder: {drive.title} application closes tomorrow",
                recipients=[user.email],
                body=f"Hi {user.name},\n\nThe application deadline for '{drive.title}' "
                     f"is tomorrow ({drive.deadline}). Apply now if you're interested.\n\n"
                     f"- Placement Cell"
            )
            mail.send(msg)
            sent_count += 1

    return f"Sent {sent_count} reminder emails"


@celery.task(name="tasks.send_monthly_report")
def send_monthly_report():
    now = datetime.utcnow()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_of_last_month = (first_of_this_month - timedelta(days=1)).replace(day=1)

    drives_count = PlacementDrive.query.filter(
        PlacementDrive.created_at >= first_of_last_month,
        PlacementDrive.created_at < first_of_this_month
    ).count()

    applications_last_month = Application.query.filter(
        Application.applied_at >= first_of_last_month,
        Application.applied_at < first_of_this_month
    ).all()

    applied_count = len(applications_last_month)
    selected_count = len([a for a in applications_last_month if a.status == "Selected"])

    html_body = f"""
    <h2>Monthly Placement Activity Report</h2>
    <p>Period: {first_of_last_month.strftime('%B %Y')}</p>
    <ul>
        <li>Drives conducted: {drives_count}</li>
        <li>Students applied: {applied_count}</li>
        <li>Students selected: {selected_count}</li>
    </ul>
    """

    msg = Message(
        subject=f"Monthly Placement Report - {first_of_last_month.strftime('%B %Y')}",
        recipients=[app.config["ADMIN_EMAIL"]],
        html=html_body
    )
    mail.send(msg)

    return f"Monthly report sent: {drives_count} drives, {applied_count} applied, {selected_count} selected"


@celery.task(name="tasks.export_applications_csv")
def export_applications_csv(student_id):
    os.makedirs(app.config["EXPORT_FOLDER"], exist_ok=True)

    applications = Application.query.filter_by(student_id=student_id).all()
    filename = f"applications_student_{student_id}_{int(datetime.utcnow().timestamp())}.csv"
    filepath = os.path.join(app.config["EXPORT_FOLDER"], filename)

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Student ID", "Company Name", "Drive Title", "Status", "Applied At"])

        for a in applications:
            drive = PlacementDrive.query.get(a.drive_id)
            company = CompanyProfile.query.get(drive.company_id)
            writer.writerow([student_id, company.company_name, drive.title, a.status, a.applied_at])

    student = StudentProfile.query.get(student_id)
    user = User.query.get(student.user_id)
    msg = Message(
        subject="Your application history export is ready",
        recipients=[user.email],
        body=f"Hi {user.name},\n\nYour placement application history export is ready: {filename}"
    )
    mail.send(msg)

    return filename
