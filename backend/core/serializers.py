# core/serializers.py
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Restaurant,
    DeliveryZone,
    Customer,
    DeliveryAddress,
    MenuCategory,
    MenuItem,
    Coupon,
    DailyLimit,
    Driver,
    Delivery,
    Order,
    OrderItem,
    Event,
)


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = "__all__"


class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class DeliveryAddressSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name", read_only=True
    )

    class Meta:
        model = DeliveryAddress
        fields = "__all__"


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = "__all__"


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name", read_only=True
    )
    margin_cop = serializers.IntegerField(read_only=True)

    class Meta:
        model = MenuItem
        fields = "__all__"


class CouponSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)
    is_usable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = "__all__"


class DailyLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyLimit
        fields = "__all__"


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = "__all__"


class DeliverySerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(
        source="driver.name", read_only=True
    )

    class Meta:
        model = Delivery
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(
        source="menu_item.name", read_only=True
    )

    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ("line_total_cop",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    delivery = DeliverySerializer(read_only=True)
    customer_name = serializers.CharField(
        source="customer.name", read_only=True
    )

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = (
            "order_number",
            "subtotal_cop",
            "discount_cop",
            "delivery_fee_cop",
            "total_cop",
            "estimated_prep_minutes",
            "eta_ready_at",
            "pending_at",
            "in_progress_at",
            "ready_at",
            "completed_at",
            "cancelled_at",
        )


# Para crear pedido + items en un solo POST
class OrderCreateItemSerializer(serializers.Serializer):
    menu_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderCreateItemSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            "restaurant",
            "customer",
            "delivery_address",
            "channel",
            "coupon",
            "customer_notes",
            "items",
        )

    def validate(self, attrs):
        items = attrs.get("items", [])
        if not items:
            raise serializers.ValidationError("Debes enviar al menos un ítem en la orden.")
        return attrs

    def create(self, validated_data):
        from django.db import transaction
        from datetime import timedelta

        items_data = validated_data.pop("items")
        restaurant = validated_data["restaurant"]

        with transaction.atomic():
            subtotal = 0
            max_prep_minutes = 0

            # Creamos la orden “vacía” para luego asociar items
            order = Order.objects.create(
                **validated_data,
                subtotal_cop=0,          # se actualiza más abajo
                delivery_fee_cop=restaurant.delivery_fee_base_cop,
            )

            for item_data in items_data:
                menu_item_id = item_data["menu_item_id"]
                quantity = item_data["quantity"]
                notes = item_data.get("notes", "")

                menu_item = MenuItem.objects.get(pk=menu_item_id)

                unit_price = menu_item.price_cop
                line_total = unit_price * quantity
                subtotal += line_total

                prep_minutes = menu_item.average_prep_minutes or restaurant.default_prep_minutes
                max_prep_minutes = max(max_prep_minutes, prep_minutes)

                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    unit_price_cop=unit_price,
                    line_total_cop=line_total,
                    notes=notes,
                )

            order.subtotal_cop = subtotal
            order.estimated_prep_minutes = max_prep_minutes or restaurant.default_prep_minutes
            order.eta_ready_at = timezone.now() + timedelta(
                minutes=order.estimated_prep_minutes
            )

            # Se recalcula total / descuento en save()
            order.save()

        return order


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"
