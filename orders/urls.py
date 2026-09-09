from django.urls import path

from . import views


urlpatterns = [
    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),

    path(
        "checkout/review/",
        views.checkout_review,
        name="checkout_review",
    ),

    path(
        "checkout/place-order/",
        views.place_order,
        name="place_order",
    ),

    path(
        "payment/<str:order_number>/",
        views.payment,
        name="payment",
    ),

    path(
        "payment/<str:order_number>/process/",
        views.process_payment,
        name="process_payment",
    ),

    path(
        "confirmation/<str:order_number>/",
        views.order_confirmation,
        name="order_confirmation",
    ),

    path(
        "my-orders/",
        views.my_orders,
        name="my_orders",
    ),

    path(
        "my-orders/<str:order_number>/",
        views.order_detail,
        name="order_detail",
    ),
]