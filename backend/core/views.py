# core/views.py
from django.db.models import Sum, Count
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

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
from .serializers import (
    RestaurantSerializer,
    DeliveryZoneSerializer,
    CustomerSerializer,
    DeliveryAddressSerializer,
    MenuCategorySerializer,
    MenuItemSerializer,
    CouponSerializer,
    DailyLimitSerializer,
    DriverSerializer,
    DeliverySerializer,
    OrderSerializer,
    OrderItemSerializer,
    EventSerializer,
    OrderCreateSerializer,
)


# --------- PERMISOS BÁSICOS --------- #

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Lectura para todos, escritura solo staff (admin Noah).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


# --------- VIEWSETS PRINCIPALES --------- #

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAdminUser]


class DeliveryZoneViewSet(viewsets.ModelViewSet):
    queryset = DeliveryZone.objects.all()
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.IsAdminUser]


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Clientes que compran en Noah (nombre, teléfono, etc.).
    """
    queryset = Customer.objects.all().order_by("-id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrReadOnly]


class DeliveryAddressViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAddress.objects.all().order_by("-id")
    serializer_class = DeliveryAddressSerializer
    permission_classes = [IsAdminOrReadOnly]


class MenuCategoryViewSet(viewsets.ModelViewSet):
    """
    Categorías del menú (corrientes, especiales, bebidas, etc.).
    """
    queryset = MenuCategory.objects.all().order_by("sort_order", "name")
    serializer_class = MenuCategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    Platos individuales con su precio en COP.
    """
    queryset = MenuItem.objects.all().order_by("id")
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrReadOnly]


class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all().order_by("-id")
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]


class DailyLimitViewSet(viewsets.ModelViewSet):
    queryset = DailyLimit.objects.all().order_by("-date")
    serializer_class = DailyLimitSerializer
    permission_classes = [permissions.IsAdminUser]


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all().order_by("-id")
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAdminUser]


class OrderViewSet(viewsets.ModelViewSet):
    """
    Pedidos (lo usa cocina, conductores y admin).
    """
    queryset = Order.objects.select_related(
        "restaurant", "customer", "delivery_address", "coupon"
    ).prefetch_related("items__menu_item")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        restaurant_id = self.request.query_params.get("restaurant_id")
        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)

        return qs

    def create(self, request, *args, **kwargs):
        """
        Usa OrderCreateSerializer para crear pedido + líneas en un solo POST.
        """
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all().order_by("-id")
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeliveryViewSet(viewsets.ModelViewSet):
    """
    Entregas realizadas por los conductores.
    """
    queryset = Delivery.objects.select_related("order", "driver").order_by("-id")
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by("-at")
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAdminUser]


# --------- MÉTRICAS DE VENTAS (COP) --------- #

class SalesSummaryView(APIView):
    """
    Endpoint para el panel administrativo de Noah Food.

    Devuelve métricas clave en COP:
    - total_revenue: ventas totales (solo pedidos COMPLETED)
    - today_revenue: ventas de hoy
    - total_orders: número total de pedidos
    - orders_by_status: conteo por estado
    - top_items: platos más vendidos (cantidad y ventas en COP)
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request, format=None):
        today = timezone.localdate()

        base_qs = Order.objects.all()

        # Solo COMPLETED cuentan como venta efectiva
        delivered_qs = base_qs.filter(status=Order.STATUS_COMPLETED)

        total_orders = base_qs.count()
        total_revenue = delivered_qs.aggregate(
            total=Sum("total_cop")
        )["total"] or 0
        today_revenue = delivered_qs.filter(
            created_at__date=today
        ).aggregate(
            total=Sum("total_cop")
        )["total"] or 0

        orders_by_status = (
            base_qs.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        top_items_qs = (
            OrderItem.objects.values("menu_item_id", "menu_item__name")
            .annotate(
                total_qty=Sum("quantity"),
                total_revenue=Sum("line_total_cop"),
            )
            .order_by("-total_qty")[:5]
        )

        top_items = [
            {
                "menu_item_id": row["menu_item_id"],
                "name": row["menu_item__name"],
                "total_qty": row["total_qty"],
                "total_revenue": row["total_revenue"] or 0,
            }
            for row in top_items_qs
        ]

        data = {
            "currency": "COP",
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "orders_by_status": list(orders_by_status),
            "top_items": top_items,
        }

        return Response(data)
