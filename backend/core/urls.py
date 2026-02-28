# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from .views import (
    AuthLoginView,
    AuthLogoutView,
    AuthMeView,
    AuthRegisterView,
    RestaurantViewSet,
    DeliveryZoneViewSet,
    CustomerViewSet,
    DeliveryAddressViewSet,
    MenuCategoryViewSet,
    MenuItemViewSet,
    CouponViewSet,
    DailyLimitViewSet,
    DriverViewSet,
    OrderViewSet,
    OrderItemViewSet,
    DeliveryViewSet,
    EventViewSet,
    SalesSummaryView,
)

router = DefaultRouter()
router.register(r"restaurants", RestaurantViewSet, basename="restaurant")
router.register(r"delivery-zones", DeliveryZoneViewSet, basename="deliveryzone")
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"addresses", DeliveryAddressViewSet, basename="address")
router.register(r"categories", MenuCategoryViewSet, basename="category")
router.register(r"menu-items", MenuItemViewSet, basename="menuitem")
router.register(r"coupons", CouponViewSet, basename="coupon")
router.register(r"daily-limits", DailyLimitViewSet, basename="dailylimit")
router.register(r"drivers", DriverViewSet, basename="driver")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemViewSet, basename="orderitem")
router.register(r"deliveries", DeliveryViewSet, basename="delivery")
router.register(r"events", EventViewSet, basename="event")

urlpatterns = [
    path("auth/login/", AuthLoginView.as_view(), name="auth-login"),
    path("auth/register/", AuthRegisterView.as_view(), name="auth-register"),
    path("auth/logout/", AuthLogoutView.as_view(), name="auth-logout"),
    path("auth/me/", AuthMeView.as_view(), name="auth-me"),
    path("", include(router.urls)),
    path("kpi/sales-summary/", SalesSummaryView.as_view(), name="sales-summary"),    
]
