from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from coupons.models import Coupon
from products.models import Product, ProductVariant


class Order(models.Model):

    ORDER_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    order_number = models.CharField(
        max_length=30,
        unique=True,
    )

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="pending",
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending",
    )

    payment_method = models.CharField(
    max_length=30,
    blank=True,
    )

    payment_reference = models.CharField(
    max_length=100,
    blank=True,
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    shipping_full_name = models.CharField(
        max_length=150,
    )

    shipping_phone = models.CharField(
        max_length=20,
    )

    shipping_address_line1 = models.CharField(
        max_length=255,
    )

    shipping_address_line2 = models.CharField(
        max_length=255,
        blank=True,
    )

    shipping_city = models.CharField(
        max_length=100,
    )

    shipping_state = models.CharField(
        max_length=100,
    )

    shipping_postal_code = models.CharField(
        max_length=20,
    )

    shipping_country = models.CharField(
        max_length=100,
        default="India",
    )

    billing_full_name = models.CharField(
        max_length=150,
        blank=True,
    )

    billing_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    billing_address_line1 = models.CharField(
        max_length=255,
        blank=True,
    )

    billing_address_line2 = models.CharField(
        max_length=255,
        blank=True,
    )

    billing_city = models.CharField(
        max_length=100,
        blank=True,
    )

    billing_state = models.CharField(
        max_length=100,
        blank=True,
    )

    billing_postal_code = models.CharField(
        max_length=20,
        blank=True,
    )

    billing_country = models.CharField(
        max_length=100,
        blank=True,
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
        return self.order_number


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    product_name = models.CharField(
        max_length=200,
    )

    variant_name = models.CharField(
        max_length=150,
    )

    sku = models.CharField(
        max_length=50,
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.order.order_number} - {self.product_name}"