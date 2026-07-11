from flask import Flask, request
from extensions import db
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

from models import User, StudentProfile, CompanyProfile, PlacementDrive, Application
from routes.auth import auth_bp
app.register_blueprint(auth_bp)
@app.route("/")
def home():
    return "Placement portal backend"

from routes.admin import admin_bp
app.register_blueprint(admin_bp)


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

