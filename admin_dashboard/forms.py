from django import forms
from .models import *

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'remarks']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-input border rounded w-full'}),
            'remarks': forms.TextInput(attrs={'class': 'form-input border rounded w-full'}),
        }

class RateSettingForm(forms.ModelForm):
    class Meta:
        model = RateSetting
        fields = ['role', 'rate_per_litre']