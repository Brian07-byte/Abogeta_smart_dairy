# accounts/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail

from admin_dashboard.models import MilkCollection, Payment, SupplementOrder



from .forms import (
    CustomUserCreationForm,
    CustomLoginForm,
    FeedbackForm,
    UserUpdateForm,
    CustomPasswordChangeForm
)
from .models import Feedback, Notification, CustomUser


# ----------------- Home / Landing Page ------------------
def home_redirect(request):
    """
    Handles the landing page.
    - If user is authenticated, redirects them to their dashboard.
    - If user is not authenticated, shows the homepage with login and registration forms.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    # If you want to show forms on the homepage for anonymous users
    login_form = CustomLoginForm()
    register_form = CustomUserCreationForm()
    return render(request, 'auths/home.html', {
        'login_form': login_form,
        'register_form': register_form,
    })


# ----------------- Registration ------------------
def register_view(request):
    """
    Handles user registration. Immediately activates the user.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Immediately activate user
            user.save()

            messages.success(request, "Registration successful! You can now log in.")
            return redirect('home')  # Redirect to login page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'auths/register.html', {'register_form': form})

# ----------------- Login / Logout ------------------
def login_view(request):
    """
    Handles user login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # The check for user.is_active should ideally be handled within the CustomLoginForm
            # But we can double-check here for security.
            if not user.is_active:
                messages.error(request, "Account not verified. Please check the verification link in your email.")
                return redirect('login')

            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()
        
    return render(request, 'auths/login.html', {'login_form': form})


@login_required
def logout_view(request):
    """
    Handles user logout.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


# ----------------- Unified Dashboard ------------------
@login_required
def dashboard_view(request):
    """
    A single view that directs users to the correct dashboard based on their role.
    This avoids code repetition.
    """
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-timestamp')[:5]
    context = {
        'notifications': notifications,
        'user_role': user.role
    }

    if user.is_superuser or user.role == 'admin':
        template_name = 'auths/admin_dashboard.html'
    elif user.role == 'collector':
        template_name = 'auths/collector_dashboard.html'
    elif user.role == 'farmer':
        template_name = 'auths/farmer_dashboard.html'
    else:
        # A fallback for users with no assigned role, or redirect them
        messages.warning(request, "You do not have a role assigned to access a dashboard.")
        return redirect('home')

    return render(request, template_name, context)



# ----------------- Dashboards ------------------
from django.db.models import Sum, Count
from decimal import Decimal
@login_required
def farmer_dashboard(request):
    user = request.user

    # Total Milk Delivered
    total_milk = MilkCollection.objects.filter(farmer=user).aggregate(total=Sum('quantity_litres'))['total'] or 0

    # Unpaid Milk Earnings
    unpaid_earnings = MilkCollection.objects.filter(farmer=user, is_paid=False).aggregate(
        total=Sum('amount_payable_to_farmer')
    )['total'] or Decimal('0.00')

    # Recent Supplement Orders
    recent_orders = SupplementOrder.objects.filter(user=user).order_by('-created_at')[:5]

    # Recent Payments
    recent_payments = Payment.objects.filter(user=user).order_by('-date_paid')[:5]

    # Feedback Summary
    sent_feedback = Feedback.objects.filter(sender=user).count()
    received_feedback = Feedback.objects.filter(recipient=user).count()

    # Optional: Unread Notifications
    unread_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-timestamp')[:5]

    return render(request, 'auths/farmer_dashboard.html', {
        'total_milk': total_milk,
        'unpaid_earnings': unpaid_earnings,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'sent_feedback': sent_feedback,
        'received_feedback': received_feedback,
        'unread_notifications': unread_notifications,
    })


@login_required
def collector_dashboard(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:5]
    return render(request, 'auths/collector_dashboard.html', {
        'notifications': notifications,
        'user_role': 'collector'
    })


# ----------------- User Profile Management ------------------
@login_required
def profile_view(request):
    """
    Allows a user to view and update their profile information.
    """
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'auths/profile.html', {
        'form': form,
        'user_role': request.user.role
    })


@login_required
def change_password_view(request):
    """
    Allows a logged-in user to change their password.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'auths/change_password.html', {
        'form': form,
        'user_role': request.user.role
        
    })
    
@login_required
def read_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    # Redirect to dashboard or any generic view
    return redirect('dashboard')  # Replace 'dashboard' with actual route name

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import FeedbackForm
from .models import Feedback, Notification, CustomUser

@login_required
def send_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.sender = request.user

            # Prevent sending feedback to self
            if feedback.sender == feedback.recipient:
                messages.error(request, "You can't send feedback to yourself.")
                return redirect('send_feedback')

            feedback.save()

            # Create notification for recipient
            Notification.objects.create(
                user=feedback.recipient,
                message=f"📨 New feedback from {feedback.sender.username}"
            )

            messages.success(request, "Feedback sent successfully.")
            return redirect('inbox')
    else:
        form = FeedbackForm()

        # Optional: limit recipient options (e.g., based on role)
        form.fields['recipient'].queryset = CustomUser.objects.exclude(id=request.user.id)

    return render(request, 'feedback/send_feedback.html', {'form': form})


@login_required
def inbox(request):
    feedbacks = Feedback.objects.filter(recipient=request.user).order_by('-timestamp')
    unread_count = feedbacks.filter(is_read=False).count()

    return render(request, 'feedback/inbox.html', {
        'feedbacks': feedbacks,
        'unread_count': unread_count
    })


@login_required
def feedback_detail(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk, recipient=request.user)

    # Mark feedback as read
    if not feedback.is_read:
        feedback.is_read = True
        feedback.save()

    if request.method == 'POST':
        reply_text = request.POST.get('reply')
        if reply_text:
            feedback.reply = reply_text
            feedback.save()

            # Create notification for original sender
            Notification.objects.create(
                user=feedback.sender,
                message=f"📬 Reply from {feedback.recipient.username} to your feedback."
            )

            messages.success(request, "Reply sent successfully.")
            return redirect('inbox')

    return render(request, 'feedback/detail.html', {'feedback': feedback})
