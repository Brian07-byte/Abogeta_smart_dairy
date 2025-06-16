from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from .models import MilkCollection, Payment, User, RateSetting
from .forms import MilkCollectionForm, PaymentForm
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from auths.models import CustomUser
from .models import MilkCollection,Payment,PaymentLog,Supplement,SupplementOrder
from django.db.models import Q
from .forms import *
from .models import RateSetting 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Q, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal

User = get_user_model()

# ----------- Helper Function for Admin Check -----------
def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


# ----------- Manage All Non-Superuser Users -----------
# View all non-superuser users
@login_required
@user_passes_test(is_admin)
def manage_users(request):
    # Get all farmers and collectors (excluding superusers)
    farmers = User.objects.filter(role='farmer', is_superuser=False)
    collectors = User.objects.filter(role='collector', is_superuser=False)

    farmer_data = []
    collector_data = []

    for user in farmers:
        total_milk = MilkCollection.objects.filter(farmer=user).aggregate(
            Sum('quantity_litres'))['quantity_litres__sum'] or 0
        total_paid = Payment.objects.filter(user=user, status='paid').aggregate(
            Sum('net_amount'))['net_amount__sum'] or 0
        total_pending = Payment.objects.filter(user=user, status='pending').aggregate(
            Sum('net_amount'))['net_amount__sum'] or 0

        farmer_data.append({
            'user': user,
            'total_milk': total_milk,
            'total_paid': total_paid,
            'total_pending': total_pending,
        })

    for user in collectors:
        total_collected = MilkCollection.objects.filter(collector=user).aggregate(
            Sum('quantity_litres'))['quantity_litres__sum'] or 0
        total_commission = Payment.objects.filter(user=user, status='paid').aggregate(
            Sum('net_amount'))['net_amount__sum'] or 0
        total_due = Payment.objects.filter(user=user, status='pending').aggregate(
            Sum('net_amount'))['net_amount__sum'] or 0

        collector_data.append({
            'user': user,
            'total_collected': total_collected,
            'total_commission': total_commission,
            'total_due': total_due,
        })

    return render(request, 'admin_dashboard/manage_users.html', {
        'farmer_data': farmer_data,
        'collector_data': collector_data,
    })



# ----------- View a Specific User -----------
@login_required
@user_passes_test(is_admin)
def view_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'admin_dashboard/view_user.html', {'user': user})


# ----------- Edit a User -----------
@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '').strip()

        if username and email and role:
            if user.is_superuser:
                messages.error(request, 'Cannot edit a superuser account.')
            else:
                user.username = username
                user.email = email
                user.role = role
                user.save()
                messages.success(request, 'User updated successfully.')
                return redirect('admin_dashboard:manage_users')
        else:
            messages.error(request, 'All fields are required.')

    return render(request, 'admin_dashboard/edit_user.html', {'user': user})


# ----------- Delete a User -----------
@login_required
@user_passes_test(is_admin)
@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.role == 'admin' or user.is_superuser:
        messages.error(request, 'You cannot delete another admin or superuser.')
    else:
        user.delete()
        messages.warning(request, 'User deleted successfully.')
    return redirect('admin_dashboard:manage_users')


# ----------- Deactivate a User -----------
@login_required
@user_passes_test(is_admin)
@require_POST
def deactivate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if not user.is_superuser:
        user.is_active = False
        user.save()
        messages.info(request, 'User account has been deactivated.')
    else:
        messages.error(request, 'Cannot deactivate a superuser.')
    return redirect('admin_dashboard:manage_users')


# ----------- Activate a User -----------
@login_required
@user_passes_test(is_admin)
@require_POST
def activate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, 'User account has been activated.')
    return redirect('admin_dashboard:manage_users')
#  ------------------Milk Management ---------------------

def is_admin_or_collector(user):
    return user.is_authenticated and (
        user.role in ['admin', 'collector'] or user.is_superuser
    )

def is_collector(user):
    return user.is_authenticated and (
        user.role == 'collector' or user.is_superuser
    )

def is_farmer(user):
    return user.is_authenticated and (
        user.role == 'farmer' or user.is_superuser
    )


# 🔹 Admin + All: View current milk payment & commission rates
from django.db import IntegrityError
from datetime import date, timedelta

def manage_rates(request):
    roles = ['farmer', 'collector']
    current_rates = {
        role: RateSetting.objects.filter(role=role).order_by('-effective_date').first()
        for role in roles
    }

    if request.method == 'POST':
        for role in roles:
            rate_value = request.POST.get(f'{role}_rate')
            effective = request.POST.get('effective_date') or str(date.today())

            if rate_value:
                try:
                    # Try to update existing rate for same date
                    existing_rate = RateSetting.objects.get(role=role, effective_date=effective)
                    if str(existing_rate.rate_per_litre) != rate_value:
                        existing_rate.rate_per_litre = rate_value
                        existing_rate.save()
                        messages.success(request, f"{role.capitalize()} rate updated for {effective}.")
                    else:
                        messages.info(request, f"No change for {role} rate on {effective}.")
                except RateSetting.DoesNotExist:
                    # Create new rate
                    RateSetting.objects.create(
                        role=role,
                        rate_per_litre=rate_value,
                        effective_date=effective
                    )
                    messages.success(request, f"{role.capitalize()} rate set for {effective}.")

        return redirect('admin_dashboard:manage_rates')

    return render(request, 'admin_dashboard/manage_rates.html', {
        'current_rates': current_rates,
        'today': date.today()
    })
    
# 🔹 Admin + Collector: Form to collect milk from a farmer
@login_required
@user_passes_test(is_admin_or_collector)
def add_milk_collection(request):
    if request.method == 'POST':
        form = MilkCollectionForm(request.POST, user=request.user)
        if form.is_valid():
            milk_collection = form.save(commit=False)

            # Assign collector automatically if user is a collector
            if request.user.role == 'collector':
                milk_collection.collector = request.user

            milk_collection.save()
            form.save_m2m()  # Save M2M fields if any

            # 🔸 Farmer Payment
            farmer_payment = Payment.objects.create(
                user=milk_collection.farmer,
                gross_amount=milk_collection.amount_payable_to_farmer,
                farmer_deduction=Decimal('0.00'),
                collector_deduction=Decimal('0.00'),
                net_amount=milk_collection.amount_payable_to_farmer,
                method="System Generated",
                remarks="Milk collection payment",
                status="pending",
                date_paid=timezone.now()
            )
            farmer_payment.milk_collections.add(milk_collection)

            # 🔸 Collector Payment
            if milk_collection.collector:
                collector_payment = Payment.objects.create(
                    user=milk_collection.collector,
                    gross_amount=milk_collection.commission_payable_to_collector,
                    farmer_deduction=Decimal('0.00'),
                    collector_deduction=Decimal('0.00'),
                    net_amount=milk_collection.commission_payable_to_collector,
                    method="System Generated",
                    remarks="Milk collection commission",
                    status="pending",
                    date_paid=timezone.now()
                )
                collector_payment.milk_collections.add(milk_collection)

            return redirect('admin_dashboard:milk_collection_list')
    else:
        form = MilkCollectionForm(user=request.user)

    return render(request, 'admin_dashboard/add_milk_collection.html', {'form': form})

def milk_collection_success_view(request):
    return render(request, 'admin_dashboard/collection_success.html')

# 🔹 Admin + Collector + Farmer: List milk collection history
from django.core.paginator import Paginator

@login_required
@user_passes_test(is_admin_or_collector)
def milk_collection_list(request):
    query = request.GET.get('q', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    collections = MilkCollection.objects.all()

    if query:
        collections = collections.filter(
            Q(farmer__username__icontains=query) |
            Q(collector__username__icontains=query)
        )

    if start_date:
        collections = collections.filter(date_collected__date__gte=start_date)
    if end_date:
        collections = collections.filter(date_collected__date__lte=end_date)

    # Summary totals
    total_quantity = collections.aggregate(Sum('quantity_litres'))['quantity_litres__sum'] or 0
    total_farmer_payment = collections.aggregate(Sum('amount_payable_to_farmer'))['amount_payable_to_farmer__sum'] or 0
    total_collector_commission = collections.aggregate(Sum('commission_payable_to_collector'))['commission_payable_to_collector__sum'] or 0

    # Pagination setup
    paginator = Paginator(collections, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'collections': page_obj,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
        'total_quantity': total_quantity,
        'total_farmer_payment': total_farmer_payment,
        'total_collector_commission': total_collector_commission,
        'page_obj': page_obj,
    }
    return render(request, 'admin_dashboard/milk_collection_list.html', context)


# ------detail --------
@login_required
@user_passes_test(is_admin_or_collector)
def milk_collection_detail(request, pk):
    collection = get_object_or_404(MilkCollection, pk=pk)

    # Ensure only assigned collector or admin/superuser can view
    if request.user != collection.collector and not request.user.is_superuser and request.user.role != 'admin':
        return render(request, '403.html')  # Optional: custom permission denied page

    return render(request, 'admin_dashboard/milk_collection_detail.html', {'collection': collection})
# edit/delete------------
@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def edit_milk_collection(request, pk):
    collection = get_object_or_404(MilkCollection, pk=pk)

    if request.method == 'POST':
        form = MilkCollectionForm(request.POST, instance=collection)
        if form.is_valid():
            form.save()
            messages.success(request, "Milk collection record updated successfully.")
            return redirect('admin_dashboard:milk_collection_detail', pk=pk)
        else:
            messages.error(request, "There was an error updating the record. Please check the form.")
    else:
        form = MilkCollectionForm(instance=collection)

    return render(request, 'admin_dashboard/edit_milk_collection.html', {
        'form': form,
        'collection': collection,
    })
# --------Delete-------
@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def delete_milk_collection(request, pk):
    collection = get_object_or_404(MilkCollection, pk=pk)

    if request.method == 'POST':
        collection.delete()
        return redirect('admin_dashboard:milk_collection_list')

    return render(request, 'admin_dashboard/delete_milk_collection_confirm.html', {'collection': collection})

# -----Milk summary----
from django.utils.timezone import now
@login_required
@user_passes_test(is_admin_or_collector)
def milk_summary_view(request):
    today = now().date()

    # Total stats
    total_quantity = MilkCollection.objects.aggregate(total=Sum('quantity_litres'))['total'] or 0
    total_farmers_payment = MilkCollection.objects.aggregate(total=Sum('amount_payable_to_farmer'))['total'] or 0
    total_collector_commission = MilkCollection.objects.aggregate(total=Sum('commission_payable_to_collector'))['total'] or 0

    # Daily stats
    daily_collections = MilkCollection.objects.filter(date_collected__date=today)
    daily_total = daily_collections.aggregate(total=Sum('quantity_litres'))['total'] or 0

    # By farmer
    farmer_summary = (
        MilkCollection.objects
        .values(farmer_username=F('farmer__username'))
        .annotate(total_milk=Sum('quantity_litres'), total_payment=Sum('amount_payable_to_farmer'))
        .order_by('-total_milk')
    )

    # By collector
    collector_summary = (
        MilkCollection.objects
        .values(collector_username=F('collector__username'))
        .annotate(total_milk=Sum('quantity_litres'), total_commission=Sum('commission_payable_to_collector'))
        .order_by('-total_milk')
    )

    context = {
        'total_quantity': total_quantity,
        'total_farmers_payment': total_farmers_payment,
        'total_collector_commission': total_collector_commission,
        'daily_total': daily_total,
        'farmer_summary': farmer_summary,
        'collector_summary': collector_summary,
        'today': today,
    }

    return render(request, 'admin_dashboard/milk_summary.html', context)

# 🔹 Admin only: Form to make a payment
# 📋 List all payments (with search & pagination)

from decimal import Decimal, ROUND_HALF_UP

    # overview
@login_required
@user_passes_test(lambda u: u.is_superuser or u.role == 'admin')
def payment_overview(request):
    today = now().date()

    all_payments = Payment.objects.all()
    farmer_payments = all_payments.filter(user__role='farmer')
    collector_payments = all_payments.filter(user__role='collector')

    # Filters
    status_filter = request.GET.get('status')
    method_filter = request.GET.get('method')

    filtered_payments = all_payments
    if status_filter:
        filtered_payments = filtered_payments.filter(status=status_filter)
    if method_filter:
        filtered_payments = filtered_payments.filter(method__icontains=method_filter)

    # Pagination
    paginator = Paginator(filtered_payments.order_by('-date_paid'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Totals
    total_gross = all_payments.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0
    total_net = all_payments.aggregate(Sum('net_amount'))['net_amount__sum'] or 0
    total_farmer_deductions = all_payments.aggregate(Sum('farmer_deduction'))['farmer_deduction__sum'] or 0
    total_collector_deductions = all_payments.aggregate(Sum('collector_deduction'))['collector_deduction__sum'] or 0

    # Status counts
    paid_count = all_payments.filter(status='paid').count()
    pending_count = all_payments.filter(status='pending').count()

    # Recent payments
    recent_farmer_payments = farmer_payments.select_related('user').order_by('-date_paid')[:5]
    recent_collector_payments = collector_payments.select_related('user').order_by('-date_paid')[:5]

    # Chart Data
    method_breakdown = (
        all_payments.values('method')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    chart_data = {
        "labels": [entry['method'] for entry in method_breakdown],
        "values": [entry['total'] for entry in method_breakdown],
    }

    context = {
        'total_gross': total_gross,
        'total_net': total_net,
        'total_farmer_deductions': total_farmer_deductions,
        'total_collector_deductions': total_collector_deductions,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'recent_farmer_payments': recent_farmer_payments,
        'recent_collector_payments': recent_collector_payments,
        'today': today,
        'page_obj': page_obj,
        'chart_data': chart_data,
    }

    return render(request, 'admin_dashboard/payment_overview.html', context)
# farmer list

@login_required
@user_passes_test(is_admin)
def farmer_payments_list(request):
    farmers = CustomUser.objects.filter(role='farmer')

    farmer_data = []
    for farmer in farmers:
        payments = Payment.objects.filter(user=farmer)
        if payments.exists():
            farmer_data.append({
                'farmer': farmer,
                'total_gross': payments.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0,
                'total_deductions': payments.aggregate(Sum('farmer_deduction'))['farmer_deduction__sum'] or 0,
                'total_net': payments.aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
                'payment_count': payments.count(),
            })

    context = {
        'farmer_data': farmer_data,
    }
    return render(request, 'admin_dashboard/farmer_payment_list.html', context)

# views.py
@login_required
@user_passes_test(is_admin)
def farmer_payment_detail(request, farmer_id):
    farmer = get_object_or_404(CustomUser, id=farmer_id, role='farmer')
    payments = Payment.objects.filter(user=farmer)

    total_gross = payments.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0
    total_deductions = payments.aggregate(Sum('farmer_deduction'))['farmer_deduction__sum'] or 0
    total_net = payments.aggregate(Sum('net_amount'))['net_amount__sum'] or 0

    context = {
        'farmer': farmer,
        'payments': payments,
        'total_gross': total_gross,
        'total_deductions': total_deductions,
        'total_net': total_net,
    }

    return render(request, 'admin_dashboard/farmer_payment_detail.html', context)


    
@login_required
@user_passes_test(is_admin)
def collector_payments_list(request):
    collectors = CustomUser.objects.filter(role='collector')

    collector_data = []
    for collector in collectors:
        payments = Payment.objects.filter(user=collector)
        if payments.exists():
            collector_data.append({
                'collector': collector,
                'total_gross': payments.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0,
                'total_deductions': payments.aggregate(Sum('collector_deduction'))['collector_deduction__sum'] or 0,
                'total_net': payments.aggregate(Sum('net_amount'))['net_amount__sum'] or 0,
                'payment_count': payments.count(),
            })

    context = {
        'collector_data': collector_data,
    }
    return render(request, 'admin_dashboard/collector_payment_list.html', context)
    
@login_required
@user_passes_test(is_admin)
def collector_payment_detail(request, collector_id):
    collector = get_object_or_404(CustomUser, id=collector_id, role='collector')
    payments = Payment.objects.filter(user=collector)

    total_gross = payments.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0
    total_deductions = payments.aggregate(Sum('collector_deduction'))['collector_deduction__sum'] or 0
    total_net = payments.aggregate(Sum('net_amount'))['net_amount__sum'] or 0

    context = {
        'collector': collector,
        'payments': payments,
        'total_gross': total_gross,
        'total_deductions': total_deductions,
        'total_net': total_net,
    }
    return render(request, 'admin_dashboard/collector_payment_detail.html', context)
# generate payments
from django.core.mail import send_mail 
@login_required
@user_passes_test(is_admin)
def generate_payments(request):
    if request.method == 'GET':
        # Preview: fetch unpaid milk collections
        farmers = CustomUser.objects.filter(role='farmer')
        collectors = CustomUser.objects.filter(role='collector')

        unpaid_farmers = []
        unpaid_collectors = []

        for farmer in farmers:
            deliveries = MilkCollection.objects.filter(farmer=farmer, is_paid=False, payments=None)
            if deliveries.exists():
                gross = sum(Decimal(d.quantity_litres) * d.farmer_rate_at_collection for d in deliveries)
                deduction = gross * Decimal('0.05')
                net = gross - deduction
                unpaid_farmers.append({'user': farmer, 'gross': gross, 'deduction': deduction, 'net': net, 'count': deliveries.count()})

        for collector in collectors:
            collections = MilkCollection.objects.filter(collector=collector, is_paid=False, payments=None)
            if collections.exists():
                gross = sum(Decimal(c.quantity_litres) * c.collector_rate_at_collection for c in collections)
                deduction = gross * Decimal('0.03')
                net = gross - deduction
                unpaid_collectors.append({'user': collector, 'gross': gross, 'deduction': deduction, 'net': net, 'count': collections.count()})

        return render(request, 'admin_dashboard/generate_payments.html', {
            'unpaid_farmers': unpaid_farmers,
            'unpaid_collectors': unpaid_collectors,
        })

    elif request.method == 'POST':
        created_payments = []

        farmers = CustomUser.objects.filter(role='farmer')
        for farmer in farmers:
            deliveries = MilkCollection.objects.filter(farmer=farmer, is_paid=False, payments=None)
            if deliveries.exists():
                gross = sum(Decimal(d.quantity_litres) * d.farmer_rate_at_collection for d in deliveries)
                deduction = gross * Decimal('0.05')
                net = gross - deduction

                if not Payment.objects.filter(user=farmer, gross_amount=gross, net_amount=net, status='pending').exists():
                    payment = Payment.objects.create(
                        user=farmer,
                        gross_amount=gross,
                        farmer_deduction=deduction,
                        net_amount=net,
                        method='Bank Transfer',
                        status='pending',
                        generated_at=timezone.now()
                    )
                    payment.milk_collections.set(deliveries)
                    created_payments.append(payment)

        collectors = CustomUser.objects.filter(role='collector')
        for collector in collectors:
            collections = MilkCollection.objects.filter(collector=collector, is_paid=False, payments=None)
            if collections.exists():
                gross = sum(Decimal(c.quantity_litres) * c.collector_rate_at_collection for c in collections)
                deduction = gross * Decimal('0.03')
                net = gross - deduction

                if not Payment.objects.filter(user=collector, gross_amount=gross, net_amount=net, status='pending').exists():
                    payment = Payment.objects.create(
                        user=collector,
                        gross_amount=gross,
                        collector_deduction=deduction,
                        net_amount=net,
                        method='Bank Transfer',
                        status='pending',
                        generated_at=timezone.now()
                    )
                    payment.milk_collections.set(collections)
                    created_payments.append(payment)

        if created_payments:
            # Optional email notification (can configure settings.py with email backend)
            send_mail(
                'New Payments Generated',
                f'{len(created_payments)} new payments have been generated.',
                'admin@system.com',
                ['finance@company.com'],
                fail_silently=True,
            )
            messages.success(request, f"{len(created_payments)} payments generated successfully.")
        else:
            messages.info(request, "No new payments found to generate.")

        return redirect('admin_dashboard:payment_overview')

@user_passes_test(is_admin)
def batch_update_payments(request):
    if request.method == "POST":
        ids = request.POST.getlist('payment_ids')
        action = request.POST.get('action')

        if not ids:
            messages.warning(request, "No payments selected.")
            return redirect('admin_dashboard:payment_overview')

        if action not in ["approve", "reverse"]:
            messages.error(request, "Invalid action selected.")
            return redirect('admin_dashboard:payment_overview')

        payments = Payment.objects.filter(id__in=ids)

        if not payments.exists():
            messages.error(request, "No matching payments found.")
            return redirect('admin_dashboard:payment_overview')

        if action == "approve":
            updated_count = 0
            for payment in payments:
                if payment.status != "paid":
                    payment.status = "paid"
                    payment.save()
                    updated_count += 1
            messages.success(request, f"{updated_count} payment(s) approved successfully.")
        
        elif action == "reverse":
            updated_count = 0
            for payment in payments:
                if payment.status != "pending":
                    payment.status = "pending"
                    payment.save()
                    updated_count += 1
            messages.success(request, f"{updated_count} payment(s) reversed successfully.")

    return redirect('admin_dashboard:payment_overview')
# Utility: Check milk quota this month
def has_farmer_discount(user):
    if user.role != 'farmer':
        return False

    now = timezone.now()
    start_of_month = now.replace(day=1)
    end_of_month = now.replace(day=28) + timezone.timedelta(days=4)
    end_of_month = end_of_month.replace(day=1) - timezone.timedelta(days=1)

    total_milk = MilkCollection.objects.filter(
        user=user,
        date__range=(start_of_month, end_of_month)
    ).aggregate(total=Sum('litres'))['total'] or 0

    return total_milk >= 200


# LIST
@user_passes_test(is_admin)
def supplement_list(request):
    query = request.GET.get("q", "")
    supplements = Supplement.objects.all()

    if query:
        supplements = supplements.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    paginator = Paginator(supplements, 10)
    page = request.GET.get("page")
    supplements = paginator.get_page(page)

    return render(request, "inventory/supplement_list.html", {
        "supplements": supplements,
        "query": query,
        "title": "Supplements Overview",
    })


# ADD
@user_passes_test(is_admin)
def supplement_add(request):
    if request.method == "POST":
        form = SupplementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Supplement added successfully.")
            return redirect("admin_dashboard:supplement_list")
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = SupplementForm()

    return render(request, "inventory/supplement_form.html", {
        "form": form,
        "title": "Add Supplement"
    })


# EDIT
@user_passes_test(is_admin)
def supplement_edit(request, pk):
    supplement = get_object_or_404(Supplement, pk=pk)

    if request.method == "POST":
        form = SupplementForm(request.POST, request.FILES, instance=supplement)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Supplement updated successfully.")
            return redirect("admin_dashboard:supplement_list")
        else:
            messages.error(request, "❌ Update failed. Please check the form.")
    else:
        form = SupplementForm(instance=supplement)

    return render(request, "inventory/supplement_form.html", {
        "form": form,
        "edit": True,
        "title": "Edit Supplement"
    })


# DELETE
@user_passes_test(is_admin)
def supplement_delete(request, pk):
    supplement = get_object_or_404(Supplement, pk=pk)
    supplement.delete()
    messages.success(request, f"🗑️ Supplement '{supplement.name}' deleted.")
    return redirect("admin_dashboard:supplement_list")
# order list

# List Supplement Orders with optional status filtering
@user_passes_test(is_admin)
def supplement_orders(request):
    status_filter = request.GET.get("status")
    orders = SupplementOrder.objects.select_related("user").prefetch_related("cart_items__supplement").all()

    if status_filter:
        orders = orders.filter(status=status_filter)

    paginator = Paginator(orders, 10)
    page = request.GET.get("page")
    orders = paginator.get_page(page)

    return render(request, "inventory/supplement_orders.html", {
        "orders": orders,
        "status_filter": status_filter
    })


# View a single supplement order in detail
@user_passes_test(is_admin)
def supplement_order_detail(request, pk):
    order = get_object_or_404(SupplementOrder.objects.select_related("user").prefetch_related("cart_items__supplement"), pk=pk)
    
    # For each cart item, we have supplement and quantity info
    return render(request, "inventory/supplement_order_detail.html", {
        "order": order,
        "cart_items": order.cart_items.all()
    })


# Mark an order as paid
@user_passes_test(is_admin)
def mark_order_paid(request, pk):
    order = get_object_or_404(SupplementOrder, pk=pk)
    order.mark_as_paid()
    messages.success(request, f"Order #{order.id} by {order.user.username} marked as PAID.")
    return redirect("admin_dashboard:supplement_orders")

# ANALYTICS
from django.db.models import Sum, Count, Avg, F
from django.utils.timezone import now
@user_passes_test(is_admin)
def analytics_dashboard(request):
    today = now().date()
    month_start = date(today.year, today.month, 1)

    # Milk data
    milk_data = MilkCollection.objects.aggregate(
        total_litres=Sum('quantity_litres'),
        this_month_litres=Sum('quantity_litres', filter=Q(date_collected__date__gte=month_start)),
        avg_fat=Avg('fat_content')
    )

    # Payment data - using correct fields
    payment_data = Payment.objects.aggregate(
        total_paid=Sum('gross_amount', filter=Q(status='paid')),
        total_pending=Sum('gross_amount', filter=Q(status='pending')),
        avg_payment=Avg('gross_amount')
    )

    gross_amount = Payment.objects.aggregate(total=Sum('gross_amount'))['total'] or 0
    farmer_ded = Payment.objects.aggregate(ded=Sum('farmer_deduction'))['ded'] or 0
    collector_ded = Payment.objects.aggregate(ded=Sum('collector_deduction'))['ded'] or 0
    net_amount = Payment.objects.aggregate(net=Sum('net_amount'))['net'] or 0
    available_balance = net_amount

    # Orders and Revenue
    order_counts = SupplementOrder.objects.values('status').annotate(count=Count('id'))
    total_orders = SupplementOrder.objects.count()
    orders_this_month = SupplementOrder.objects.filter(created_at__date__gte=month_start).count()
    supplement_revenue = SupplementOrder.objects.aggregate(total=Sum('total_price'))['total'] or 0

    # Top Farmers & Collectors
    top_farmers = MilkCollection.objects.values('farmer__username').annotate(
        total=Sum('quantity_litres')
    ).order_by('-total')[:5]

    top_collectors = MilkCollection.objects.values('collector__username').annotate(
        total=Sum('quantity_litres')
    ).order_by('-total')[:5]

    # Stock Overview
    supplements = Supplement.objects.all()
    stock_summary = supplements.values('name', 'stock')
    out_of_stock = supplements.filter(stock=0).count()

    context = {
        'total_litres': milk_data['total_litres'] or 0,
        'litres_this_month': milk_data['this_month_litres'] or 0,
        'avg_fat': milk_data['avg_fat'] or 0,

        'total_paid': payment_data['total_paid'] or 0,
        'total_pending': payment_data['total_pending'] or 0,
        'avg_payment': payment_data['avg_payment'] or 0,

        'gross_amount': gross_amount,
        'farmer_ded': farmer_ded,
        'collector_ded': collector_ded,
        'net_amount': net_amount,
        'available_balance': available_balance,

        'order_status_counts': order_counts,
        'total_orders': total_orders,
        'orders_this_month': orders_this_month,
        'supplement_revenue': supplement_revenue,

        'top_farmers': top_farmers,
        'top_collectors': top_collectors,

        'stock_summary': stock_summary,
        'out_of_stock': out_of_stock,
    }

    return render(request, 'analytics/analytics_dashboard.html', context)