from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product

from .models import Wishlist, WishlistItem


@login_required
def wishlist_detail(request):

    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user,
    )

    wishlist_items = wishlist.items.select_related(
        "product",
        "product__brand",
        "product__category",
    ).prefetch_related(
        "product__images",
    )

    return render(
        request,
        "wishlist/wishlist_detail.html",
        {
            "wishlist": wishlist,
            "wishlist_items": wishlist_items,
        },
    )


@login_required
def add_to_wishlist(request, product_id):

    if request.method != "POST":
        return redirect("product_list")

    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True,
    )

    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user,
    )

    wishlist_item, item_created = (
        WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product,
        )
    )

    if item_created:
        messages.success(
            request,
            f"{product.name} added to your wishlist.",
        )
    else:
        messages.info(
            request,
            f"{product.name} is already in your wishlist.",
        )

    return redirect(
        request.POST.get(
            "next",
            "product_list",
        )
    )


@login_required
def remove_from_wishlist(request, product_id):

    if request.method != "POST":
        return redirect("wishlist_detail")

    wishlist = get_object_or_404(
        Wishlist,
        user=request.user,
    )

    wishlist_item = get_object_or_404(
        WishlistItem,
        wishlist=wishlist,
        product_id=product_id,
    )

    product_name = wishlist_item.product.name

    wishlist_item.delete()

    messages.success(
        request,
        f"{product_name} removed from your wishlist.",
    )

    return redirect(
        request.POST.get(
            "next",
            "wishlist_detail",
        )
    )