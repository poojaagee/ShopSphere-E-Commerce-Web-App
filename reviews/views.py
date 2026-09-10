from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from orders.models import Order, OrderItem
from products.models import Product

from .forms import ReviewForm
from .models import Review


@login_required
def create_review(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )

    purchased_order_items = OrderItem.objects.filter(
    order__user=request.user,
    product=product,
    order__status__in=[
        "processing",
        "shipped",
        "delivered",
      ],
    )
    
    if not purchased_order_items.exists():

        messages.error(
            request,
            "You can review a product only after purchasing it.",
        )

        return redirect(
            "product_detail",
            slug=product.slug,
        )

    # Check whether the user has already reviewed this product.
    existing_review = Review.objects.filter(
        user=request.user,
        product=product,
    ).first()

    if existing_review:

        messages.info(
            request,
            "You have already reviewed this product.",
        )

        return redirect(
            "product_detail",
            slug=product.slug,
        )

    if request.method == "POST":

        form = ReviewForm(request.POST)

        if form.is_valid():

            review = form.save(
                commit=False,
            )

            review.user = request.user
            review.product = product

            # Attach the review to the first order
            # in which the user purchased this product.
            review.order = (
                purchased_order_items
                .select_related("order")
                .order_by("order__created_at")
                .first()
                .order
            )

            review.save()

            messages.success(
                request,
                "Your review has been submitted successfully.",
            )

            return redirect(
                "product_detail",
                slug=product.slug,
            )

    else:

        form = ReviewForm()

    context = {
        "product": product,
        "form": form,
    }

    return render(
        request,
        "reviews/create_review.html",
        context,
    )

@login_required
def edit_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user,
    )

    if request.method == "POST":

        form = ReviewForm(
            request.POST,
            instance=review,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your review has been updated successfully.",
            )

            return redirect(
                "product_detail",
                slug=review.product.slug,
            )

    else:

        form = ReviewForm(
            instance=review,
        )

    context = {
        "product": review.product,
        "form": form,
        "review": review,
        "is_edit": True,
    }

    return render(
        request,
        "reviews/create_review.html",
        context,
    )


@login_required
def delete_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user,
    )

    product_slug = review.product.slug

    if request.method == "POST":

        review.delete()

        messages.success(
            request,
            "Your review has been deleted successfully.",
        )

        return redirect(
            "product_detail",
            slug=product_slug,
        )

    context = {
        "review": review,
    }

    return render(
        request,
        "reviews/delete_review.html",
        context,
    )