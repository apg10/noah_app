# core/models.py
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


# ----------------------------------------------------------------------
# 1. Base de tiempo (created_at / updated_at)
# ----------------------------------------------------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ----------------------------------------------------------------------
# 2. Restaurante (tenant)
# ----------------------------------------------------------------------
class Restaurant(TimeStampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    # Límite de pedidos diario (puede sobreescribirse con DailyLimit)
    max_daily_orders = models.PositiveIntegerField(
        default=100,
        help_text="Límite base de pedidos por día."
    )
    # Tarifas de delivery
    delivery_fee_base_cop = models.PositiveIntegerField(
        default=0,
        help_text="Tarifa base de envío (COP)."
    )
    delivery_fee_per_km_cop = models.PositiveIntegerField(
        default=0,
        help_text="Tarifa por km (COP)."
    )
    # Tiempo promedio de preparación
    default_prep_minutes = models.PositiveIntegerField(
        default=20,
        help_text="Tiempo promedio de preparación si no hay datos más precisos."
    )

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------
# 3. Zonas de delivery (geojson opcional)
# ----------------------------------------------------------------------
class DeliveryZone(TimeStampedModel):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="delivery_zones",
    )
    name = models.CharField(max_length=100)
    area_geojson = models.JSONField(blank=True, null=True)
    extra_fee_cop = models.PositiveIntegerField(
        default=0,
        help_text="Recargo por zona (COP)."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("restaurant", "name")
        indexes = [models.Index(fields=["restaurant"])]

    def __str__(self):
        return f"{self.restaurant.name} – {self.name}"


# ----------------------------------------------------------------------
# 4. Cliente
# ----------------------------------------------------------------------
class Customer(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_profile",
        help_text="Cuenta de usuario asociada (opcional).",
    )
    name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["phone"])]

    def __str__(self):
        return self.name or self.phone


# ----------------------------------------------------------------------
# 5. OTP
# ----------------------------------------------------------------------
class OTP(TimeStampedModel):
    phone = models.CharField(max_length=30)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"OTP {self.phone} – {self.code}"


# ----------------------------------------------------------------------
# 6. Dirección de entrega
# ----------------------------------------------------------------------
class DeliveryAddress(TimeStampedModel):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(
        max_length=100,
        help_text="Etiqueta: Casa, Trabajo, etc.",
    )
    address_line = models.CharField(max_length=255)
    neighborhood = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, default="Buga")
    notes = models.TextField(blank=True)
    lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitud (WGS84).",
    )
    lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitud (WGS84).",
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("customer", "label")
        indexes = [models.Index(fields=["customer"])]

    def __str__(self):
        return f"{self.customer} – {self.label}"


# ----------------------------------------------------------------------
# 7. Categoría del menú
# ----------------------------------------------------------------------
class MenuCategory(TimeStampedModel):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("restaurant", "name")
        ordering = ["sort_order", "name"]
        indexes = [models.Index(fields=["restaurant"])]

    def __str__(self):
        return f"{self.restaurant.name} – {self.name}"


# ----------------------------------------------------------------------
# 8. Plato del menú
# ----------------------------------------------------------------------
class MenuItem(TimeStampedModel):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menu_items",
    )
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price_cop = models.PositiveIntegerField(default=0,help_text="Precio de venta (COP).")
    cost_cop = models.PositiveIntegerField(
        default=0,
        help_text="Costo estimado (COP).",
    )
    stock = models.PositiveIntegerField(
        default=0,
        help_text="Stock aproximado (0 = sin control).",
    )
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_combination = models.BooleanField(
        default=False,
        help_text="Combo con varios componentes.",
    )
    average_prep_minutes = models.PositiveIntegerField(
        default=0,
        help_text="0 → usa restaurant.default_prep_minutes.",
    )

    class Meta:
        unique_together = ("restaurant", "name")
        indexes = [models.Index(fields=["restaurant"])]

    def __str__(self):
        return self.name

    @property
    def margin_cop(self):
        return self.price_cop - self.cost_cop


# ----------------------------------------------------------------------
# 9. Cupón
# ----------------------------------------------------------------------
class Coupon(TimeStampedModel):
    PERCENT = "percent"
    FIXED = "fixed"

    DISCOUNT_TYPE_CHOICES = [
        (PERCENT, "Porcentaje"),
        (FIXED, "Valor fijo"),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="coupons",
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default=PERCENT,
    )
    percent_off = models.PositiveIntegerField(
        default=0,
        help_text="Porcentaje de descuento (0‑100).",
    )
    amount_off_cop = models.PositiveIntegerField(
        default=0,
        help_text="Descuento fijo (COP).",
    )
    max_uses = models.PositiveIntegerField(default=0)
    usage_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["restaurant"])]

    def __str__(self):
        return self.code

    @property
    def is_expired(self):
        return bool(self.expires_at and timezone.now() > self.expires_at)

    @property
    def is_usable(self):
        if not self.is_active or self.is_expired:
            return False
        if self.max_uses and self.usage_count >= self.max_uses:
            return False
        return True


# ----------------------------------------------------------------------
# 10. Límite diario
# ----------------------------------------------------------------------
class DailyLimit(TimeStampedModel):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="daily_limits",
    )
    date = models.DateField()
    max_orders = models.PositiveIntegerField()
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("restaurant", "date")
        indexes = [models.Index(fields=["restaurant", "date"])]

    def __str__(self):
        return f"{self.restaurant.name} – {self.date} ({self.max_orders})"


# ----------------------------------------------------------------------
# 11. Conductor
# ----------------------------------------------------------------------
class Driver(TimeStampedModel):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="drivers",
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("restaurant", "phone")
        indexes = [models.Index(fields=["restaurant"])]

    def __str__(self):
        return f"{self.name} ({self.phone})"


# ----------------------------------------------------------------------
# 12. Entrega
# ----------------------------------------------------------------------
class Delivery(TimeStampedModel):
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_PICKED_UP = "PICKED_UP"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_ASSIGNED, "Asignado"),
        (STATUS_PICKED_UP, "Recogido"),
        (STATUS_DELIVERED, "Entregado"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    order = models.OneToOneField(
        "Order",
        on_delete=models.CASCADE,
        related_name="delivery",
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ASSIGNED,
    )
    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distancia estimada (km).",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["order"]), models.Index(fields=["driver"])]

    def __str__(self):
        return f"Delivery #{self.order.order_number}"


# ----------------------------------------------------------------------
# 13. Pedido
# ----------------------------------------------------------------------
class Order(TimeStampedModel):
    STATUS_PENDING = "PENDING"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_READY = "READY"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_IN_PROGRESS, "En preparación"),
        (STATUS_READY, "Listo"),
        (STATUS_COMPLETED, "Completado"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    CHANNEL_WEB = "web"
    CHANNEL_WHATSAPP = "whatsapp"
    CHANNEL_PHONE = "phone"
    CHANNEL_WALKIN = "walkin"

    CHANNEL_CHOICES = [
        (CHANNEL_WEB, "Web"),
        (CHANNEL_WHATSAPP, "WhatsApp"),
        (CHANNEL_PHONE, "Teléfono"),
        (CHANNEL_WALKIN, "Mostrador"),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    delivery_address = models.ForeignKey(
        DeliveryAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default=CHANNEL_WEB,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    subtotal_cop = models.PositiveIntegerField(default=0)
    discount_cop = models.PositiveIntegerField(default=0)
    delivery_fee_cop = models.PositiveIntegerField(default=0)
    total_cop = models.PositiveIntegerField(default=0)
    estimated_prep_minutes = models.PositiveIntegerField(default=0)
    eta_ready_at = models.DateTimeField(null=True, blank=True)
    customer_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    pending_at = models.DateTimeField(null=True, blank=True)
    in_progress_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["restaurant"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["delivery_address"]),
        ]

    def __str__(self):
        return f"Order {self.order_number} – {self.restaurant.name}"

    def save(self, *args, **kwargs):
        # Generar número único de pedido si no existe
        if not self.order_number:
            today_str = timezone.now().strftime("%Y%m%d")
            random_part = uuid.uuid4().hex[:6].upper()
            self.order_number = f"NF-{today_str}-{random_part}"

        # Asegurar que haya valores numéricos
        self.subtotal_cop = self.subtotal_cop or 0
        self.delivery_fee_cop = self.delivery_fee_cop or 0

        # Aplicar cupón si es válido
        if self.coupon and self.coupon.is_usable:
            if self.coupon.discount_type == Coupon.PERCENT:
                self.discount_cop = (self.subtotal_cop * self.coupon.percent_off) // 100
            else:
                # No permitir que el descuento exceda el subtotal
                self.discount_cop = min(self.coupon.amount_off_cop, self.subtotal_cop)
        else:
            self.discount_cop = 0

        # Calcular total
        self.total_cop = max(
            self.subtotal_cop + self.delivery_fee_cop - self.discount_cop,
            0,
        )

        # timestamps de estados básicos
        if self.status == self.STATUS_PENDING and not self.pending_at:
            self.pending_at = timezone.now()

        super().save(*args, **kwargs)

# ----------------------------------------------------------------------
# 14. Línea de pedido
# ----------------------------------------------------------------------
class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price_cop = models.PositiveIntegerField(default=0)
    line_total_cop = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("order", "menu_item")
        indexes = [models.Index(fields=["order"]), models.Index(fields=["menu_item"])]

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} ({self.order.order_number})"

    def save(self, *args, **kwargs):
        # 1) Si no se especifica precio, usar el del MenuItem
        if not self.unit_price_cop:
            self.unit_price_cop = self.menu_item.price_cop

        # 2) Calcular total de la línea
        self.line_total_cop = self.unit_price_cop * self.quantity

        # 3) Guardar la línea
        super().save(*args, **kwargs)

        # 4) Recalcular subtotal y total de la orden
        agg = self.order.items.aggregate(
            total=models.Sum("line_total_cop")
        )
        self.order.subtotal_cop = agg["total"] or 0
        # al guardar la orden, se recalcula discount/total en Order.save
        self.order.save(update_fields=["subtotal_cop", "discount_cop", "delivery_fee_cop", "total_cop"])


# ----------------------------------------------------------------------
# 15. Eventos (funnel y analítica)
# ----------------------------------------------------------------------
class Event(TimeStampedModel):
    name = models.CharField(max_length=100)
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    meta = models.JSONField(blank=True, null=True)
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["name"]), models.Index(fields=["at"])]

    def __str__(self):
        return f"{self.name} @ {self.at}"