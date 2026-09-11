from django.urls import path

from . import views


urlpatterns = [

    path(
    "",
    views.APIRootAPIView.as_view(),
    name="api_root",
    ),

    path(
        "products/",
        views.ProductListAPIView.as_view(),
        name="api_product_list",
    ),

    path(
        "products/<slug:slug>/",
        views.ProductDetailAPIView.as_view(),
        name="api_product_detail",
    ),

    path(
    "categories/",
    views.CategoryListAPIView.as_view(),
    name="api_category_list",
    ),

    path(
    "brands/",
    views.BrandListAPIView.as_view(),
    name="api_brand_list",
    ),

     path(
        "cart/",
        views.CartAPIView.as_view(),
        name="api_cart",
    ),
    path(
        "cart/add/",
        views.CartAddAPIView.as_view(),
        name="api_cart_add",
    ),
    path(
        "cart/update/",
        views.CartUpdateAPIView.as_view(),
        name="api_cart_update",
    ),
    path(
        "cart/remove/",
        views.CartRemoveAPIView.as_view(),
        name="api_cart_remove",
    ),

    path(
    "wishlist/",
    views.WishlistAPIView.as_view(),
    name="api_wishlist",
    ),
    path(
    "wishlist/add/",
    views.WishlistAddAPIView.as_view(),
    name="api_wishlist_add",
    ),
    path(
    "wishlist/remove/",
    views.WishlistRemoveAPIView.as_view(),
    name="api_wishlist_remove",
    ),

    path(
    "coupons/",
    views.CouponListAPIView.as_view(),
    name="api_coupon_list",
    ),

    path(
    "cart/coupon/",
    views.CouponApplyAPIView.as_view(),
    name="api_coupon_apply",
    ),

    path(
    "cart/coupon/remove/",
    views.CouponRemoveAPIView.as_view(),
    name="api_coupon_remove",
    ),

    path(
    "orders/",
    views.OrderListAPIView.as_view(),
    name="api_order_list",
    ),

    path(
    "orders/<str:order_number>/",
    views.OrderDetailAPIView.as_view(),
    name="api_order_detail",
    ),

    path(
    "products/<int:product_id>/reviews/",
    views.ProductReviewListAPIView.as_view(),
    name="api_product_reviews",
),

    path(
    "products/<int:product_id>/reviews/create/",
    views.ReviewCreateAPIView.as_view(),
    name="api_review_create",
    ),

    path(
    "reviews/<int:pk>/",
    views.ReviewUpdateAPIView.as_view(),
    name="api_review_update",
    ),

    path(
    "reviews/<int:pk>/delete/",
    views.ReviewDeleteAPIView.as_view(),
    name="api_review_delete",
    ),

]