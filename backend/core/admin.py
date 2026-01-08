# core/admin.py
from django.contrib import admin

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


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "max_daily_orders")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "extra_fee_cop", "is_active")
    list_filter = ("restaurant", "is_active")
    search_fields = ("name",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "is_active")
    search_fields = ("name", "phone", "email")
    list_filter = ("is_active",)


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ("customer", "label", "city", "neighborhood", "is_default")
    list_filter = ("city", "neighborhood", "is_default")
    search_fields = ("address_line", "customer__name", "customer__phone")


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "sort_order", "is_active")
    list_filter = ("restaurant", "is_active")
    search_fields = ("name",)
    ordering = ("restaurant", "sort_order")


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "category", "price_cop", "cost_cop", "margin_cop", "is_active")
    list_filter = ("restaurant", "category", "is_active")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "restaurant", "discount_type", "percent_off", "amount_off_cop", "is_active", "usage_count")
    list_filter = ("restaurant", "discount_type", "is_active")
    search_fields = ("code",)


@admin.register(DailyLimit)
class DailyLimitAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "date", "max_orders")
    list_filter = ("restaurant", "date")


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "phone", "is_active")
    list_filter = ("restaurant", "is_active")
    search_fields = ("name", "phone")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total_cop",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "restaurant",
        "customer",
        "status",
        "channel",
        "total_cop",
        "created_at",
    )
    list_filter = ("restaurant", "status", "channel", "created_at")
    search_fields = ("order_number", "customer__name", "customer__phone")
    inlines = [OrderItemInline]
    readonly_fields = (
        "order_number",
        "subtotal_cop",
        "discount_cop",
        "delivery_fee_cop",
        "total_cop",
        "pending_at",
        "in_progress_at",
        "ready_at",
        "completed_at",
        "cancelled_at",
    )


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("order", "driver", "status", "started_at", "delivered_at")
    list_filter = ("status", "driver", "order__restaurant")
    search_fields = ("order__order_number", "driver__name")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "customer", "at")
    list_filter = ("name", "at")
    search_fields = ("name", "order__order_number", "customer__phone")
