from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Address(models.Model):

    ADDRESS_TYPE_CHOICES = [
        ("shipping", "Shipping"),
        ("billing", "Billing"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default="shipping",
    )
    full_name = models.CharField(
        max_length=150,
    )
    phone = models.CharField(
        max_length=20,
    )
    address_line1 = models.CharField(
        max_length=255,
    )
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
    )
    city = models.CharField(
        max_length=100,
    )
    state = models.CharField(
        max_length=100,
    )
    postal_code = models.CharField(
        max_length=20,
    )
    country = models.CharField(
        max_length=100,
        default="India",
    )
    is_default = models.BooleanField(
        default=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.city}"