# farmer/forms.py

from django import forms
from auths.models import Feedback
from django.contrib.auth import get_user_model

User = get_user_model()

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['recipient', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(FeedbackForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['recipient'].queryset = User.objects.exclude(id=user.id)

class FeedbackReplyForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['reply']
        widgets = {
            'reply': forms.Textarea(attrs={'rows': 3}),
        }
