from django import forms
from auths.models import CustomUser
from .models import RateSetting, MilkCollection, Payment
from django.contrib.auth import get_user_model

User = get_user_model()

# -------------------------
# Rate Setting Form
# -------------------------
class RateSettingForm(forms.ModelForm):
    class Meta:
        model = RateSetting
        fields = ['role', 'rate_per_litre']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'rate_per_litre': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        
        
        # milk rate



# -------------------------
# Milk Collection Form
# -------------------------
class MilkCollectionForm(forms.ModelForm):
    class Meta:
        model = MilkCollection
        fields = ['collector', 'farmer', 'collection_point', 'quantity_litres', 'fat_content']
        widgets = {
            'quantity_litres': forms.NumberInput(attrs={'step': '0.01'}),
            'fat_content': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(MilkCollectionForm, self).__init__(*args, **kwargs)

        # Remove hardcoded 'form-control' class to allow Tailwind styling via template
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.setdefault('placeholder', f'Enter {field_name.replace("_", " ").capitalize()}')

        # Customize field labels and queryset
        self.fields['farmer'].queryset = CustomUser.objects.filter(role='farmer')
        self.fields['farmer'].label = "Farmer (Supplier)"

        if user:
            if user.is_superuser:
                self.fields['collector'].queryset = CustomUser.objects.filter(role='collector')
                self.fields['collector'].label = "Collector"
            elif user.role == 'collector':
                self.fields['collector'].initial = user
                self.fields['collector'].widget = forms.HiddenInput()

# -------------------------
# Payment Form
# -------------------------

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'user',
            'milk_collections',
            'method',
            'remarks',
            'status',
            'date_paid',
        ]
        widgets = {
            'milk_collections': forms.CheckboxSelectMultiple(),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'date_paid': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)

        # Apply Bootstrap class to all fields except milk_collections (which uses checkboxes)
        for name, field in self.fields.items():
            if name != 'milk_collections':
                field.widget.attrs.update({'class': 'form-control'})

        # Optional: Only show unpaid milk collections
        self.fields['milk_collections'].queryset = MilkCollection.objects.filter(is_paid=False)

        # Optional: Show only farmers or collectors as the 'user' to be paid
        self.fields['user'].queryset = CustomUser.objects.filter(role__in=['farmer', 'collector'])
        self.fields['user'].label = "Payee (Farmer or Collector)"
        
        # supplemets 
from .models import Supplement

class SupplementForm(forms.ModelForm):
    class Meta:
        model = Supplement
        fields = ['name', 'description', 'price', 'stock', 'image', 'is_active']