from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect,render

from products.models import ProductVariant

from .models import Cart, CartItem


@login_required
def add_to_cart(request, variant_id):

    if request.method != "POST":
        return redirect("product_list")

    variant = get_object_or_404(
        ProductVariant.objects.select_related(
            "product",
            "inventory",
        ),
        pk=variant_id,
        is_active=True,
        product__is_active=True,
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        messages.error(
            request,
            "Quantity must be at least 1.",
        )
        return redirect(
            "product_detail",
            slug=variant.product.slug,
        )

    inventory = getattr(variant, "inventory", None)

    if inventory is None or inventory.quantity == 0:
        messages.error(
            request,
            "This variant is currently out of stock.",
        )
        return redirect(
            "product_detail",
            slug=variant.product.slug,
        )

    cart, created = Cart.objects.get_or_create(
        user=request.user,
    )

    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={
            "quantity": quantity,
        },
    )

    if not item_created:

        new_quantity = cart_item.quantity + quantity

        if new_quantity > inventory.quantity:
            messages.error(
                request,
                f"Only {inventory.quantity} units are available.",
            )
            return redirect(
                "product_detail",
                slug=variant.product.slug,
            )

        cart_item.quantity = new_quantity
        cart_item.save()

    elif quantity > inventory.quantity:

        cart_item.delete()

        messages.error(
            request,
            f"Only {inventory.quantity} units are available.",
        )

        return redirect(
            "product_detail",
            slug=variant.product.slug,
        )

    messages.success(
        request,
        f"{variant.product.name} added to your cart.",
    )

    return redirect(
        "product_detail",
        slug=variant.product.slug,
    )

@login_required
def cart_detail(request):

    cart, created = Cart.objects.get_or_create(
        user=request.user,
    )

    cart_items = cart.items.select_related(
        "variant",
        "variant__product",
    ).prefetch_related(
        "variant__product__images",
    )

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart": cart,
            "cart_items": cart_items,
        },
    )

@login_required
def increase_cart_item(request, item_id):

    if request.method != "POST":
        return redirect("cart_detail")

    cart_item = get_object_or_404(
        CartItem.objects.select_related(
            "variant",
            "variant__product",
            "variant__inventory",
        ),
        pk=item_id,
        cart__user=request.user,
    )

    inventory = getattr(
        cart_item.variant,
        "inventory",
        None,
    )

    if inventory is None or inventory.quantity == 0:
        messages.error(
            request,
            "This product is currently out of stock.",
        )
        return redirect("cart_detail")

    if cart_item.quantity >= inventory.quantity:
        messages.error(
            request,
            f"Only {inventory.quantity} units are available.",
        )
        return redirect("cart_detail")

    cart_item.quantity += 1
    cart_item.save()

    messages.success(
        request,
        "Cart quantity updated.",
    )

    return redirect("cart_detail")


@login_required
def decrease_cart_item(request, item_id):

    if request.method != "POST":
        return redirect("cart_detail")

    cart_item = get_object_or_404(
        CartItem,
        pk=item_id,
        cart__user=request.user,
    )

    if cart_item.quantity > 1:

        cart_item.quantity -= 1
        cart_item.save()

        messages.success(
            request,
            "Cart quantity updated.",
        )

    else:

        cart_item.delete()

        messages.success(
            request,
            "Item removed from your cart.",
        )

    return redirect("cart_detail")


@login_required
def remove_cart_item(request, item_id):

    if request.method != "POST":
        return redirect("cart_detail")

    cart_item = get_object_or_404(
        CartItem,
        pk=item_id,
        cart__user=request.user,
    )

    cart_item.delete()

    messages.success(
        request,
        "Item removed from your cart.",
    )

    return redirect("cart_detail")