from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.cart_detail,
        name="cart_detail",
    ),

    path(
        "add/<int:variant_id>/",
        views.add_to_cart,
        name="add_to_cart",
    ),

    path(
        "item/<int:item_id>/increase/",
        views.increase_cart_item,
        name="increase_cart_item",
    ),

    path(
        "item/<int:item_id>/decrease/",
        views.decrease_cart_item,
        name="decrease_cart_item",
    ),

    path(
        "item/<int:item_id>/remove/",
        views.remove_cart_item,
        name="remove_cart_item",
    ),
]