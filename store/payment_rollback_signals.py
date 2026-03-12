"""Signals to rollback reserved stock/coupon for failed pending Razorpay orders."""

from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from .models import Coupon, Order


def _rollback_pending_online_order(order):
    """Restore stock/coupon when a pending Razorpay order fails or is deleted."""
    if not order or order.payment_method != 'razorpay' or order.payment_status != 'pending':
        return

    for item in order.items.select_related('product'):
        if item.product:
            item.product.stock_quantity += item.quantity
            item.product.save(update_fields=['stock_quantity'])

    if order.coupon_code and order.discount_amount:
        coupon = Coupon.objects.filter(code__iexact=order.coupon_code).first()
        if coupon and coupon.used_count > 0:
            coupon.used_count -= 1
            coupon.save(update_fields=['used_count'])


@receiver(pre_save, sender=Order)
def order_rollback_on_failure_transition(sender, instance, **kwargs):
    """Rollback reserved stock/coupon when pending Razorpay order moves to failed/cancelled."""
    if not instance.pk:
        return

    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    becoming_failed = (
        old.payment_status == 'pending' and
        (instance.payment_status == 'failed' or instance.status == 'cancelled')
    )
    if becoming_failed:
        _rollback_pending_online_order(old)


@receiver(pre_delete, sender=Order)
def order_rollback_on_delete(sender, instance, **kwargs):
    """Rollback reserved stock/coupon before deleting a pending Razorpay order."""
    _rollback_pending_online_order(instance)
