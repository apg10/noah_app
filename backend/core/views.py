# core/views.py
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.contrib.auth import authenticate, logout as django_logout

from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
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
    UserSessionToken,
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
    AuthLoginSerializer,
    AuthRegisterSerializer,
    AuthUserSerializer,
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


def _create_user_session(user, request):
    device_name = str(request.data.get("device_name", "") or "").strip()[:120]
    user_agent = str(request.META.get("HTTP_USER_AGENT", "") or "").strip()[:255]
    return UserSessionToken.objects.create(
        user=user,
        device_name=device_name,
        user_agent=user_agent,
    )


class AuthLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = AuthLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Usuario o contraseña inválidos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return Response(
                {"detail": "La cuenta está inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        token = _create_user_session(user, request)
        return Response(
            {"token": token.key, "user": AuthUserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class AuthRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = AuthRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = _create_user_session(user, request)
        return Response(
            {"token": token.key, "user": AuthUserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class AuthMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({"user": AuthUserSerializer(request.user).data}, status=status.HTTP_200_OK)


class AuthLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        auth = getattr(request, "auth", None)
        if hasattr(auth, "delete"):
            auth.delete()
        django_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    queryset = Customer.objects.select_related("user").all().order_by("-id")
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
            return

        if Customer.objects.filter(user=self.request.user).exists():
            raise ValidationError("El usuario autenticado ya tiene un perfil de cliente.")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if not self.request.user.is_staff and instance.user_id != self.request.user.id:
            raise PermissionDenied("No puedes modificar un perfil de cliente ajeno.")

        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(user=self.request.user)


class DeliveryAddressViewSet(viewsets.ModelViewSet):
    queryset = DeliveryAddress.objects.select_related("customer", "customer__user").all().order_by("-id")
    serializer_class = DeliveryAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(customer__user=self.request.user)

    def _validate_owned_customer(self, serializer, fallback_customer=None):
        customer = serializer.validated_data.get("customer", fallback_customer)
        if customer is None:
            raise ValidationError({"customer": "El campo customer es obligatorio."})
        if customer.user_id != self.request.user.id:
            raise PermissionDenied("No puedes usar un customer de otro usuario.")

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
            return
        self._validate_owned_customer(serializer)
        serializer.save()

    def perform_update(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
            return
        self._validate_owned_customer(
            serializer,
            fallback_customer=self.get_object().customer,
        )
        serializer.save()


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
        "restaurant", "customer", "customer__user", "delivery_address", "coupon"
    ).prefetch_related("items__menu_item")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(customer__user=self.request.user)

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
        payload = request.data.copy()

        if not request.user.is_staff:
            customer = getattr(request.user, "customer_profile", None)
            if customer is None:
                raise ValidationError(
                    {"customer": "Debes crear tu perfil de cliente antes de crear pedidos."}
                )

            payload["customer"] = customer.id
            delivery_address_id = payload.get("delivery_address")
            if delivery_address_id and not DeliveryAddress.objects.filter(
                pk=delivery_address_id,
                customer_id=customer.id,
            ).exists():
                raise ValidationError(
                    {"delivery_address": "La direccion no pertenece al usuario autenticado."}
                )

        serializer = OrderCreateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        output_serializer = OrderSerializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def _ensure_staff_for_write(self):
        if not self.request.user.is_staff:
            raise PermissionDenied("Solo staff puede modificar o eliminar pedidos.")

    def update(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().destroy(request, *args, **kwargs)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("order", "order__customer", "order__customer__user").all().order_by("-id")
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(order__customer__user=self.request.user)

    def _ensure_staff_for_write(self):
        if not self.request.user.is_staff:
            raise PermissionDenied("Solo staff puede crear o modificar lineas de pedido.")

    def create(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().destroy(request, *args, **kwargs)


class DeliveryViewSet(viewsets.ModelViewSet):
    """
    Entregas realizadas por los conductores.
    """
    queryset = Delivery.objects.select_related("order", "order__customer", "order__customer__user", "driver").order_by("-id")
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(order__customer__user=self.request.user)

    def _ensure_staff_for_write(self):
        if not self.request.user.is_staff:
            raise PermissionDenied("Solo staff puede crear o modificar entregas.")

    def create(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._ensure_staff_for_write()
        return super().destroy(request, *args, **kwargs)


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
            OrderItem.objects.filter(order__status=Order.STATUS_COMPLETED)
            .values("menu_item_id", "menu_item__name")
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
    


def healthz(request):
    """
    Liveness probe:
    - Si el proceso responde, está 'vivo'.
    - No valida DB para evitar reinicios innecesarios por fallas temporales de DB.
    """
    return JsonResponse({"status": "ok"}, status=200)

def readyz(request):
    """
    Readiness probe:
    - Debe confirmar que la app está lista para recibir tráfico.
    - Aquí validamos conectividad a la DB.
    """
    try:
        conn = connections["default"]
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
        return JsonResponse({"status": "ready", "db": "ok"}, status=200)
    except OperationalError:
        return JsonResponse({"status": "not-ready", "db": "down"}, status=503)
