from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth import get_user_model
from .models import CustomUser, Feedback

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[('farmer', 'Farmer'), ('collector', 'Collector')],  # Removed 'admin'
        widget=forms.RadioSelect
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} form-control'.strip()


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:ring-2 focus:ring-indigo-400 focus:outline-none'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:ring-2 focus:ring-indigo-400 focus:outline-none'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:ring-2 focus:ring-indigo-400 focus:outline-none'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:ring-2 focus:ring-indigo-400 focus:outline-none'
            }),
        }
        help_texts = {
            'username': '',
            'email': '',
            'first_name': '',
            'last_name': '',
        }


class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    old_password = forms.CharField(
        label="Old Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:ring-2 focus:ring-red-400 focus:outline-none'
        }),
        help_text=''
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:ring-2 focus:ring-green-400 focus:outline-none'
        }),
        help_text=''
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:ring-2 focus:ring-green-400 focus:outline-none'
        }),
        help_text=''
    )


class FeedbackForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=User.objects.all(), label="Send To")

    class Meta:
        model = Feedback
        fields = ['recipient', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your feedback...'}),
        }
