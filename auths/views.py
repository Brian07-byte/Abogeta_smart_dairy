from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import *
from .models import Notification


# ----------------- Home ------------------
def home_redirect(request):
    if request.user.is_authenticated:
        user = request.user
        if user.role == 'admin' or user.is_superuser:
            return redirect('admin_dashboard:manage_users')  # or 'admin_dashboard:admin_dashboard'
        elif user.role == 'farmer':
            return redirect('auths:farmer_dashboard')
        elif user.role == 'collector':
            return redirect('auths:collector_dashboard')
        else:
            # Default redirect if role unknown
            return redirect('auths:farmer_dashboard')  # or any default page

    # If not authenticated, show login and register forms
    login_form = CustomLoginForm()
    register_form = CustomUserCreationForm()
    return render(request, 'auths/home.html', {
        'login_form': login_form,
        'register_form': register_form,
    })

# ----------------- Register ------------------
@csrf_protect
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! You are now logged in.")
            return redirect_role_dashboard(user)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'auths/register.html', {'register_form': form})


# ----------------- Login ------------------
@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect_role_dashboard(user)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()
    return render(request, 'auths/login.html', {'login_form': form})


# ----------------- Logout ------------------
def logout_view(request):
    logout(request)
    return redirect('home')


# ----------------- Role-based Redirect ------------------
def redirect_role_dashboard(user):
    print("DEBUG:", user.role)
    if user.role == 'farmer':
        return redirect('farmer_dashboard')
    elif user.role == 'collector':
        return redirect('collector_dashboard')
    elif user.is_superuser or user.role == 'admin':
        return redirect('admin_dashboard')
    return redirect('home')


# ----------------- Dashboards ------------------
@login_required
def farmer_dashboard(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:5]
    return render(request, 'auths/farmer_dashboard.html', {
        'notifications': notifications,
        'user_role': 'farmer'
    })


@login_required
def collector_dashboard(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:5]
    return render(request, 'auths/collector_dashboard.html', {
        'notifications': notifications,
        'user_role': 'collector'
    })


@login_required
def admin_dashboard(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:5]
    return render(request, 'auths/admin_dashboard.html', {
        'notifications': notifications,
        'user_role': 'admin'
    })


# ----------------- User Profile ------------------
@login_required
def profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)

    user_role = getattr(request.user, 'role', 'user')
    return render(request, 'auths/profile.html', {
        'u_form': u_form,
        'user_role': user_role,
    })


# ----------------- Change Password ------------------
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keeps user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    user_role = getattr(request.user, 'role', 'user')
    return render(request, 'auths/change_password.html', {
        'form': form,
        'user_role': user_role,
    })
