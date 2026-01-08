# core/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order, Coupon, Delivery


@receiver(post_save, sender=Order)
def update_coupon_usage(sender, instance, created, **kwargs):
    """
    Si la orden se creó con cupón, incrementa usage_count.
    """
    if created and instance.coupon:
        instance.coupon.usage_count += 1
        instance.coupon.save(update_fields=["usage_count"])


@receiver(pre_save, sender=Order)
def set_order_timestamps(sender, instance, **kwargs):
    """
    Actualiza los timestamps de cambios de estado.
    Solo aplica si la orden ya existía (pk no nulo).
    """
    if not instance.pk:
        # Orden nueva: ya se maneja pending_at en el save() del modelo
        return

    previous = sender.objects.get(pk=instance.pk)
    if previous.status == instance.status:
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
