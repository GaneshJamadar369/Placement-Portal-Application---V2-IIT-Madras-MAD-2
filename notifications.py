from extensions import db
from models import Notification, User


def notify_user(user_id, message):
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()


def notify_all_admins(message):
    admins = User.query.filter_by(role="admin").all()
    for admin in admins:
        notify_user(admin.id, message)
