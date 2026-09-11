from rest_framework import serializers

from products.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductImage,
    ProductVariant,
)

from cart.models import Cart, CartItem

from wishlist.models import Wishlist, WishlistItem

from coupons.models import Coupon

from orders.models import Order, OrderItem

from reviews.models import Review


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
        ]


class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
        ]


class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage

        fields = [
            "id",
            "image",
            "alt_text",
            "is_primary",
        ]


class InventorySerializer(serializers.ModelSerializer):

    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Inventory

        fields = [
            "quantity",
            "low_stock_threshold",
            "is_low_stock",
        ]


class ProductVariantSerializer(serializers.ModelSerializer):

    inventory = InventorySerializer(
        read_only=True,
    )

    class Meta:
        model = ProductVariant

        fields = [
            "id",
            "name",
            "sku",
            "price",
            "is_active",
            "inventory",
        ]


class ProductSerializer(serializers.ModelSerializer):

    category = CategorySerializer(
        read_only=True,
    )

    brand = BrandSerializer(
        read_only=True,
    )

    images = ProductImageSerializer(
        many=True,
        read_only=True,
    )

    variants = ProductVariantSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Product

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "sku",
            "is_active",
            "category",
            "brand",
            "images",
            "variants",
            "created_at",
            "updated_at",
        ]

class CartItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="variant.product.name",
        read_only=True,
    )

    variant_name = serializers.CharField(
        source="variant.name",
        read_only=True,
    )

    sku = serializers.CharField(
        source="variant.sku",
        read_only=True,
    )

    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    stock_quantity = serializers.IntegerField(
        source="variant.inventory.quantity",
        read_only=True,
    )

    class Meta:
        model = CartItem

        fields = [
            "id",
            "variant",
            "product_name",
            "variant_name",
            "sku",
            "quantity",
            "unit_price",
            "total_price",
            "stock_quantity",
        ]

    def to_representation(self, instance):

        data = super().to_representation(instance)

        data["unit_price"] = instance.unit_price
        data["total_price"] = instance.total_price

        return data


class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(
        many=True,
        read_only=True,
    )

    total_quantity = serializers.IntegerField(
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    discount_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    coupon_code = serializers.CharField(
        source="coupon.code",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Cart

        fields = [
            "id",
            "items",
            "total_quantity",
            "subtotal",
            "coupon_code",
            "discount_amount",
            "total",
        ]

    def to_representation(self, instance):

        data = super().to_representation(instance)

        data["total_quantity"] = instance.total_quantity
        data["subtotal"] = instance.subtotal
        data["discount_amount"] = instance.discount_amount
        data["total"] = instance.total

        return data


class CartItemAddSerializer(serializers.Serializer):

    variant_id = serializers.IntegerField(
        min_value=1,
    )

    quantity = serializers.IntegerField(
        min_value=1,
    )


class CartItemUpdateSerializer(serializers.Serializer):

    item_id = serializers.IntegerField(
        min_value=1,
    )

    quantity = serializers.IntegerField(
        min_value=1,
    )


class CartItemRemoveSerializer(serializers.Serializer):

    item_id = serializers.IntegerField(
        min_value=1,
    )        

class WishlistItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    product_slug = serializers.CharField(
        source="product.slug",
        read_only=True,
    )

    product_price = serializers.DecimalField(
        source="product.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    brand_name = serializers.CharField(
        source="product.brand.name",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="product.category.name",
        read_only=True,
    )

    class Meta:
        model = WishlistItem

        fields = [
            "id",
            "product",
            "product_name",
            "product_slug",
            "product_price",
            "brand_name",
            "category_name",
            "created_at",
        ]


class WishlistSerializer(serializers.ModelSerializer):

    items = WishlistItemSerializer(
        many=True,
        read_only=True,
    )

    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist

        fields = [
            "id",
            "items",
            "item_count",
            "created_at",
            "updated_at",
        ]

    def get_item_count(self, obj):

        return obj.items.count()


class WishlistAddSerializer(serializers.Serializer):

    product_id = serializers.IntegerField(
        min_value=1,
    )


class WishlistRemoveSerializer(serializers.Serializer):

    item_id = serializers.IntegerField(
        min_value=1,
    )    

class CouponSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coupon

        fields = [
            "id",
            "code",
            "discount_type",
            "discount_value",
            "minimum_order_amount",
            "valid_from",
            "valid_until",
        ]


class CouponApplySerializer(serializers.Serializer):

    code = serializers.CharField(
        max_length=50,
    )


class CouponRemoveSerializer(serializers.Serializer):

    pass   

class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem

        fields = [
            "id",
            "product",
            "variant",
            "product_name",
            "variant_name",
            "sku",
            "quantity",
            "unit_price",
            "total_price",
        ]


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order

        fields = [
            "id",
            "order_number",
            "status",
            "payment_status",
            "payment_method",
            "payment_reference",
            "subtotal",
            "discount_amount",
            "total",
            "shipping_full_name",
            "shipping_phone",
            "shipping_address_line1",
            "shipping_address_line2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "billing_full_name",
            "billing_phone",
            "billing_address_line1",
            "billing_address_line2",
            "billing_city",
            "billing_state",
            "billing_postal_code",
            "billing_country",
            "items",
            "created_at",
            "updated_at",
        ]

class ReviewSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )

    verified_purchase = serializers.SerializerMethodField()

    class Meta:
        model = Review

        fields = [
            "id",
            "product",
            "product_name",
            "username",
            "rating",
            "title",
            "comment",
            "verified_purchase",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "user",
            "product",
            "product_name",
            "username",
            "verified_purchase",
            "created_at",
            "updated_at",
        ]

    def get_verified_purchase(self, obj):

        return obj.order.status in [
            "processing",
            "shipped",
            "delivered",
        ]

class ReviewCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review

        fields = [
            "rating",
            "title",
            "comment",
        ]        