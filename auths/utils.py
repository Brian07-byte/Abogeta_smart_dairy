# auths/utils.py

from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def send_notification(user, message):
    Notification.objects.create(user=user, message=message)

def notify_admins(message):
    admins = User.objects.filter(is_superuser=True)
    for admin in admins:
        send_notification(admin, message)
