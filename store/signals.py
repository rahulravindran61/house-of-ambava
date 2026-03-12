"""Django signals for store side-effects (emails, payment rollback safety)."""

from django.db.models.signals import pre_save, post_delete
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
def order_status_changed(sender, instance, **kwargs):
    """Send shipping notification email when order status changes."""
    if not instance.pk:
        return  # New order — handled in checkout view

    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if old.status != instance.status:
        from .emails import send_shipping_notification
        # Use a post-save approach via a flag to send after save completes
        instance._status_changed = True


@receiver(pre_save, sender=Order)
def order_send_status_email(sender, instance, **kwargs):
    """Deferred email sending after status change."""
    pass  # Handled via pre_save flag


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


@receiver(post_delete, sender=Order)
def order_rollback_on_delete(sender, instance, **kwargs):
    """Rollback reserved stock/coupon when pending Razorpay order is deleted."""
    _rollback_pending_online_order(instance)


from django.db.models.signals import post_save

@receiver(post_save, sender=Order)
def order_post_save_email(sender, instance, created, **kwargs):
    """Send email after order save if status changed."""
    if created:
        return
    if getattr(instance, '_status_changed', False):
        try:
            from .emails import send_shipping_notification
            send_shipping_notification(instance)
        except Exception:
            pass
        finally:
            instance._status_changed = False
