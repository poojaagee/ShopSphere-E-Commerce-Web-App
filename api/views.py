from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from products.models import Brand, Category, Product, ProductVariant

from .serializers import (
    BrandSerializer,
    CartItemAddSerializer,
    CartItemRemoveSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
    CategorySerializer,
    CouponApplySerializer,
    CouponRemoveSerializer,
    CouponSerializer,
    ProductSerializer,
    WishlistAddSerializer,
    WishlistRemoveSerializer,
    WishlistSerializer,
    OrderSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
)

from wishlist.models import Wishlist, WishlistItem

from coupons.models import Coupon
from django.utils import timezone

from orders.models import Order

from django.shortcuts import get_object_or_404

from orders.models import OrderItem
from reviews.models import Review

class ProductListAPIView(generics.ListAPIView):

    serializer_class = ProductSerializer

    def get_queryset(self):

        return (
            Product.objects
            .filter(is_active=True)
            .select_related(
                "category",
                "brand",
            )
            .prefetch_related(
                "images",
                "variants__inventory",
            )
        )


class ProductDetailAPIView(generics.RetrieveAPIView):

    serializer_class = ProductSerializer

    lookup_field = "slug"

    def get_queryset(self):

        return (
            Product.objects
            .filter(is_active=True)
            .select_related(
                "category",
                "brand",
            )
            .prefetch_related(
                "images",
                "variants__inventory",
            )
        )

class CategoryListAPIView(generics.ListAPIView):

    serializer_class = CategorySerializer

    def get_queryset(self):

        return Category.objects.filter(
            is_active=True
        ).order_by("name")


class BrandListAPIView(generics.ListAPIView):

    serializer_class = BrandSerializer

    def get_queryset(self):

        return Brand.objects.filter(
            is_active=True
        ).order_by("name")

class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart = (
            Cart.objects
            .prefetch_related(
                "items__variant__product",
                "items__variant__inventory",
            )
            .get(
                id=cart.id
            )
        )

        serializer = CartSerializer(cart)

        return Response(serializer.data)

class CartAddAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CartItemAddSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]

        variant = (
            ProductVariant.objects
            .select_related(
                "product",
                "inventory",
            )
            .filter(
                id=variant_id,
                is_active=True,
                product__is_active=True,
            )
            .first()
        )

        if not variant:
            return Response(
                {
                    "detail": "Product variant not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not hasattr(variant, "inventory"):
            return Response(
                {
                    "detail": "Inventory information is not available."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart, created = Cart.objects.get_or_create(
            user=request.user
        )

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={
                "quantity": quantity,
            },
        )

        if not item_created:

            new_quantity = (
                cart_item.quantity + quantity
            )

            if new_quantity > variant.inventory.quantity:
                return Response(
                    {
                        "detail": (
                            f"Only {variant.inventory.quantity} "
                            "items are available in stock."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item.quantity = new_quantity
            cart_item.save()

        else:

            if quantity > variant.inventory.quantity:

                cart_item.delete()

                return Response(
                    {
                        "detail": (
                            f"Only {variant.inventory.quantity} "
                            "items are available in stock."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_201_CREATED,
        )

class CartUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CartItemUpdateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        item_id = serializer.validated_data["item_id"]
        quantity = serializer.validated_data["quantity"]

        cart = Cart.objects.filter(
            user=request.user
        ).first()

        if not cart:
            return Response(
                {
                    "detail": "Cart not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item = (
            CartItem.objects
            .select_related(
                "variant__inventory",
            )
            .filter(
                id=item_id,
                cart=cart,
            )
            .first()
        )

        if not cart_item:
            return Response(
                {
                    "detail": "Cart item not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not hasattr(
            cart_item.variant,
            "inventory",
        ):
            return Response(
                {
                    "detail": "Inventory information is not available."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity > cart_item.variant.inventory.quantity:
            return Response(
                {
                    "detail": (
                        f"Only "
                        f"{cart_item.variant.inventory.quantity} "
                        "items are available in stock."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )

class CartRemoveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CartItemRemoveSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        item_id = serializer.validated_data["item_id"]

        cart = Cart.objects.filter(
            user=request.user
        ).first()

        if not cart:
            return Response(
                {
                    "detail": "Cart not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item = CartItem.objects.filter(
            id=item_id,
            cart=cart,
        ).first()

        if not cart_item:
            return Response(
                {
                    "detail": "Cart item not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_item.delete()

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )

class WishlistAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user
        )

        wishlist = (
            Wishlist.objects
            .prefetch_related(
                "items__product__brand",
                "items__product__category",
            )
            .get(
                id=wishlist.id
            )
        )

        serializer = WishlistSerializer(
            wishlist
        )

        return Response(
            serializer.data
        )

class WishlistAddAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = WishlistAddSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        product_id = serializer.validated_data[
            "product_id"
        ]

        product = Product.objects.filter(
            id=product_id,
            is_active=True,
        ).first()

        if not product:

            return Response(
                {
                    "detail": "Product not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user
        )

        wishlist_item, item_created = (
            WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product,
            )
        )

        if not item_created:

            return Response(
                {
                    "detail": "Product is already in your wishlist."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            WishlistSerializer(wishlist).data,
            status=status.HTTP_201_CREATED,
        )

class WishlistRemoveAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = WishlistRemoveSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        item_id = serializer.validated_data[
            "item_id"
        ]

        wishlist = Wishlist.objects.filter(
            user=request.user
        ).first()

        if not wishlist:

            return Response(
                {
                    "detail": "Wishlist not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        wishlist_item = WishlistItem.objects.filter(
            id=item_id,
            wishlist=wishlist,
        ).first()

        if not wishlist_item:

            return Response(
                {
                    "detail": "Wishlist item not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        wishlist_item.delete()

        return Response(
            WishlistSerializer(wishlist).data,
            status=status.HTTP_200_OK,
        )   

class CouponListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        now = timezone.now()

        coupons = Coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now,
        ).order_by("code")

        serializer = CouponSerializer(
            coupons,
            many=True,
        )

        return Response(
            serializer.data
        )

class CouponApplyAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CouponApplySerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        code = serializer.validated_data["code"].strip()

        cart = Cart.objects.filter(
            user=request.user
        ).first()

        if not cart:

            return Response(
                {
                    "detail": "Cart not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        now = timezone.now()

        coupon = Coupon.objects.filter(
            code__iexact=code,
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now,
        ).first()

        if not coupon:

            return Response(
                {
                    "detail": "Invalid or expired coupon."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cart.subtotal < coupon.minimum_order_amount:

            return Response(
                {
                    "detail": (
                        f"Minimum order amount for this coupon "
                        f"is ₹{coupon.minimum_order_amount}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if coupon.usage_limit is not None:

            usage_count = coupon.usages.count()

            if usage_count >= coupon.usage_limit:

                return Response(
                    {
                        "detail": "This coupon has reached its usage limit."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user_usage_count = coupon.usages.filter(
            user=request.user
        ).count()

        if user_usage_count >= coupon.per_user_limit:

            return Response(
                {
                    "detail": "You have already used this coupon."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart.coupon = coupon
        cart.save(
            update_fields=[
                "coupon",
                "updated_at",
            ]
        )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )

class CouponRemoveAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CouponRemoveSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        cart = Cart.objects.filter(
            user=request.user
        ).first()

        if not cart:

            return Response(
                {
                    "detail": "Cart not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        cart.coupon = None

        cart.save(
            update_fields=[
                "coupon",
                "updated_at",
            ]
        )

        return Response(
            CartSerializer(cart).data,
            status=status.HTTP_200_OK,
        )

class OrderListAPIView(generics.ListAPIView):

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return (
            Order.objects
            .filter(
                user=self.request.user,
            )
            .prefetch_related(
                "items",
            )
            .order_by(
                "-created_at",
            )
        )

class OrderDetailAPIView(generics.RetrieveAPIView):

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    lookup_field = "order_number"

    def get_queryset(self):

        return (
            Order.objects
            .filter(
                user=self.request.user,
            )
            .prefetch_related(
                "items",
            )
        )

class ProductReviewListAPIView(generics.ListAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        product_id = self.kwargs["product_id"]

        return (
            Review.objects
            .filter(
                product_id=product_id,
            )
            .select_related(
                "user",
                "product",
                "order",
            )
            .order_by(
                "-created_at",
            )
        )

class ReviewCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):

        product = Product.objects.filter(
            id=product_id,
            is_active=True,
        ).first()

        if not product:

            return Response(
                {
                    "detail": "Product not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        existing_review = Review.objects.filter(
            user=request.user,
            product=product,
        ).first()

        if existing_review:

            return Response(
                {
                    "detail": "You have already reviewed this product."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        purchased_order_items = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status__in=[
                "processing",
                "shipped",
                "delivered",
            ],
        ).select_related(
            "order",
        ).order_by(
            "order__created_at",
        )

        first_purchase = purchased_order_items.first()

        if not first_purchase:

            return Response(
                {
                    "detail": (
                        "You can review this product only "
                        "after purchasing it."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReviewCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        review = serializer.save(
            user=request.user,
            product=product,
            order=first_purchase.order,
        )

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )

class ReviewUpdateAPIView(generics.UpdateAPIView):

    serializer_class = ReviewCreateSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "put",
        "patch",
    ]

    def get_queryset(self):

        return Review.objects.filter(
            user=self.request.user,
        )

    def perform_update(self, serializer):

        serializer.save()

class ReviewDeleteAPIView(generics.DestroyAPIView):

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Review.objects.filter(
            user=self.request.user,
        )

class APIRootAPIView(APIView):

    permission_classes = []

    def get(self, request):

        return Response(
            {
                "products": "/api/products/",
                "categories": "/api/categories/",
                "brands": "/api/brands/",
                "cart": "/api/cart/",
                "wishlist": "/api/wishlist/",
                "coupons": "/api/coupons/",
                "orders": "/api/orders/",
                "reviews": "/api/products/<product_id>/reviews/",
            }
        )                         