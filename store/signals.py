"""Django signals for the store app — auto-send emails on status changes."""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Order


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
