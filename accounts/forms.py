from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Address, Profile


class RegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = [
            "phone",
        ]


class AddressForm(forms.ModelForm):

    class Meta:
        model = Address
        fields = [
            "address_type",
            "full_name",
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "is_default",
        ]