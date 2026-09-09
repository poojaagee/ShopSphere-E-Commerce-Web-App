from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from coupons.models import Coupon
from products.models import ProductVariant


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart",
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_quantity(self):
        return sum(
            item.quantity
            for item in self.items.all()
        )

    @property
    def subtotal(self):
        return sum(
            (item.total_price for item in self.items.all()),
            Decimal("0.00"),
        )

    @property
    def discount_amount(self):

        if not self.coupon:
            return Decimal("0.00")

        if self.subtotal < self.coupon.minimum_order_amount:
            return Decimal("0.00")

        if self.coupon.discount_type == "percentage":

            discount = (
                self.subtotal
                * self.coupon.discount_value
                / Decimal("100")
            )

        else:

            discount = self.coupon.discount_value

        return min(
            discount,
            self.subtotal,
        )

    @property
    def total(self):
        return max(
            self.subtotal - self.discount_amount,
            Decimal("0.00"),
        )

    def __str__(self):
        return f"Cart - {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_cart_variant",
            ),
        ]
        ordering = ["-created_at"]

    @property
    def unit_price(self):
        return (
            self.variant.price
            if self.variant.price is not None
            else self.variant.product.price
        )

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return (
            f"{self.cart.user.username} - "
            f"{self.variant.product.name} - "
            f"{self.variant.name}"
        )