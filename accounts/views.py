from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressForm, ProfileForm, RegistrationForm
from .models import Address


def register(request):

    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect("profile")

    else:

        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


@login_required
def profile(request):

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            instance=request.user.profile,
        )

        if form.is_valid():
            form.save()
            return redirect("profile")

    else:

        form = ProfileForm(
            instance=request.user.profile,
        )

    addresses = request.user.addresses.all()

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "addresses": addresses,
        },
    )


@login_required
def address_create(request):

    if request.method == "POST":

        form = AddressForm(request.POST)

        if form.is_valid():

            address = form.save(commit=False)
            address.user = request.user

            if address.is_default:

                Address.objects.filter(
                    user=request.user,
                    address_type=address.address_type,
                ).update(
                    is_default=False,
                )

            address.save()

            return redirect("profile")

    else:

        form = AddressForm()

    return render(
        request,
        "accounts/address_form.html",
        {
            "form": form,
            "page_title": "Add Address",
        },
    )


@login_required
def address_edit(request, pk):

    address = get_object_or_404(
        Address,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":

        form = AddressForm(
            request.POST,
            instance=address,
        )

        if form.is_valid():

            address = form.save(commit=False)

            if address.is_default:

                Address.objects.filter(
                    user=request.user,
                    address_type=address.address_type,
                ).exclude(
                    pk=address.pk,
                ).update(
                    is_default=False,
                )

            address.save()

            return redirect("profile")

    else:

        form = AddressForm(
            instance=address,
        )

    return render(
        request,
        "accounts/address_form.html",
        {
            "form": form,
            "page_title": "Edit Address",
        },
    )


@login_required
def address_delete(request, pk):

    address = get_object_or_404(
        Address,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        address.delete()

    return redirect("profile")