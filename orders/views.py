from decimal import Decimal
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Address
from cart.models import Cart
from coupons.models import Coupon, CouponUsage
from products.models import ProductVariant, Inventory

from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_items = cart.items.select_related(
        "variant",
        "variant__product",
        "variant__product__brand",
    ).prefetch_related(
        "variant__product__images"
    )

    if not cart_items.exists():
        messages.info(
            request,
            "Your cart is empty. Add products before checkout."
        )
        return redirect("cart_detail")

    if request.method == "POST":
        form = CheckoutForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            shipping_address = form.cleaned_data["shipping_address"]
            billing_same_as_shipping = form.cleaned_data[
                "billing_same_as_shipping"
            ]
            billing_address = form.cleaned_data["billing_address"]

            if billing_same_as_shipping:
                billing_address = shipping_address

            request.session[
                "checkout_shipping_address_id"
            ] = shipping_address.id

            request.session[
                "checkout_billing_address_id"
            ] = billing_address.id if billing_address else None

            return redirect("checkout_review")

    else:
        form = CheckoutForm(user=request.user)

    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "cart_items": cart_items,
            "form": form,
        },
    )


@login_required
def checkout_review(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_items = cart.items.select_related(
        "variant",
        "variant__product",
        "variant__product__brand",
    ).prefetch_related(
        "variant__product__images"
    )

    if not cart_items.exists():
        messages.info(
            request,
            "Your cart is empty."
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
            "Please select a shipping address."
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
            "The selected shipping address is no longer available."
        )
        return redirect("checkout")

    return render(
        request,
        "orders/checkout_review.html",
        {
            "cart": cart,
            "cart_items": cart_items,
            "shipping_address": shipping_address,
            "billing_address": billing_address,
        },
    )


def generate_order_number():
    """
    Generate a unique ShopSphere order number.
    """

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
    """
    Create the order and order-item snapshots.

    Inventory is NOT deducted here.

    Inventory is deducted only when:
    - Demo Card payment succeeds
    - Cash on Delivery is confirmed
    """

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
            "Please select a shipping address before placing the order."
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
                "Your cart is empty."
            )
            return redirect("cart_detail")

        shipping_address = Address.objects.filter(
            id=shipping_address_id,
            user=request.user,
        ).first()

        if not shipping_address:
            messages.error(
                request,
                "The selected shipping address is no longer available."
            )
            return redirect("checkout")

        billing_address = None

        if billing_address_id:
            billing_address = Address.objects.filter(
                id=billing_address_id,
                user=request.user,
            ).first()

        # ---------------------------------------------------------
        # Validate all variants before creating the order
        # ---------------------------------------------------------

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
                    "One of the products in your cart is no longer available."
                )
                return redirect("cart_detail")

            variants.append(
                (item, variant)
            )

        # ---------------------------------------------------------
        # Validate inventory
        # ---------------------------------------------------------

        for item, variant in variants:

            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(variant=variant)
                .first()
            )

            if inventory is None:
                messages.error(
                    request,
                    f"Inventory unavailable for "
                    f"{variant.product.name}."
                )
                return redirect("cart_detail")

            if inventory.quantity < item.quantity:
                messages.error(
                    request,
                    f"Insufficient stock for "
                    f"{variant.product.name} - {variant.name}. "
                    f"Only {inventory.quantity} available."
                )
                return redirect("cart_detail")

        # ---------------------------------------------------------
        # Calculate subtotal
        # ---------------------------------------------------------

        subtotal = Decimal("0.00")

        for item, variant in variants:

            price = (
                variant.price
                if variant.price is not None
                else variant.product.price
            )

            subtotal += (
                Decimal(price) * item.quantity
            )

        # ---------------------------------------------------------
        # Validate coupon
        # ---------------------------------------------------------

        discount_amount = Decimal("0.00")
        coupon = cart.coupon

        if coupon:

            now = timezone.now()

            if not (
                coupon.is_active
                and coupon.valid_from <= now <= coupon.valid_until
            ):
                messages.error(
                    request,
                    "The coupon applied to your cart is no longer valid."
                )
                return redirect("cart_detail")

            if (
                coupon.discount_type == "percentage"
                and coupon.discount_value > 100
            ):
                messages.error(
                    request,
                    "The applied coupon has an invalid discount value."
                )
                return redirect("cart_detail")

            if subtotal < coupon.minimum_order_amount:
                messages.error(
                    request,
                    "Your order no longer meets the minimum amount "
                    "required for the coupon."
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
                    "The coupon has reached its usage limit."
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
                    "for this coupon."
                )
                return redirect("cart_detail")

            if coupon.discount_type == "percentage":

                discount_amount = (
                    subtotal
                    * coupon.discount_value
                    / Decimal("100")
                )

            else:

                discount_amount = Decimal(
                    coupon.discount_value
                )

            discount_amount = min(
                discount_amount,
                subtotal
            )

        # ---------------------------------------------------------
        # Final total
        # ---------------------------------------------------------

        total = max(
            subtotal - discount_amount,
            Decimal("0.00")
        )

        # ---------------------------------------------------------
        # Create order
        # ---------------------------------------------------------

        order = Order.objects.create(
            user=request.user,

            order_number=generate_order_number(),

            status="pending",

            payment_status="pending",

            payment_method="",

            payment_reference="",

            coupon=coupon,

            subtotal=subtotal,

            discount_amount=discount_amount,

            total=total,

            shipping_full_name=shipping_address.full_name,
            shipping_phone=shipping_address.phone,
            shipping_address_line1=shipping_address.address_line1,
            shipping_address_line2=(
                shipping_address.address_line2 or ""
            ),
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
                and billing_address.address_line2
                else shipping_address.address_line2 or ""
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

        # ---------------------------------------------------------
        # Create OrderItem snapshots
        # ---------------------------------------------------------

        order_items = []

        for item, variant in variants:

            unit_price = Decimal(
                variant.price
                if variant.price is not None
                else variant.product.price
            )

            order_items.append(
                OrderItem(
                    order=order,

                    product=variant.product,

                    variant=variant,

                    product_name=variant.product.name,

                    variant_name=variant.name or "",

                    sku=variant.sku or "",

                    quantity=item.quantity,

                    unit_price=unit_price,

                    total_price=(
                        unit_price * item.quantity
                    ),
                )
            )

        OrderItem.objects.bulk_create(
            order_items
        )

        # ---------------------------------------------------------
        # Clear cart after order creation
        # ---------------------------------------------------------

        cart.items.all().delete()

        cart.coupon = None

        cart.save(
            update_fields=[
                "coupon",
                "updated_at",
            ]
        )

    # -------------------------------------------------------------
    # Clear checkout session data
    # -------------------------------------------------------------

    request.session.pop(
        "checkout_shipping_address_id",
        None,
    )

    request.session.pop(
        "checkout_billing_address_id",
        None,
    )

    request.session[
        "last_order_id"
    ] = order.id

    return redirect(
        "payment",
        order_number=order.order_number,
    )


def generate_payment_reference():
    """
    Generate a unique demo payment reference.
    """

    return (
        f"DEMO-{uuid.uuid4().hex[:12].upper()}"
    )


def finalize_order_inventory_and_coupon(order):
    """
    Finalize inventory and coupon usage.

    IMPORTANT:
    This function MUST be called inside transaction.atomic().

    It:
    1. Locks inventory rows.
    2. Re-checks stock.
    3. Deducts inventory.
    4. Re-validates the coupon.
    5. Records coupon usage.

    It also prevents the same order from consuming inventory twice.
    """

    # -------------------------------------------------------------
    # Safety check against double finalization
    # -------------------------------------------------------------

    if order.status == "processing":
        raise ValueError(
            "This order has already been finalized."
        )

    if order.payment_status == "paid":
        raise ValueError(
            "This order has already been paid."
        )

    # -------------------------------------------------------------
    # Lock coupon if present
    # -------------------------------------------------------------

    coupon = None

    if order.coupon_id:

        coupon = (
            Coupon.objects
            .select_for_update()
            .filter(id=order.coupon_id)
            .first()
        )

        if coupon is None:
            raise ValueError(
                "The coupon associated with this order is no longer available."
            )

        now = timezone.now()

        if not (
            coupon.is_active
            and coupon.valid_from <= now <= coupon.valid_until
        ):
            raise ValueError(
                "The coupon applied to this order is no longer valid."
            )

        if (
            coupon.discount_type == "percentage"
            and coupon.discount_value > 100
        ):
            raise ValueError(
                "The coupon has an invalid discount value."
            )

        if order.subtotal < coupon.minimum_order_amount:
            raise ValueError(
                "This order no longer meets the minimum amount "
                "required for the coupon."
            )

        # ---------------------------------------------------------
        # Overall coupon usage limit
        # ---------------------------------------------------------

        total_usage = CouponUsage.objects.filter(
            coupon=coupon
        ).count()

        if (
            coupon.usage_limit is not None
            and total_usage >= coupon.usage_limit
        ):
            raise ValueError(
                "The coupon has reached its usage limit."
            )

        # ---------------------------------------------------------
        # Per-user coupon usage limit
        # ---------------------------------------------------------

        user_usage = CouponUsage.objects.filter(
            coupon=coupon,
            user=order.user,
        ).count()

        if user_usage >= coupon.per_user_limit:
            raise ValueError(
                "You have already reached the usage limit "
                "for this coupon."
            )

    # -------------------------------------------------------------
    # Lock and validate inventory
    # -------------------------------------------------------------

    order_items = order.items.select_related(
        "variant",
        "variant__product",
    )

    locked_inventory = []

    for item in order_items:

        inventory = (
            Inventory.objects
            .select_for_update()
            .filter(
                variant=item.variant,
                variant__is_active=True,
                variant__product__is_active=True,
            )
            .first()
        )

        if inventory is None:
            raise ValueError(
                f"Inventory unavailable for "
                f"{item.product_name}."
            )

        if inventory.quantity < item.quantity:
            raise ValueError(
                f"Insufficient stock for "
                f"{item.product_name} - "
                f"{item.variant_name}. "
                f"Only {inventory.quantity} left."
            )

        locked_inventory.append(
            (item, inventory)
        )

    # -------------------------------------------------------------
    # Deduct inventory
    # -------------------------------------------------------------

    for item, inventory in locked_inventory:

        inventory.quantity -= item.quantity

        inventory.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

    # -------------------------------------------------------------
    # Record coupon usage
    # -------------------------------------------------------------

    if coupon:

        existing_usage = CouponUsage.objects.filter(
            coupon=coupon,
            user=order.user,
        ).first()

        if existing_usage is None:

            CouponUsage.objects.create(
                coupon=coupon,
                user=order.user,
            )


@login_required
def payment(request, order_number):
    """
    Display payment page.

    Failed Demo Card payments can be retried.

    A COD order that has already been finalized goes directly
    to confirmation.
    """

    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    # -------------------------------------------------------------
    # Already completed Demo Card payment
    # -------------------------------------------------------------

    if order.payment_status == "paid":
        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    # -------------------------------------------------------------
    # COD has already been finalized
    # -------------------------------------------------------------

    if (
        order.payment_method == "Cash on Delivery"
        and order.status == "processing"
    ):
        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    return render(
        request,
        "orders/payment.html",
        {
            "order": order,
        },
    )


@login_required
def process_payment(request, order_number):
    """
    Process Demo Card or Cash on Delivery.

    Demo Card:
        success -> deduct stock + coupon usage + mark paid

        failure -> mark payment failed
                   but keep order retryable

    COD:
        finalize inventory + coupon usage
        keep payment status pending
        mark order processing
    """

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

    # -------------------------------------------------------------
    # Already paid
    # -------------------------------------------------------------

    if order.payment_status == "paid":
        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    # -------------------------------------------------------------
    # COD already finalized
    # -------------------------------------------------------------

    if (
        order.payment_method == "Cash on Delivery"
        and order.status == "processing"
    ):
        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    payment_method = request.POST.get(
        "payment_method",
        "",
    ).strip()

    # =============================================================
    # DEMO CARD
    # =============================================================

    if payment_method == "demo_card":

        demo_result = request.POST.get(
            "demo_result",
            "",
        ).strip()

        # ---------------------------------------------------------
        # Demo payment failed
        # ---------------------------------------------------------

        if demo_result == "failure":

            order.payment_method = "Demo Card"

            order.payment_reference = (
                generate_payment_reference()
            )

            order.payment_status = "failed"

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
                "Demo card payment failed. "
                "You can retry the payment."
            )

            return redirect(
                "payment",
                order_number=order.order_number,
            )

        # ---------------------------------------------------------
        # Demo payment success
        # ---------------------------------------------------------

        if demo_result == "success":

            payment_reference = (
                generate_payment_reference()
            )

            try:

                with transaction.atomic():

                    locked_order = (
                        Order.objects
                        .select_for_update()
                        .get(id=order.id)
                    )

                    # Final safety check
                    if locked_order.payment_status == "paid":
                        return redirect(
                            "order_confirmation",
                            order_number=locked_order.order_number,
                        )

                    if (
                        locked_order.status == "processing"
                        and locked_order.payment_method
                        == "Cash on Delivery"
                    ):
                        return redirect(
                            "order_confirmation",
                            order_number=locked_order.order_number,
                        )

                    # Finalize inventory + coupon
                    finalize_order_inventory_and_coupon(
                        locked_order
                    )

                    locked_order.payment_method = (
                        "Demo Card"
                    )

                    locked_order.payment_reference = (
                        payment_reference
                    )

                    locked_order.payment_status = (
                        "paid"
                    )

                    locked_order.status = (
                        "processing"
                    )

                    locked_order.save(
                        update_fields=[
                            "payment_method",
                            "payment_status",
                            "payment_reference",
                            "status",
                            "updated_at",
                        ]
                    )

            except ValueError as e:

                messages.error(
                    request,
                    str(e),
                )

                return redirect(
                    "payment",
                    order_number=order.order_number,
                )

            messages.success(
                request,
                "Demo card payment completed successfully."
            )

            return redirect(
                "order_confirmation",
                order_number=order.order_number,
            )

        # ---------------------------------------------------------
        # Invalid demo result
        # ---------------------------------------------------------

        messages.error(
            request,
            "Please select a valid demo payment result."
        )

        return redirect(
            "payment",
            order_number=order.order_number,
        )

    # =============================================================
    # CASH ON DELIVERY
    # =============================================================

    elif payment_method == "cod":

        try:

            with transaction.atomic():

                locked_order = (
                    Order.objects
                    .select_for_update()
                    .get(id=order.id)
                )

                # Prevent duplicate COD finalization
                if (
                    locked_order.status == "processing"
                    and locked_order.payment_method
                    == "Cash on Delivery"
                ):
                    return redirect(
                        "order_confirmation",
                        order_number=locked_order.order_number,
                    )

                # Finalize inventory + coupon
                finalize_order_inventory_and_coupon(
                    locked_order
                )

                locked_order.payment_method = (
                    "Cash on Delivery"
                )

                # COD is not paid yet
                locked_order.payment_status = (
                    "pending"
                )

                locked_order.payment_reference = ""

                locked_order.status = (
                    "processing"
                )

                locked_order.save(
                    update_fields=[
                        "payment_method",
                        "payment_status",
                        "payment_reference",
                        "status",
                        "updated_at",
                    ]
                )

        except ValueError as e:

            messages.error(
                request,
                str(e),
            )

            return redirect(
                "payment",
                order_number=order.order_number,
            )

        messages.success(
            request,
            "Cash on Delivery selected successfully."
        )

        return redirect(
            "order_confirmation",
            order_number=order.order_number,
        )

    # =============================================================
    # INVALID PAYMENT METHOD
    # =============================================================

    else:

        messages.error(
            request,
            "Please select a valid payment method."
        )

        return redirect(
            "payment",
            order_number=order.order_number,
        )


@login_required
def order_confirmation(request, order_number):

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_number=order_number,
        user=request.user,
    )

    return render(
        request,
        "orders/order_confirmation.html",
        {
            "order": order,
        },
    )


@login_required
def my_orders(request):

    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/my_orders.html",
        {
            "orders": orders,
        },
    )


@login_required
def order_detail(request, order_number):

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        order_number=order_number,
        user=request.user,
    )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
        },
    )