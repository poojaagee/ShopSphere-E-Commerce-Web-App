from decimal import Decimal
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Address
from cart.models import Cart
from coupons.models import CouponUsage
from products.models import ProductVariant

from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required
def checkout(request):

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_items = cart.items.select_related(
        "variant",
        "variant__product",
        "variant__product__brand",
    ).prefetch_related(
        "variant__product__images",
    )

    if not cart_items.exists():

        messages.info(
            request,
            "Your cart is empty. Add products before checkout.",
        )

        return redirect("cart_detail")

    if request.method == "POST":

        form = CheckoutForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():

            shipping_address = form.cleaned_data[
                "shipping_address"
            ]

            billing_same_as_shipping = form.cleaned_data[
                "billing_same_as_shipping"
            ]

            billing_address = form.cleaned_data[
                "billing_address"
            ]

            if billing_same_as_shipping:
                billing_address = shipping_address

            request.session["checkout_shipping_address_id"] = (
                shipping_address.id
            )

            request.session["checkout_billing_address_id"] = (
                billing_address.id
                if billing_address
                else None
            )

            return redirect("checkout_review")

    else:

        form = CheckoutForm(
            user=request.user,
        )

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "form": form,
    }

    return render(
        request,
        "orders/checkout.html",
        context,
    )


@login_required
def checkout_review(request):

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_items = cart.items.select_related(
        "variant",
        "variant__product",
        "variant__product__brand",
    ).prefetch_related(
        "variant__product__images",
    )

    if not cart_items.exists():

        messages.info(
            request,
            "Your cart is empty.",
        )

        return redirect("cart_detail")

    shipping_address_id = request.session.get(
        "checkout_shipping_address_id"
    )

    billing_address_id = request.session.get(
        "checkout_billing_address_id"
    )

    if not shipping_address_id:

        messages.error(
            request,
            "Please select a shipping address.",
        )

        return redirect("checkout")

    shipping_address = Address.objects.filter(
        id=shipping_address_id,
        user=request.user,
    ).first()

    billing_address = None

    if billing_address_id:

        billing_address = Address.objects.filter(
            id=billing_address_id,
            user=request.user,
        ).first()

    if not shipping_address:

        messages.error(
            request,
            "The selected shipping address is no longer available.",
        )

        return redirect("checkout")

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "shipping_address": shipping_address,
        "billing_address": billing_address,
    }

    return render(
        request,
        "orders/checkout_review.html",
        context,
    )


def generate_order_number():

    while True:

        order_number = (
            f"SS-{timezone.now():%Y%m%d}-"
            f"{uuid.uuid4().hex[:10].upper()}"
        )

        if not Order.objects.filter(
            order_number=order_number
        ).exists():

            return order_number


@login_required
def place_order(request):

    if request.method != "POST":

        return redirect("checkout_review")

    shipping_address_id = request.session.get(
        "checkout_shipping_address_id"
    )

    billing_address_id = request.session.get(
        "checkout_billing_address_id"
    )

    if not shipping_address_id:

        messages.error(
            request,
            "Please select a shipping address before placing the order.",
        )

        return redirect("checkout")

    with transaction.atomic():

        cart = Cart.objects.select_for_update().get(
            user=request.user
        )

        cart_items = list(
            cart.items.select_related(
                "variant",
                "variant__product",
            )
        )

        if not cart_items:

            messages.error(
                request,
                "Your cart is empty.",
            )

            return redirect("cart_detail")

        shipping_address = Address.objects.filter(
            id=shipping_address_id,
            user=request.user,
        ).first()

        if not shipping_address:

            messages.error(
                request,
                "The selected shipping address is no longer available.",
            )

            return redirect("checkout")

        billing_address = None

        if billing_address_id:

            billing_address = Address.objects.filter(
                id=billing_address_id,
                user=request.user,
            ).first()

        # Lock inventory rows before checking quantities.
        variants = []

        for item in cart_items:

            variant = (
                ProductVariant.objects
                .select_for_update()
                .select_related("product")
                .filter(
                    id=item.variant_id,
                    is_active=True,
                    product__is_active=True,
                )
                .first()
            )

            if not variant:

                messages.error(
                    request,
                    "One of the products in your cart is no longer available.",
                )

                return redirect("cart_detail")

            variants.append(
                (item, variant)
            )

        # Validate inventory.
        for item, variant in variants:

            inventory = getattr(
                variant,
                "inventory",
                None,
            )

            if inventory is None:

                messages.error(
                    request,
                    f"Inventory information is unavailable for "
                    f"{variant.product.name}.",
                )

                return redirect("cart_detail")

            if inventory.quantity < item.quantity:

                messages.error(
                    request,
                    f"Insufficient stock for "
                    f"{variant.product.name} - "
                    f"{variant.name}. "
                    f"Only {inventory.quantity} item(s) are available.",
                )

                return redirect("cart_detail")

        # Recalculate totals from the locked cart.
        subtotal = sum(
            (
                item.variant.price
                if item.variant.price is not None
                else item.variant.product.price
            ) * item.quantity
            for item in cart_items
        )

        subtotal = Decimal(subtotal)

        discount_amount = Decimal("0.00")
        coupon = cart.coupon

        if coupon:

            now = timezone.now()

            coupon_valid = (
                coupon.is_active
                and coupon.valid_from <= now
                and coupon.valid_until >= now
            )

            if not coupon_valid:

                messages.error(
                    request,
                    "The coupon applied to your cart is no longer valid.",
                )

                return redirect("cart_detail")

            if (
                coupon.discount_type == "percentage"
                and coupon.discount_value > 100
            ):

                messages.error(
                    request,
                    "The applied coupon has an invalid discount value.",
                )

                return redirect("cart_detail")

            if subtotal < coupon.minimum_order_amount:

                messages.error(
                    request,
                    "Your order no longer meets the minimum amount "
                    "required for the coupon.",
                )

                return redirect("cart_detail")

            total_usage = CouponUsage.objects.filter(
                coupon=coupon
            ).count()

            if (
                coupon.usage_limit is not None
                and total_usage >= coupon.usage_limit
            ):

                messages.error(
                    request,
                    "The coupon has reached its usage limit.",
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

            if coupon.discount_type == "percentage":

                discount_amount = (
                    subtotal
                    * coupon.discount_value
                    / Decimal("100")
                )

            else:

                discount_amount = coupon.discount_value

            discount_amount = min(
                discount_amount,
                subtotal,
            )

        total = max(
            subtotal - discount_amount,
            Decimal("0.00"),
        )

        # Create the order.
        order = Order.objects.create(
            user=request.user,
            order_number=generate_order_number(),
            status="pending",
            payment_status="pending",
            coupon=coupon,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total=total,

            shipping_full_name=shipping_address.full_name,
            shipping_phone=shipping_address.phone,
            shipping_address_line1=shipping_address.address_line1,
            shipping_address_line2=shipping_address.address_line2,
            shipping_city=shipping_address.city,
            shipping_state=shipping_address.state,
            shipping_postal_code=shipping_address.postal_code,
            shipping_country=shipping_address.country,

            billing_full_name=(
                billing_address.full_name
                if billing_address
                else shipping_address.full_name
            ),
            billing_phone=(
                billing_address.phone
                if billing_address
                else shipping_address.phone
            ),
            billing_address_line1=(
                billing_address.address_line1
                if billing_address
                else shipping_address.address_line1
            ),
            billing_address_line2=(
                billing_address.address_line2
                if billing_address
                else shipping_address.address_line2
            ),
            billing_city=(
                billing_address.city
                if billing_address
                else shipping_address.city
            ),
            billing_state=(
                billing_address.state
                if billing_address
                else shipping_address.state
            ),
            billing_postal_code=(
                billing_address.postal_code
                if billing_address
                else shipping_address.postal_code
            ),
            billing_country=(
                billing_address.country
                if billing_address
                else shipping_address.country
            ),
        )

        # Create order items and reduce inventory.
        for item, variant in variants:

            unit_price = (
                variant.price
                if variant.price is not None
                else variant.product.price
            )

            item_total = unit_price * item.quantity

            OrderItem.objects.create(
                order=order,
                product=variant.product,
                variant=variant,
                product_name=variant.product.name,
                variant_name=variant.name,
                sku=variant.sku,
                quantity=item.quantity,
                unit_price=unit_price,
                total_price=item_total,
            )

            inventory = variant.inventory

            inventory.quantity -= item.quantity
            inventory.save(
                update_fields=[
                    "quantity",
                    "updated_at",
                ]
            )

        # Record coupon usage.
        if coupon:

            CouponUsage.objects.create(
                coupon=coupon,
                user=request.user,
            )

        # Clear the cart.
        cart.items.all().delete()

        cart.coupon = None

        cart.save(
            update_fields=[
                "coupon",
                "updated_at",
            ]
        )

    # Remove temporary checkout data.
    request.session.pop(
        "checkout_shipping_address_id",
        None,
    )

    request.session.pop(
        "checkout_billing_address_id",
        None,
    )

    request.session["last_order_id"] = order.id

    return redirect(
    "payment",
    order_number=order.order_number,
    )

def generate_payment_reference():

    return (
        f"DEMO-{uuid.uuid4().hex[:12].upper()}"
    )


@login_required
def payment(request, order_number):

    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    if order.payment_status != "pending":

        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    context = {
        "order": order,
    }

    return render(
        request,
        "orders/payment.html",
        context,
    )


@login_required
def process_payment(request, order_number):

    if request.method != "POST":
        return redirect(
            "payment",
            order_number=order_number,
        )

    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    if order.payment_status != "pending":
        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    payment_method = request.POST.get(
        "payment_method",
        "",
    ).strip()

    # --------------------------------
    # DEMO CARD PAYMENT
    # --------------------------------

    if payment_method == "demo_card":

        demo_result = request.POST.get(
            "demo_result",
            "",
        ).strip()

        order.payment_method = "Demo Card"
        order.payment_reference = (
            generate_payment_reference()
        )

        if demo_result == "success":

            order.payment_status = "paid"
            order.status = "processing"

            order.save(
                update_fields=[
                    "payment_method",
                    "payment_status",
                    "payment_reference",
                    "status",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Demo card payment completed successfully.",
            )

            return redirect(
                "order_confirmation",
                order_number=order.order_number,
            )

        elif demo_result == "failure":

            order.payment_status = "failed"

            # Keep order pending because payment failed.
            order.status = "pending"

            order.save(
                update_fields=[
                    "payment_method",
                    "payment_status",
                    "payment_reference",
                    "status",
                    "updated_at",
                ]
            )

            messages.error(
                request,
                "Demo card payment failed.",
            )

            return redirect(
                "payment",
                order_number=order.order_number,
            )

        else:

            messages.error(
                request,
                "Please select a valid demo payment result.",
            )

            return redirect(
                "payment",
                order_number=order.order_number,
            )

    # --------------------------------
    # CASH ON DELIVERY
    # --------------------------------

    elif payment_method == "cod":

        order.payment_method = "Cash on Delivery"
        order.payment_status = "pending"
        order.payment_reference = ""
        order.status = "processing"

        order.save(
            update_fields=[
                "payment_method",
                "payment_status",
                "payment_reference",
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "Cash on Delivery selected successfully.",
        )

        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    # --------------------------------
    # INVALID PAYMENT METHOD
    # --------------------------------

    else:

        messages.error(
            request,
            "Please select a valid payment method.",
        )

        return redirect(
            "payment",
            order_number=order.order_number,
        )

@login_required
def order_confirmation(request, order_number):

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items",
        ),
        order_number=order_number,
        user=request.user,
    )

    context = {
        "order": order,
    }

    return render(
        request,
        "orders/order_confirmation.html",
        context,
    )

@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        "items",
    )

    context = {
        "orders": orders,
    }

    return render(
        request,
        "orders/my_orders.html",
        context,
    )


@login_required
def order_detail(request, order_number):

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items",
        ),
        order_number=order_number,
        user=request.user,
    )

    context = {
        "order": order,
    }

    return render(
        request,
        "orders/order_detail.html",
        context,
    )