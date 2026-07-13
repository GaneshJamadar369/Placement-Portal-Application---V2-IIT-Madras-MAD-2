from flask import Blueprint, session
from extensions import db
from models import Notification
from routes.decorator import login_required

notification_bp = Blueprint("notification", __name__, url_prefix="/notifications")


@notification_bp.route("", methods=["GET"])
@login_required()
def get_notifications():
    notifications = (
        Notification.query
        .filter_by(user_id=session["user_id"])
        .order_by(Notification.created_at.desc())
        .limit(30)
        .all()
    )
    return [
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": str(n.created_at)
        }
        for n in notifications
    ]


@notification_bp.route("/<int:notification_id>/read", methods=["PATCH"])
@login_required()
def mark_read(notification_id):
    notification = Notification.query.get(notification_id)
    if not notification or notification.user_id != session["user_id"]:
        return {"error": "Notification not found"}, 404

    notification.is_read = True
    db.session.commit()
    return {"message": "Marked as read"}


@notification_bp.route("/read-all", methods=["PATCH"])
@login_required()
def mark_all_read():
    Notification.query.filter_by(user_id=session["user_id"], is_read=False).update({"is_read": True})
    db.session.commit()
    return {"message": "All marked as read"}
