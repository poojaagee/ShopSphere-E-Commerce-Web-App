from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render
from django.shortcuts import render

from .models import Brand, Category, Product


def product_list(request):
    products = Product.objects.filter(
        is_active=True
    ).select_related(
        "category",
        "brand",
    ).prefetch_related(
        "images",
    )

    # -------------------------
    # Search
    # -------------------------

    search_query = request.GET.get("q", "").strip()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(sku__icontains=search_query)
            | Q(brand__name__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    # -------------------------
    # Category Filter
    # -------------------------

    category_slug = request.GET.get(
        "category",
        ""
    ).strip()

    if category_slug:
        products = products.filter(
            category__slug=category_slug
        )

    # -------------------------
    # Brand Filter
    # -------------------------

    brand_slug = request.GET.get(
        "brand",
        ""
    ).strip()

    if brand_slug:
        products = products.filter(
            brand__slug=brand_slug
        )

    # -------------------------
    # Minimum Price
    # -------------------------

    min_price = request.GET.get(
        "min_price",
        ""
    ).strip()

    if min_price:
        try:
            min_price_value = Decimal(min_price)
            products = products.filter(
                price__gte=min_price_value
            )
        except InvalidOperation:
            min_price = ""

    # -------------------------
    # Maximum Price
    # -------------------------

    max_price = request.GET.get(
        "max_price",
        ""
    ).strip()

    if max_price:
        try:
            max_price_value = Decimal(max_price)
            products = products.filter(
                price__lte=max_price_value
            )
        except InvalidOperation:
            max_price = ""

    # -------------------------
    # Sorting
    # -------------------------

    sort = request.GET.get(
        "sort",
        "newest"
    )

    sort_options = {
        "newest": "-created_at",
        "oldest": "created_at",
        "price_low": "price",
        "price_high": "-price",
        "name_az": "name",
        "name_za": "-name",
    }

    products = products.order_by(
        sort_options.get(sort, "-created_at")
    )

    # -------------------------
    # Pagination
    # -------------------------

    paginator = Paginator(products, 6)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    # -------------------------
    # Filter Options
    # -------------------------

    categories = Category.objects.filter(
        is_active=True
    )

    brands = Brand.objects.filter(
        is_active=True
    )

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "search_query": search_query,
        "category_slug": category_slug,
        "brand_slug": brand_slug,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
    }

    return render(
        request,
        "products/product_list.html",
        context,
    )


def product_detail(request, slug):

    product = Product.objects.get(
        slug=slug,
        is_active=True,
    )

    variants = product.variants.filter(
        is_active=True
    ).select_related("inventory")

    reviews = product.reviews.select_related(
        "user",
    ).all()

    rating_summary = reviews.aggregate(
        average_rating=Avg("rating"),
        review_count=Count("id"),
    )

    rating_distribution = {
        rating: reviews.filter(
            rating=rating
        ).count()
        for rating in range(5, 0, -1)
    }

    context = {
        "product": product,
        "variants": variants,
        "reviews": reviews,
        "average_rating": rating_summary["average_rating"],
        "review_count": rating_summary["review_count"],
        "rating_distribution": rating_distribution,
    }

    return render(
        request,
        "products/product_detail.html",
        context,
    )