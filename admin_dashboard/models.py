# core/models.py
from django.db import models
from django.db.models import Sum
from django.contrib.auth import get_user_model

User = get_user_model()

class MilkCollection(models.Model):
    collector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='milk_collections')
    quantity_litres = models.FloatField()
    fat_content = models.FloatField()
    price_per_litre = models.DecimalField(max_digits=6, decimal_places=2)
    date_collected = models.DateField(auto_now_add=True)

    def total_price(self):
        return round(self.quantity_litres * float(self.price_per_litre), 2)

    def __str__(self):
        return f"{self.collector.username} - {self.quantity_litres}L on {self.date_collected}"


class Payment(models.Model):
    PAYEE_ROLE_CHOICES = (
        ('collector', 'Collector'),
        ('farmer', 'Farmer'),  # In case farmers also need future payment tracking
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=100, default="Cash")  # Mpesa, Bank, etc.
    remarks = models.TextField(blank=True)
    payee_role = models.CharField(max_length=10, choices=PAYEE_ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} paid {self.amount} on {self.date}"
  
class RateSetting(models.Model):
    role = models.CharField(max_length=20, choices=(('collector', 'Collector'), ('farmer', 'Farmer')))
    rate_per_litre = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.role} - Ksh {self.rate_per_litre}/L"
