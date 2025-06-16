from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from admin_dashboard.models import *
from .utils import send_notification, notify_admins

User = get_user_model()

# -------------------- 1. User Registration --------------------
@receiver(post_save, sender=User)
def notify_admin_on_user_registration(sender, instance, created, **kwargs):
    if created:
        notify_admins(f"🧑 New user registered: {instance.username} ({instance.role})")


# -------------------- 2. Milk Collection --------------------
@receiver(post_save, sender=MilkCollection)
def notify_on_milk_collection(sender, instance, created, **kwargs):
    if created:
        send_notification(instance.farmer, f"🍼 {instance.quantity_litres}L of milk collected by {instance.collector.username}.")
        send_notification(instance.collector, f"✅ You collected {instance.quantity_litres}L from {instance.farmer.username}.")
        notify_admins(f"📥 Milk collection recorded: {instance.quantity_litres}L from {instance.farmer.username} by {instance.collector.username}.")


# -------------------- 3. Payment --------------------
@receiver(post_save, sender=Payment)
def notify_on_payment(sender, instance, created, **kwargs):
    if created:
        if instance.method == 'milk_deduction':
            send_notification(instance.user, f"💸 Payment made using milk deductions: KES {instance.farmer_deduction} deducted.")
            notify_admins(f"🧾 Payment by {instance.user.username} via milk deduction: KES {instance.farmer_deduction}.")

        elif instance.method == 'mpesa':
            send_notification(instance.user, f"📱 M-Pesa payment of KES {instance.gross_amount} received successfully.")
            notify_admins(f"📲 Payment by {instance.user.username} via M-Pesa: KES {instance.gross_amount}.")

    else:
        # Optional: Alert when payment is marked/updated by admin
        if instance.status == 'paid':
            send_notification(instance.user, f"✅ Your payment of KES {instance.net_amount} has been marked as paid.")
            notify_admins(f"🧾 Payment updated for {instance.user.username}: now marked as paid.")


# -------------------- 4. Supplement Order --------------------
@receiver(post_save, sender=SupplementOrder)
def notify_on_order_status(sender, instance, created, **kwargs):
    if created:
        # Notify user and admin on order placement
        send_notification(instance.user, f"🛒 Order #{instance.id} placed successfully. Waiting for approval.")
        notify_admins(f"📦 New supplement order #{instance.id} by {instance.user.username} pending approval.")

    # Notify user when order is approved
    elif instance.status == "approved" and not instance.notification_sent:
        send_notification(instance.user, f"✅ Your supplement order #{instance.id} has been approved.")
        notify_admins(f"🆗 Order #{instance.id} approved for {instance.user.username}.")
        instance.notification_sent = True
        instance.save(update_fields=["notification_sent"])

    # Notify user when order is paid
    elif instance.status == "paid" and not instance.notification_sent:
        send_notification(instance.user, f"💰 Your supplement order #{instance.id} has been paid. Thank you!")
        notify_admins(f"💳 Order #{instance.id} marked as paid for {instance.user.username}.")
        instance.notification_sent = True
        instance.save(update_fields=["notification_sent"])
