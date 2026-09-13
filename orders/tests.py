from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Address
from cart.models import Cart, CartItem
from coupons.models import Coupon
from orders.models import Order, OrderItem
from products.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductVariant,
)
from reviews.models import Review
from wishlist.models import Wishlist, WishlistItem


class ShopSphereTestCase(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="testpass123",
        )

        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
        )

        self.brand = Brand.objects.create(
            name="TestBrand",
            slug="test-brand",
        )

        self.product = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name="Test Laptop",
            slug="test-laptop",
            description="A test product.",
            price=Decimal("50000.00"),
            sku="TEST-LAPTOP-001",
            is_active=True,
        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            name="Standard",
            sku="TEST-LAPTOP-STD",
            price=Decimal("48000.00"),
            is_active=True,
        )

        self.inventory = Inventory.objects.create(
            variant=self.variant,
            quantity=10,
            low_stock_threshold=3,
        )

        self.address = Address.objects.create(
            user=self.user,
            address_type="shipping",
            full_name="Test User",
            phone="9876543210",
            address_line1="123 Test Street",
            address_line2="",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            country="India",
            is_default=True,
        )

    def create_order(
        self,
        user=None,
        status="pending",
        payment_status="pending",
        quantity=1,
    ):

        user = user or self.user

        order = Order.objects.create(
            user=user,
            order_number=f"TEST-{Order.objects.count() + 1:06d}",
            status=status,
            payment_status=payment_status,
            subtotal=Decimal("48000.00") * quantity,
            discount_amount=Decimal("0.00"),
            total=Decimal("48000.00") * quantity,
            shipping_full_name="Test User",
            shipping_phone="9876543210",
            shipping_address_line1="123 Test Street",
            shipping_address_line2="",
            shipping_city="Bengaluru",
            shipping_state="Karnataka",
            shipping_postal_code="560001",
            shipping_country="India",
            billing_full_name="Test User",
            billing_phone="9876543210",
            billing_address_line1="123 Test Street",
            billing_address_line2="",
            billing_city="Bengaluru",
            billing_state="Karnataka",
            billing_postal_code="560001",
            billing_country="India",
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            variant=self.variant,
            product_name=self.product.name,
            variant_name=self.variant.name,
            sku=self.variant.sku,
            quantity=quantity,
            unit_price=Decimal("48000.00"),
            total_price=Decimal("48000.00") * quantity,
        )

        return order


# ============================================================
# PRODUCT AND INVENTORY TESTS
# ============================================================

class ProductInventoryTests(ShopSphereTestCase):

    def test_inventory_low_stock_property(self):

        self.inventory.quantity = 3
        self.inventory.save()

        self.assertTrue(
            self.inventory.is_low_stock
        )

    def test_inventory_not_low_stock(self):

        self.inventory.quantity = 10
        self.inventory.save()

        self.assertFalse(
            self.inventory.is_low_stock
        )

    def test_product_string_representation(self):

        self.assertEqual(
            str(self.product),
            "Test Laptop",
        )


# ============================================================
# CART TESTS
# ============================================================

class CartTests(ShopSphereTestCase):

    def test_cart_subtotal(self):

        cart = Cart.objects.create(
            user=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=2,
        )

        self.assertEqual(
            cart.subtotal,
            Decimal("96000.00"),
        )

    def test_cart_total_quantity(self):

        cart = Cart.objects.create(
            user=self.user,
        )

        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=3,
        )

        self.assertEqual(
            cart.total_quantity,
            3,
        )

    def test_cart_fixed_coupon_discount(self):

        coupon = Coupon.objects.create(
            code="SAVE500",
            discount_type="fixed",
            discount_value=Decimal("500.00"),
            minimum_order_amount=Decimal("1000.00"),
            valid_from=timezone.now(),
            valid_until=timezone.now()
            + timezone.timedelta(days=10),
            is_active=True,
        )

        cart = Cart.objects.create(
            user=self.user,
            coupon=coupon,
        )

        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=1,
        )

        self.assertEqual(
            cart.discount_amount,
            Decimal("500.00"),
        )

        self.assertEqual(
            cart.total,
            Decimal("47500.00"),
        )


# ============================================================
# WISHLIST TESTS
# ============================================================

class WishlistTests(ShopSphereTestCase):

    def test_wishlist_item_creation(self):

        wishlist = Wishlist.objects.create(
            user=self.user,
        )

        item = WishlistItem.objects.create(
            wishlist=wishlist,
            product=self.product,
        )

        self.assertEqual(
            item.product,
            self.product,
        )

        self.assertEqual(
            wishlist.items.count(),
            1,
        )


# ============================================================
# ORDER AND PAYMENT TESTS
# ============================================================

class OrderPaymentTests(ShopSphereTestCase):

    def test_demo_card_success_marks_order_paid(self):

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        order = self.create_order()

        response = self.client.post(
            reverse(
                "process_payment",
                kwargs={
                    "order_number": order.order_number,
                },
            ),
            {
                "payment_method": "demo_card",
                "demo_result": "success",
            },
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            order.payment_status,
            "paid",
        )

        self.assertEqual(
            order.status,
            "processing",
        )

        self.assertEqual(
            self.inventory.quantity,
            9,
        )

    def test_demo_card_failure_does_not_reduce_inventory(self):

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        order = self.create_order()

        response = self.client.post(
            reverse(
                "process_payment",
                kwargs={
                    "order_number": order.order_number,
                },
            ),
            {
                "payment_method": "demo_card",
                "demo_result": "failure",
            },
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            order.payment_status,
            "failed",
        )

        self.assertEqual(
            order.status,
            "pending",
        )

        self.assertEqual(
            self.inventory.quantity,
            10,
        )

    def test_cod_keeps_payment_pending_and_reduces_inventory(self):

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        order = self.create_order()

        response = self.client.post(
            reverse(
                "process_payment",
                kwargs={
                    "order_number": order.order_number,
                },
            ),
            {
                "payment_method": "cod",
            },
        )

        order.refresh_from_db()
        self.inventory.refresh_from_db()

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            order.payment_method,
            "Cash on Delivery",
        )

        self.assertEqual(
            order.payment_status,
            "pending",
        )

        self.assertEqual(
            order.status,
            "processing",
        )

        self.assertEqual(
            self.inventory.quantity,
            9,
        )

    def test_completed_payment_cannot_deduct_inventory_twice(self):

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        order = self.create_order()

        payment_url = reverse(
            "process_payment",
            kwargs={
                "order_number": order.order_number,
            },
        )

        self.client.post(
            payment_url,
            {
                "payment_method": "demo_card",
                "demo_result": "success",
            },
        )

        self.inventory.refresh_from_db()

        quantity_after_first_payment = (
            self.inventory.quantity
        )

        self.client.post(
            payment_url,
            {
                "payment_method": "demo_card",
                "demo_result": "success",
            },
        )

        self.inventory.refresh_from_db()

        self.assertEqual(
            self.inventory.quantity,
            quantity_after_first_payment,
        )


# ============================================================
# ORDER ACCESS CONTROL TESTS
# ============================================================

class OrderSecurityTests(ShopSphereTestCase):

    def test_user_cannot_access_another_users_order(self):

        order = self.create_order(
            user=self.other_user,
        )

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        response = self.client.get(
            reverse(
                "order_detail",
                kwargs={
                    "order_number": order.order_number,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )


# ============================================================
# REVIEW TESTS
# ============================================================

class ReviewTests(ShopSphereTestCase):

    def test_review_rating_is_stored(self):

        order = self.create_order(
            status="delivered",
            payment_status="paid",
        )

        review = Review.objects.create(
            user=self.user,
            product=self.product,
            order=order,
            rating=5,
            title="Excellent",
            comment="Very good product.",
        )

        self.assertEqual(
            review.rating,
            5,
        )

        self.assertEqual(
            Review.objects.count(),
            1,
        )


# ============================================================
# REST API TESTS
# ============================================================

class APITests(ShopSphereTestCase):

    def test_api_root_is_public(self):

        response = self.client.get(
            reverse("api_root"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "products",
            response.json(),
        )

    def test_api_product_list_is_public(self):

        response = self.client.get(
            reverse("api_product_list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.json()),
            1,
        )

    def test_api_cart_requires_authentication(self):

        response = self.client.get(
            reverse("api_cart"),
        )

        self.assertIn(
            response.status_code,
            [401, 403],
        )

    def test_api_authenticated_cart_access(self):

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        response = self.client.get(
            reverse("api_cart"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "items",
            response.json(),
        )

    def test_api_wishlist_requires_authentication(self):

        response = self.client.get(
            reverse("api_wishlist"),
        )

        self.assertIn(
            response.status_code,
            [401, 403],
        )

    def test_api_order_list_only_returns_own_orders(self):

        own_order = self.create_order(
            user=self.user,
        )

        self.create_order(
            user=self.other_user,
        )

        self.client.login(
            username="testuser",
            password="testpass123",
        )

        response = self.client.get(
            reverse("api_order_list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertEqual(
            len(data),
            1,
        )

        self.assertEqual(
            data[0]["order_number"],
            own_order.order_number,
        )