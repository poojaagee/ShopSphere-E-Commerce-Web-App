from django.contrib import admin

from .models import Address, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "phone",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "user__username",
        "user__email",
        "phone",
    ]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "full_name",
        "address_type",
        "city",
        "state",
        "postal_code",
        "is_default",
    ]

    list_filter = [
        "address_type",
        "state",
        "is_default",
    ]

    search_fields = [
        "user__username",
        "user__email",
        "full_name",
        "city",
        "postal_code",
    ]