from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Customer, DeliveryAddress, MenuItem, Order, Restaurant, Coupon, UserSessionToken
from .serializers import OrderCreateSerializer


User = get_user_model()


class OrderCreateSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass1234")
        self.customer = Customer.objects.create(user=self.user, phone="3000000001", name="Cliente 1")
        self.restaurant_a = Restaurant.objects.create(name="Rest A", slug="rest-a")
        self.restaurant_b = Restaurant.objects.create(name="Rest B", slug="rest-b")

        self.item_a = MenuItem.objects.create(
            restaurant=self.restaurant_a,
            name="Hamburguesa A",
            price_cop=12000,
            is_active=True,
        )
        self.item_b = MenuItem.objects.create(
            restaurant=self.restaurant_b,
            name="Hamburguesa B",
            price_cop=15000,
            is_active=True,
        )

    def test_rejects_menu_item_from_other_restaurant(self):
        serializer = OrderCreateSerializer(data={
            "restaurant": self.restaurant_a.id,
            "customer": self.customer.id,
            "items": [
                {"menu_item_id": self.item_b.id, "quantity": 1},
            ],
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("items", serializer.errors)

    def test_rejects_duplicate_menu_items(self):
        serializer = OrderCreateSerializer(data={
            "restaurant": self.restaurant_a.id,
            "customer": self.customer.id,
            "items": [
                {"menu_item_id": self.item_a.id, "quantity": 1},
                {"menu_item_id": self.item_a.id, "quantity": 2},
            ],
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("items", serializer.errors)


class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="login_user",
            password="Pass1234!",
            email="login_user@example.com",
        )
        self.customer = Customer.objects.create(
            user=self.user,
            phone="3001111111",
            name="Login User",
        )

    def test_login_returns_token_and_user_payload(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "login_user", "password": "Pass1234!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "login_user")
        self.assertEqual(response.data["user"]["customer_id"], self.customer.id)

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "login_user", "password": "bad-pass"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_register_creates_user_customer_and_returns_token(self):
        payload = {
            "username": "nuevo_user",
            "email": "nuevo_user@example.com",
            "name": "Nuevo User",
            "phone": "3002222222",
            "password": "Pass1234!",
            "password_confirm": "Pass1234!",
        }
        response = self.client.post(reverse("auth-register"), payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "nuevo_user")
        self.assertIsNotNone(response.data["user"]["customer_id"])
        self.assertTrue(User.objects.filter(username="nuevo_user").exists())
        self.assertTrue(Customer.objects.filter(phone="3002222222").exists())

    def test_register_rejects_password_mismatch(self):
        payload = {
            "username": "x_user",
            "email": "x_user@example.com",
            "name": "X User",
            "phone": "3003333333",
            "password": "Pass1234!",
            "password_confirm": "Pass9999!",
        }
        response = self.client.post(reverse("auth-register"), payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password_confirm", response.data)

    def test_me_requires_valid_token(self):
        token = UserSessionToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], self.user.id)
        self.assertEqual(response.data["user"]["customer_id"], self.customer.id)

    def test_logout_revokes_token(self):
        token = UserSessionToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        response = self.client.post(reverse("auth-logout"), {}, format="json")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserSessionToken.objects.filter(key=token.key).exists())

    def test_logout_revokes_only_current_device_token(self):
        token_a = UserSessionToken.objects.create(user=self.user)
        token_b = UserSessionToken.objects.create(user=self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_a.key}")
        response = self.client.post(reverse("auth-logout"), {}, format="json")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserSessionToken.objects.filter(key=token_a.key).exists())
        self.assertTrue(UserSessionToken.objects.filter(key=token_b.key).exists())

    def test_login_creates_new_token_per_session(self):
        response_1 = self.client.post(
            reverse("auth-login"),
            {"username": "login_user", "password": "Pass1234!"},
            format="json",
        )
        response_2 = self.client.post(
            reverse("auth-login"),
            {"username": "login_user", "password": "Pass1234!"},
            format="json",
        )

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)
        self.assertNotEqual(response_1.data["token"], response_2.data["token"])
        self.assertEqual(UserSessionToken.objects.filter(user=self.user).count(), 2)


class OrderViewPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user_a = User.objects.create_user(username="user_a", password="pass1234")
        self.user_b = User.objects.create_user(username="user_b", password="pass1234")
        self.staff = User.objects.create_user(username="staff", password="pass1234", is_staff=True)

        self.customer_a = Customer.objects.create(user=self.user_a, phone="3000000010", name="A")
        self.customer_b = Customer.objects.create(user=self.user_b, phone="3000000020", name="B")

        self.restaurant = Restaurant.objects.create(name="Rest Main", slug="rest-main")
        self.menu_item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Menu Base",
            price_cop=10000,
            is_active=True,
        )

        self.address_a = DeliveryAddress.objects.create(
            customer=self.customer_a,
            label="Casa",
            address_line="Calle 1",
        )
        self.address_b = DeliveryAddress.objects.create(
            customer=self.customer_b,
            label="Casa",
            address_line="Calle 2",
        )

        self.order_a = Order.objects.create(restaurant=self.restaurant, customer=self.customer_a)
        self.order_b = Order.objects.create(restaurant=self.restaurant, customer=self.customer_b)

    def test_non_staff_only_sees_own_orders(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(reverse("order-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.order_a.id)

    def test_non_staff_cannot_update_order(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(
            reverse("order-detail", args=[self.order_a.id]),
            {"status": Order.STATUS_READY},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_non_staff_create_order_forces_own_customer(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            "restaurant": self.restaurant.id,
            "customer": self.customer_b.id,
            "delivery_address": self.address_a.id,
            "items": [{"menu_item_id": self.menu_item.id, "quantity": 1}],
        }

        response = self.client.post(reverse("order-list"), payload, format="json")

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.customer_id, self.customer_a.id)

    def test_non_staff_create_order_rejects_foreign_address(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            "restaurant": self.restaurant.id,
            "delivery_address": self.address_b.id,
            "items": [{"menu_item_id": self.menu_item.id, "quantity": 1}],
        }

        response = self.client.post(reverse("order-list"), payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("delivery_address", response.data)


class OrderSignalTests(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(name="Rest Signal", slug="rest-signal")

    def test_coupon_usage_increments_when_usable(self):
        coupon = Coupon.objects.create(
            restaurant=self.restaurant,
            code="DESC10",
            discount_type=Coupon.PERCENT,
            percent_off=10,
            max_uses=2,
            usage_count=0,
            is_active=True,
        )

        order = Order.objects.create(
            restaurant=self.restaurant,
            subtotal_cop=10000,
            delivery_fee_cop=0,
            coupon=coupon,
        )

        coupon.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(coupon.usage_count, 1)
        self.assertEqual(order.coupon_id, coupon.id)
        self.assertEqual(order.discount_cop, 1000)
        self.assertEqual(order.total_cop, 9000)

    def test_coupon_is_removed_when_not_usable(self):
        coupon = Coupon.objects.create(
            restaurant=self.restaurant,
            code="MAXED",
            discount_type=Coupon.PERCENT,
            percent_off=10,
            max_uses=1,
            usage_count=1,
            is_active=True,
        )

        order = Order.objects.create(
            restaurant=self.restaurant,
            subtotal_cop=10000,
            delivery_fee_cop=2000,
            coupon=coupon,
        )
        order.refresh_from_db()
        coupon.refresh_from_db()

        self.assertIsNone(order.coupon_id)
        self.assertEqual(order.discount_cop, 0)
        self.assertEqual(order.total_cop, 12000)
        self.assertEqual(coupon.usage_count, 1)

    def test_status_change_sets_timestamp(self):
        order = Order.objects.create(restaurant=self.restaurant)
        self.assertIsNone(order.in_progress_at)

        order.status = Order.STATUS_IN_PROGRESS
        order.save()
        order.refresh_from_db()

        self.assertIsNotNone(order.in_progress_at)
