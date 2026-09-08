from django.shortcuts import render

from .models import Product


def product_list(request):
    products = Product.objects.filter(is_active=True)

    context = {
        "products": products,
    }

    return render(request, "products/product_list.html", context)