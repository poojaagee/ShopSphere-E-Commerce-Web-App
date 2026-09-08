from django.contrib import admin

from .models import (
    Category,
    Brand,
    Product,
    ProductImage,
    ProductVariant,
    Inventory,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "price",
        "sku",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "category", "brand")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("product__name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "name",
        "sku",
        "price",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("product__name", "name", "sku")


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "quantity",
        "low_stock_threshold",
        "is_low_stock",
        "updated_at",
    )
    list_filter = ("quantity",)
    search_fields = ("variant__product__name", "variant__sku")