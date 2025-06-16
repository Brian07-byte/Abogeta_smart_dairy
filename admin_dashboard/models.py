from django.db import models
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from auths.models import CustomUser  # ✅ Explicitly use CustomUser
from django.contrib.auth import get_user_model
User = get_user_model()


# -------------------- RateSetting --------------------
class RateSetting(models.Model):
    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('collector', 'Collector'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    rate_per_litre = models.DecimalField(max_digits=6, decimal_places=2)
    effective_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('role', 'effective_date')
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.role.capitalize()} Rate: {self.rate_per_litre} (Effective {self.
    effective_date})"
    


# -------------------- CollectionPoint --------------------
class CollectionPoint(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    contact_phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name


# -------------------- MilkCollection --------------------
class MilkCollection(models.Model):
    collector = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'collector'},
        related_name='milk_collections'
    )
    farmer = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'farmer'},
        related_name='milk_supplies'
    )
    collection_point = models.ForeignKey(
        CollectionPoint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='milk_collections'
    )
    quantity_litres = models.DecimalField(max_digits=6, decimal_places=2)
    fat_content = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Optional fat percentage.")
    date_collected = models.DateTimeField(default=timezone.now)

    farmer_rate_at_collection = models.DecimalField(max_digits=5, decimal_places=2, editable=False)
    collector_rate_at_collection = models.DecimalField(max_digits=5, decimal_places=2, editable=False)
    amount_payable_to_farmer = models.DecimalField(max_digits=8, decimal_places=2, editable=False)
    commission_payable_to_collector = models.DecimalField(max_digits=8, decimal_places=2, editable=False)

    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_collected']

    def __str__(self):
        return f"{self.date_collected.strftime('%Y-%m-%d')} | {self.quantity_litres}L | {self.farmer.username} → {self.collector.username}"

    def clean(self):
        if self.date_collected > timezone.now():
            raise ValidationError("Date collected cannot be in the future.")

    def save(self, *args, **kwargs):
        if self.pk is None:
            try:
                farmer_rate = RateSetting.objects.filter(role='farmer').latest('effective_date')
                collector_rate = RateSetting.objects.filter(role='collector').latest('effective_date')
            except RateSetting.DoesNotExist:
                raise ValidationError("Set both farmer and collector rates before saving.")

            self.farmer_rate_at_collection = farmer_rate.rate_per_litre
            self.collector_rate_at_collection = collector_rate.rate_per_litre

            net_quantity = self.quantity_litres
            self.amount_payable_to_farmer = (net_quantity * self.farmer_rate_at_collection).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.commission_payable_to_collector = (net_quantity * self.collector_rate_at_collection).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        super().save(*args, **kwargs)


# -------------------- Payment --------------------
class Payment(models.Model):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    milk_collections = models.ManyToManyField(MilkCollection, related_name='payments', blank=True)

    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount before deductions")
    farmer_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    collector_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount after deductions")

    method = models.CharField(max_length=50)
    remarks = models.TextField(blank=True)
    date_paid = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-date_paid']

    def __str__(self):
        return f"{self.user.username} | {self.net_amount} | {self.status}"

class PaymentLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} on {self.payment} by {self.user}"
    
    

from django.db import models
from django.utils import timezone
from django.conf import settings


class Supplement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Discount percentage (e.g., 10 for 10%)")
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='supplements/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_in_stock(self):
        return self.stock > 0

    def availability_status(self):
        return "In Stock" if self.is_in_stock() else "Out of Stock"

    def discounted_price(self):
        """Return price after static discount field is applied."""
        if self.discount > 0:
            return self.price - (self.price * (self.discount / 100))
        return self.price


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    supplement = models.ForeignKey(Supplement, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    discount_applied = models.PositiveIntegerField(default=0, help_text="Dynamic discount % based on farmer performance")
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2, help_text="Final unit price after discount")
    added_on = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return self.price_at_order * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.supplement.name} for {self.user.username}"


class SupplementOrder(models.Model):
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('deduction', 'Milk Deduction'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart_items = models.ManyToManyField(CartItem)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_orders',
        help_text="Admin who approved the order"
    )
    notification_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def mark_as_paid(self, receipt=None):
        self.status = 'paid'
        if receipt:
            self.receipt_number = receipt
        self.save()

    def approve_order(self, admin_user):
        self.status = 'approved'
        self.approved_by = admin_user
        self.save()
