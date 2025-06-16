from django.contrib import messages
import random
from django.db import transaction
from django.forms import DecimalField
from django.db.models import F, ExpressionWrapper, DecimalField
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from datetime import datetime, timezone
from admin_dashboard.models import CartItem, MilkCollection, Payment, Supplement, SupplementOrder
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models import Q
from django.utils import timezone

from auths.models import Feedback
from farmer.forms import FeedbackForm, FeedbackReplyForm
  # ✅ this is correct


@login_required
def milk_history(request):
    user = request.user

    # Get filters
    month = request.GET.get('month')
    year = request.GET.get('year')

    # Base queryset
    records = (
        MilkCollection.objects
        .filter(farmer=user)
        .select_related('collector', 'collection_point')
        .prefetch_related('payments')  # Use this for ManyToMany
        .order_by('-date_collected')
    )

    # Apply filters if provided
    if month:
        records = records.filter(date_collected__month=month)
    if year:
        records = records.filter(date_collected__year=year)

    # Pagination (10 per page)
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Summary values
    total_litres = records.aggregate(total=Sum('quantity_litres'))['total'] or 0
    total_earnings = records.aggregate(total=Sum('amount_payable_to_farmer'))['total'] or 0

    # Add computed field for display
    for record in page_obj:
        payments = record.payments.all()
        record.is_paid = any(payment.status == 'paid' for payment in payments)

    # Context
    context = {
        'page_obj': page_obj,
        'month': month,
        'year': year,
        'total_litres': total_litres,
        'total_earnings': total_earnings,
        'months': range(1, 13),
        'years': range(2023, datetime.now().year + 1),
    }

    return render(request, 'milk_view/milk_history.html', context)

@login_required
def milk_detail(request, record_id):
    record = get_object_or_404(MilkCollection, id=record_id)

    # Check ownership or admin
    if request.user != record.farmer and not request.user.is_staff:
        messages.error(request, "You do not have permission to view this record.")
        return redirect('milk_history')

    # Handle payment approval
    if request.method == "POST" and request.user.is_staff:
        payments = record.payments.all()
        if payments.exists():
            payment = payments.first()
            payment.status = 'paid'
            payment.save()
            messages.success(request, "Payment marked as paid.")
        else:
            # If no payment exists, optionally create one
            Payment.objects.create(
                farmer=record.farmer,
                amount=record.amount_payable_to_farmer,
                status='paid'
            )
            record.refresh_from_db()
            messages.success(request, "Payment created and marked as paid.")
        return redirect('milk_detail', record_id=record.id)

    return render(request, 'milk_view/milk_detail.html', {'record': record})

#     PAYMENTS

@login_required
def my_payments_view(request):
    user = request.user
    payments = Payment.objects.filter(user=user)

    # Search
    query = request.GET.get('search')
    if query:
        payments = payments.filter(
            Q(method__icontains=query) | Q(remarks__icontains=query)
        )

    # Filter by status
    status = request.GET.get('status')
    if status in ['paid', 'pending']:
        payments = payments.filter(status=status)

    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        payments = payments.filter(date_paid__gte=start_date)
    if end_date:
        payments = payments.filter(date_paid__lte=end_date)

    # Pagination
    paginator = Paginator(payments.order_by('-date_paid'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Dashboard summary calculations
    total_paid = Payment.objects.filter(user=user, status='paid').aggregate(total=Sum('net_amount'))['total'] or 0
    pending_amount = Payment.objects.filter(user=user, status='pending').aggregate(total=Sum('net_amount'))['total'] or 0
    total_farmer_deductions = Payment.objects.filter(user=user).aggregate(total=Sum('farmer_deduction'))['total'] or 0

    return render(request, 'payments/payments.html', {
        'payments': page_obj,
        'query': query,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
        'page_obj': page_obj,

        # Dashboard stats
        'total_paid': total_paid,
        'pending_amount': pending_amount,
        'total_farmer_deductions': total_farmer_deductions,
    })

@login_required
def view_milk_for_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    milk_records = payment.milk_collections.all()

    return render(request, 'payments/milk_records_for_payment.html', {
        'payment': payment,
        'milk_records': milk_records,
    })
    
#       SUPPLIMENTS LOGIC

def get_discount_for_farmer(user):
    """
    Apply a random discount if the farmer delivered 200+ litres 
    within the current half of the month.
    """
    now = timezone.now()
    start_of_month = now.replace(day=1)

    # Define mid-month boundary
    mid_month_day = 15
    mid_month = now.replace(day=mid_month_day)

    if now.day < mid_month_day:
        period_start = start_of_month
        period_end = mid_month
    else:
        period_start = mid_month
        # End of the period is now (up to current date)
        period_end = now

    # Calculate total litres collected in the current half-month period
    total_litres = MilkCollection.objects.filter(
        farmer=user,
        date_collected__range=(period_start, period_end)
    ).aggregate(total=Sum('quantity_litres'))['total'] or 0

    # Return random discount if threshold met
    if total_litres >= 200:
        return random.choice([2, 5, 8, 12])
    
    return 0

@login_required
def supplement_list(request):
    search_query = request.GET.get('q', '')
    in_stock_filter = request.GET.get('in_stock', '')

    supplements = Supplement.objects.filter(is_active=True)

    # Search logic
    if search_query:
        supplements = supplements.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Stock filter logic
    if in_stock_filter == '1':
        supplements = supplements.filter(stock__gt=0)

    # Get dynamic discount for this farmer
    discount = get_discount_for_farmer(request.user)

    # Apply discount to each supplement object dynamically
    for sup in supplements:
        sup.dynamic_discount = discount
        sup.final_price = sup.price - (sup.price * discount / 100)

    # Pagination
    paginator = Paginator(supplements, 10)  # Show 10 per page
    page = request.GET.get('page')
    supplements_page = paginator.get_page(page)

    context = {
        'supplements': supplements_page,
        'search_query': search_query,
        'in_stock_filter': in_stock_filter,
        'applied_discount': discount,
    }
    return render(request, 'supplements/list.html', context)

# ADD TO CART
@require_POST
@login_required
def add_to_cart(request, supplement_id):
    supplement = get_object_or_404(Supplement, id=supplement_id, is_active=True)

    if not supplement.is_in_stock():
        return JsonResponse({'success': False, 'message': "Out of stock"}, status=400)

    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': "Invalid quantity"}, status=400)

    if quantity > supplement.stock:
        return JsonResponse({'success': False, 'message': f"Only {supplement.stock} in stock"}, status=400)

    try:
        discount = get_discount_for_farmer(request.user) or 0
        discount_decimal = Decimal(str(discount))
        price = Decimal(str(supplement.price))
        discounted_price = round(price - (price * discount_decimal / 100), 2)
    except (InvalidOperation, TypeError):
        return JsonResponse({'success': False, 'message': "Price calculation error"}, status=500)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        supplement=supplement,
        defaults={
            'quantity': quantity,
            'price_at_order': discounted_price,
            'discount_applied': discount
        }
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.price_at_order = discounted_price
        cart_item.discount_applied = discount
        cart_item.save()

    # ✅ Sum quantities instead of counting rows
    cart_count = CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))['total'] or 0

    return JsonResponse({
        'success': True,
        'message': f"{supplement.name} added to cart with {discount}% discount.",
        'cart_count': cart_count
    })
    
@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('supplement')

    # Annotate each cart item with subtotal = price_at_order * quantity
    for item in cart_items:
        item.subtotal = item.price_at_order * item.quantity

    # Calculate total amount and total quantity
    total_amount = sum(item.subtotal for item in cart_items)
    total_quantity = sum(item.quantity for item in cart_items)

    # Check if any discount applied
    has_discount = any(item.discount_applied > 0 for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'total_quantity': total_quantity,
        'has_discount': has_discount,
        'is_cart_empty': not cart_items.exists()
    }

    return render(request, 'supplements/view_cart.html', context)

@login_required
def increase_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if item.quantity < item.supplement.stock:
        item.quantity += 1
        item.save()
    return redirect('view_cart')

@login_required
def decrease_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect('view_cart')

@login_required
def delete_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('view_cart')

@login_required
def clear_cart(request):
    CartItem.objects.filter(user=request.user).delete()
    return redirect('view_cart')
@login_required
@transaction.atomic
def checkout_view(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('supplement_list')

    total_price = sum(item.get_total_price() for item in cart_items)

    # Get farmer's unpaid milk earnings
    unpaid_earnings = Decimal('0.00')
    if user.role == 'farmer':
        unpaid_earnings = MilkCollection.objects.filter(farmer=user, is_paid=False).aggregate(
            total=Sum('amount_payable_to_farmer')
        )['total'] or Decimal('0.00')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        phone = request.POST.get('mpesa_phone', '').strip()

        if payment_method == 'deduction' and user.role == 'farmer':
            if unpaid_earnings < total_price:
                messages.error(request, "Insufficient milk earnings to cover the cost.")
                return redirect('checkout')

            # Deduct milk earnings
            collections = MilkCollection.objects.filter(farmer=user, is_paid=False).order_by('date_collected')
            remaining = total_price
            used_collections = []

            for collection in collections:
                if remaining <= 0:
                    break
                payout = collection.amount_payable_to_farmer
                if payout <= remaining:
                    used_collections.append(collection)
                    remaining -= payout
                else:
                    messages.error(request, "Partial deductions are not supported currently.")
                    return redirect('checkout')

            for c in used_collections:
                c.is_paid = True
                c.save()

            payment = Payment.objects.create(
                user=user,
                gross_amount=total_price,
                farmer_deduction=total_price,
                net_amount=0,
                method='milk_deduction',
                status='paid'
            )
            payment.milk_collections.set(used_collections)

        elif payment_method == 'mpesa':
            if not phone:
                messages.error(request, "Enter your M-Pesa phone number.")
                return redirect('checkout')

            payment = Payment.objects.create(
                user=user,
                gross_amount=total_price,
                net_amount=total_price,
                method='mpesa',
                remarks=f"M-Pesa payment by {phone}",
                status='paid'
            )

        else:
            messages.error(request, "Invalid payment method.")
            return redirect('checkout')

        # Create the order
        order = SupplementOrder.objects.create(
            user=user,
            total_price=total_price,
            payment_method=payment_method,
            status='paid' if payment_method == 'mpesa' else 'pending',
        )
        order.cart_items.set(cart_items)

        # 🔽 Reduce stock for each supplement
        for item in cart_items:
            supplement = item.supplement
            if supplement.stock >= item.quantity:
                supplement.stock -= item.quantity
                supplement.save()
            else:
                messages.error(request, f"Insufficient stock for {supplement.name}.")
                transaction.set_rollback(True)
                return redirect('checkout')

        # Clear cart
        cart_items.delete()

        messages.success(request, "Order placed successfully.")
        return redirect('order_summary')

    return render(request, 'supplements/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'unpaid_earnings': unpaid_earnings,
    })

@login_required
def order_summary_view(request):
    user = request.user
    latest_order = None
    cart_items = []
    payment = None
    milk_collections = []

    try:
        latest_order = SupplementOrder.objects.filter(user=user).latest('created_at')
        cart_items = latest_order.cart_items.all()

        # FIXED: Use correct field name instead of 'timestamp'
        payment = Payment.objects.filter(user=user, date_paid__lte=latest_order.created_at).order_by('-date_paid').first()

        if payment and payment.method == 'milk_deduction':
            milk_collections = payment.milk_collections.all()

    except SupplementOrder.DoesNotExist:
        pass

    return render(request, 'supplements/order_summary.html', {
        'order': latest_order,
        'cart_items': cart_items,
        'payment': payment,
        'milk_collections': milk_collections
    })

@login_required
def order_list_view(request):
    user = request.user
    orders = SupplementOrder.objects.filter(user=user).order_by('-created_at')  # assuming there's a created_at field

    return render(request, 'supplements/order_list.html', {
        'orders': orders
    })
    
#     feedback

@login_required
def submit_feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST, user=request.user)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.sender = request.user
            feedback.save()
            messages.success(request, "Feedback sent successfully.")
            return redirect('feedback_sent')
    else:
        form = FeedbackForm(user=request.user)

    return render(request, 'feedback/feedback_submit.html', {'form': form})


# View Sent Feedbacks
@login_required
def feedback_sent_view(request):
    feedbacks = Feedback.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'feedback/feedback_sent.html', {'feedbacks': feedbacks})


# View Received Feedbacks
@login_required
def feedback_received_view(request):
    feedbacks = Feedback.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'feedback/feedback_received.html', {'feedbacks': feedbacks})


# Reply to Feedback
@login_required
def feedback_reply_view(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id, recipient=request.user)

    if request.method == 'POST':
        form = FeedbackReplyForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            feedback.is_read = True
            feedback.save()
            messages.success(request, "Reply sent successfully.")
            return redirect('feedback_received')
    else:
        form = FeedbackReplyForm(instance=feedback)

    return render(request, 'feedback/feedback_reply.html', {'form': form, 'feedback': feedback})