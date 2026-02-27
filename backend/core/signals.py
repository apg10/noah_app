# core/signals.py
from django.db.models import F, Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, Coupon


@receiver(post_save, sender=Order)
def update_coupon_usage(sender, instance, created, **kwargs):
    """
    Incrementa usage_count solo si el cupon sigue siendo valido.
    Si no hay usos disponibles, limpia cupon/descuento para mantener consistencia.
    """
    if not created or not instance.coupon_id:
        return

    now = timezone.now()
    updated = (
        Coupon.objects
        .filter(
            pk=instance.coupon_id,
            restaurant_id=instance.restaurant_id,
            is_active=True,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        .filter(Q(max_uses=0) | Q(usage_count__lt=F("max_uses")))
        .update(usage_count=F("usage_count") + 1)
    )

    if updated:
        return

    # Si el cupon ya no era usable al confirmar el pedido, lo removemos.
    total_cop = max((instance.subtotal_cop or 0) + (instance.delivery_fee_cop or 0), 0)
    sender.objects.filter(pk=instance.pk).update(
        coupon=None,
        discount_cop=0,
        total_cop=total_cop,
    )
    instance.coupon_id = None
    instance.discount_cop = 0
    instance.total_cop = total_cop


@receiver(pre_save, sender=Order)
def set_order_timestamps(sender, instance, **kwargs):
    """
    Actualiza timestamps al cambiar de estado.
    Solo aplica si la orden ya existe.
    """
    if not instance.pk:
        return

    previous = sender.objects.filter(pk=instance.pk).only("status").first()
    if previous is None or previous.status == instance.status:
        return

    now = timezone.now()

    if instance.status == instance.STATUS_IN_PROGRESS:
        instance.in_progress_at = now
    elif instance.status == instance.STATUS_READY:
        instance.ready_at = now
    elif instance.status == instance.STATUS_COMPLETED:
        instance.completed_at = now
    elif instance.status == instance.STATUS_CANCELLED:
        instance.cancelled_at = now
