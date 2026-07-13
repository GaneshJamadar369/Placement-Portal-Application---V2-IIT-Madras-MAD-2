from flask import Flask, request, render_template
from flask_mail import Mail
from extensions import db
from config import Config
from celery_app import make_celery

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

mail = Mail(app)
celery = make_celery(app)

from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application, Notification
from routes.auth import auth_bp
app.register_blueprint(auth_bp)


@app.route("/")
def serve_frontend():
    return render_template("index.html")




from routes.admin import admin_bp
app.register_blueprint(admin_bp)

from routes.company import company_bp
app.register_blueprint(company_bp)

from routes.student import student_bp
app.register_blueprint(student_bp)

from routes.notification import notification_bp
app.register_blueprint(notification_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=False)

