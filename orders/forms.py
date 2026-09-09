from django import forms

from accounts.models import Address


class CheckoutForm(forms.Form):

    shipping_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        empty_label=None,
        widget=forms.RadioSelect,
    )

    billing_same_as_shipping = forms.BooleanField(
        required=False,
        initial=True,
    )

    billing_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        required=False,
        empty_label=None,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, user=None, **kwargs):

        super().__init__(*args, **kwargs)

        if user is not None:

            addresses = Address.objects.filter(
                user=user
            )

            self.fields["shipping_address"].queryset = addresses.filter(
                address_type="shipping"
            )

            self.fields["billing_address"].queryset = addresses.filter(
                address_type="billing"
            )