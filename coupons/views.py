from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone

from cart.models import Cart
from .models import Coupon, CouponUsage


@login_required
def apply_coupon(request):

    if request.method != "POST":
        return redirect("cart_detail")

    code = request.POST.get(
        "code",
        "",
    ).strip().upper()

    if not code:
        messages.error(
            request,
            "Please enter a coupon code.",
        )
        return redirect("cart_detail")

    coupon = Coupon.objects.filter(
        code=code,
        is_active=True,
    ).first()

    if not coupon:
        messages.error(
            request,
            "Invalid coupon code.",
        )
        return redirect("cart_detail")

    now = timezone.now()

    if now < coupon.valid_from:
        messages.error(
            request,
            "This coupon is not active yet.",
        )
        return redirect("cart_detail")

    if now > coupon.valid_until:
        messages.error(
            request,
            "This coupon has expired.",
        )
        return redirect("cart_detail")

    cart, created = Cart.objects.get_or_create(
        user=request.user,
    )

    if cart.subtotal < coupon.minimum_order_amount:
        messages.error(
            request,
            f"Minimum order amount is "
            f"₹{coupon.minimum_order_amount}.",
        )
        return redirect("cart_detail")

    total_usage = coupon.usages.count()

    if (
        coupon.usage_limit is not None
        and total_usage >= coupon.usage_limit
    ):
        messages.error(
            request,
            "This coupon has reached its usage limit.",
        )
        return redirect("cart_detail")

    user_usage = CouponUsage.objects.filter(
        coupon=coupon,
        user=request.user,
    ).count()

    if user_usage >= coupon.per_user_limit:
        messages.error(
            request,
            "You have already reached the usage limit "
            "for this coupon.",
        )
        return redirect("cart_detail")

    cart.coupon = coupon
    cart.save()

    messages.success(
        request,
        f"Coupon {coupon.code} applied successfully.",
    )

    return redirect("cart_detail")


@login_required
def remove_coupon(request):

    if request.method != "POST":
        return redirect("cart_detail")

    cart, created = Cart.objects.get_or_create(
        user=request.user,
    )

    cart.coupon = None
    cart.save()

    messages.success(
        request,
        "Coupon removed from your cart.",
    )

    return redirect("cart_detail")