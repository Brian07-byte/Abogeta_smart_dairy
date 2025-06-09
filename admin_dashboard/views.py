from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from auths.models import CustomUser
from .models import MilkCollection,Payment
from django.db.models import Q
from .forms import PaymentForm
from .models import RateSetting
from .forms import RateSettingForm 

User = get_user_model()

# Admin role check
def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

# View all non-superuser users
@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = CustomUser.objects.exclude(is_superuser=True)
    return render(request, 'admin_dashboard/manage_users.html', {'users': users})

# View a specific user by ID
@login_required
@user_passes_test(is_admin)
def view_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'admin_dashboard/view_user.html', {'user': user})

# Edit user
@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '').strip()

        if username and email and role:
            user.username = username
            user.email = email
            user.role = role
            user.save()
            messages.success(request, 'User updated successfully.')
            return redirect('admin_dashboard:manage_users')
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'admin_dashboard/edit_user.html', {'user': user})

# Delete user
@login_required
@user_passes_test(is_admin)
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.role != 'admin':
        user.delete()
        messages.warning(request, 'User deleted successfully.')
    else:
        messages.error(request, 'You cannot delete another admin.')
    return redirect('admin_dashboard:manage_users')

# Deactivate user
@login_required
@user_passes_test(is_admin)
@require_POST
def deactivate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False
    user.save()
    messages.info(request, 'User deactivated.')
    return redirect('admin_dashboard:manage_users')

# Activate user
@login_required
@user_passes_test(is_admin)
@require_POST
def activate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, 'User activated.')
    return redirect('admin_dashboard:manage_users')

# MILK OVERVIEW 
def milk_overview(request):
    query_user = request.GET.get('user')
    query_date = request.GET.get('date')

    collections = MilkCollection.objects.select_related('collector').order_by('-date_collected')

    if query_user:
        collections = collections.filter(collector__username__icontains=query_user)
    if query_date:
        collections = collections.filter(date_collected=query_date)

    total_milk = sum(c.quantity_litres for c in collections)
    total_earnings = sum(c.total_price() for c in collections)

    return render(request, 'admin_dashboard/milk_overview.html', {
        'collections': collections,
        'total_milk': total_milk,
        'total_earnings': total_earnings,
        'query_user': query_user,
        'query_date': query_date,
    })
    
def create_milk(request):
    users = User.objects.all()
    if request.method == 'POST':
        user_id = request.POST['collector']
        qty = float(request.POST['quantity'])
        fat = float(request.POST['fat'])
        rate = float(request.POST['rate'])
        MilkCollection.objects.create(
            collector_id=user_id,
            quantity_litres=qty,
            fat_content=fat,
            price_per_litre=rate,
        )
        messages.success(request, 'Milk record created successfully.')
        return redirect('admin_dashboard:milk_overview')
    return render(request, 'admin_dashboard/milk_create.html', {'users': users})


def edit_milk(request, pk):
    record = get_object_or_404(MilkCollection, pk=pk)
    users = User.objects.all()
    if request.method == 'POST':
        record.collector_id = request.POST['collector']
        record.quantity_litres = float(request.POST['quantity'])
        record.fat_content = float(request.POST['fat'])
        record.price_per_litre = float(request.POST['rate'])
        record.save()
        messages.success(request, 'Milk record updated.')
        return redirect('admin_dashboard:milk_overview')
    return render(request, 'admin_dashboard/milk_edit.html', {'record': record, 'users': users})


def delete_milk(request, pk):
    record = get_object_or_404(MilkCollection, pk=pk)
    record.delete()
    messages.success(request, 'Milk record deleted.')
    return redirect('admin_dashboard:milk_overview')

def farmer_summary(request):
    query = request.GET.get('username')
    user = None
    collections = []
    total_milk = 0
    total_earnings = 0

    if query:
        try:
            user = User.objects.get(username__iexact=query)
            collections = MilkCollection.objects.filter(collector=user)
            total_milk = collections.aggregate(Sum('quantity_litres'))['quantity_litres__sum'] or 0
            total_earnings = sum(c.total_price() for c in collections)  # Use the method here
        except User.DoesNotExist:
            user = None

    return render(request, 'admin_dashboard/farmer_summary.html', {
        'user_obj': user,
        'collections': collections,
        'total_milk': total_milk,
        'total_earnings': total_earnings,
        'query': query,
    })

# -----------------------------
# Record a payment for a user
# -----------------------------
def record_payment(request):
    users = User.objects.all()

    if request.method == 'POST':
        user_id = request.POST.get('user')
        payee_role = request.POST.get('payee_role')
        method = request.POST.get('method')
        remarks = request.POST.get('remarks', '')

        user = get_object_or_404(User, id=user_id)

        # Get rate per litre based on role
        try:
            rate = RateSetting.objects.get(role=payee_role).rate_per_litre
        except RateSetting.DoesNotExist:
            messages.error(request, f"No rate set for {payee_role}.")
            return redirect('admin_dashboard:record_payment')

        # Calculate total litres and payment
        if payee_role == 'collector':
            total_litres = MilkCollection.objects.filter(collector=user).aggregate(
                total=Sum('quantity_litres')
            )['total'] or 0
        elif payee_role == 'farmer':
            # Placeholder: Implement FarmerMilkDelivery model to track farmer deliveries
            messages.warning(request, "Farmer payment calculation not implemented yet.")
            return redirect('admin_dashboard:record_payment')
        else:
            messages.error(request, "Invalid payee role.")
            return redirect('admin_dashboard:record_payment')

        amount = round(total_litres * float(rate), 2)

        Payment.objects.create(
            user=user,
            amount=amount,
            method=method,
            remarks=remarks,
            payee_role=payee_role,
        )

        messages.success(request, f"Payment of Ksh {amount} recorded for {user.username} as {payee_role}.")
        return redirect('admin_dashboard:record_payment')

    return render(request, 'admin_dashboard/payment_create.html', {
        'users': users
    })

# -------------------------------------------
# View payment history for a specific collector
# -------------------------------------------
def collector_payment_history(request, user_id):
    user = get_object_or_404(User, id=user_id)
    payments = Payment.objects.filter(user=user, payee_role='collector').order_by('-date')

    return render(request, 'admin_dashboard/collector_payment_history.html', {
        'user': user,
        'payments': payments,
    })

# -------------------------------------------
# View payment history for a specific farmer
# -------------------------------------------
def farmer_payment_history(request, user_id):
    user = get_object_or_404(User, id=user_id)
    payments = Payment.objects.filter(user=user, payee_role='farmer').order_by('-date')

    return render(request, 'admin_dashboard/farmer_payment_history.html', {
        'user': user,
        'payments': payments,
    })

# -------------------------------------------
# View + add/update rate settings (admin)
# -------------------------------------------
def rate_settings_view(request):
    existing_settings = RateSetting.objects.all()

    if request.method == 'POST':
        form = RateSettingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Rate updated successfully.")
            return redirect('admin_dashboard:rate_settings')
    else:
        form = RateSettingForm()

    return render(request, 'admin_dashboard/rate_settings.html', {
        'form': form,
        'existing_settings': existing_settings,
    })

# -------------------------------------------
# List all collectors (for admin navigation)
# -------------------------------------------
def collector_list(request):
    collectors = User.objects.filter(groups__name='Collector')  # Optional: filter by group
    return render(request, 'admin_dashboard/collector_list.html', {'collectors': collectors})

# -------------------------------------------
# List all farmers (for admin navigation)
# -------------------------------------------
def farmer_list(request):
    farmers = User.objects.filter(groups__name='Farmer')  # Optional: filter by group
    return render(request, 'admin_dashboard/farmer_list.html', {'farmers': farmers})