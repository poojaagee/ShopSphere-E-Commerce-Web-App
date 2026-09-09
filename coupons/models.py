from django.contrib.auth.models import User
from django.db import models


class Coupon(models.Model):

    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    per_user_limit = models.PositiveIntegerField(
        default=1,
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


class CouponUsage(models.Model):

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="coupon_usages",
    )
    used_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-used_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.coupon.code}"
        )