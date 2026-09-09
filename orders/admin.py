from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = [
        "product",
        "variant",
        "product_name",
        "variant_name",
        "sku",
        "quantity",
        "unit_price",
        "total_price",
        "created_at",
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = [
    "order_number",
    "user",
    "status",
    "payment_status",
    "payment_method",
    "payment_reference",
    "subtotal",
    "discount_amount",
    "total",
    "created_at",
    ]

    list_filter = [
        "status",
        "payment_status",
        "created_at",
    ]

    search_fields = [
        "order_number",
        "user__username",
        "user__email",
    ]

    readonly_fields = [
    "order_number",
    "user",
    "coupon",
    "subtotal",
    "discount_amount",
    "total",
    "payment_reference",
    "created_at",
    "updated_at",
    ]

    inlines = [
        OrderItemInline,
    ]

    ordering = [
        "-created_at",
    ]