from django.contrib import admin

from .models import Wishlist, WishlistItem


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "created_at",
        "updated_at",
    ]

    search_fields = [
        "user__username",
        "user__email",
    ]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):

    list_display = [
        "wishlist",
        "product",
        "created_at",
    ]

    search_fields = [
        "wishlist__user__username",
        "wishlist__user__email",
        "product__name",
        "product__sku",
    ]

    list_filter = [
        "created_at",
    ]