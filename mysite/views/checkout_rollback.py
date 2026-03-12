"""Rollback helpers for checkout payment failure flows."""

from store.models import Coupon


def rollback_pending_online_order(order):
    """Restore inventory and coupon usage for a failed pending online order."""
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
