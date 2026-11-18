# OWNER Dev A
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.utils import timezone

User = get_user_model()

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    accept_terms = forms.BooleanField(
        required=True, error_messages={"required": "You need to accept the terms to create an account."})

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.terms_accepted_at = timezone.now()
        user.terms_version = settings.TERMS_VERSION
        if commit:
            user.save()
        return user