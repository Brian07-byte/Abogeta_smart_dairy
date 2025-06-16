from admin_dashboard.models import CartItem
from .models import Feedback, Notification
from django.db.models import Sum
from django.contrib.auth import get_user_model

User = get_user_model()

def notification_context(request):
    if request.user.is_authenticated:
        # Only fetch unread notifications to show in the navbar
        user_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp')
        unread_count = user_notifications.count()

        return {
            'user_notifications': user_notifications,  # Unread only
            'user_notifications_count': unread_count,
        }
    return {}


def feedback_count(request):
    if request.user.is_authenticated:
        count = Feedback.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_feedback_count': count}
    return {}



def cart_item_count(request):
    if request.user.is_authenticated:
        total_items = CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
        return {'cart_count': total_items}
    return {'cart_count': 0}
