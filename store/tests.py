import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from store.models import Coupon, Order, ShowcaseProduct


@override_settings(RAZORPAY_KEY_ID='rzp_test_key', RAZORPAY_KEY_SECRET='rzp_test_secret')
class PlaceOrderRazorpayFailureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', password='pass1234', email='buyer@example.com')
        self.client.force_login(self.user)

        self.product = ShowcaseProduct.objects.create(
            name='Royal Lehenga',
            description='Test product',
            category='bridal',
            price=Decimal('12000.00'),
            image=SimpleUploadedFile('lehenga.jpg', b'filecontent', content_type='image/jpeg'),
            stock_quantity=5,
            is_active=True,
        )

        self.coupon = Coupon.objects.create(
            code='WELCOME10',
            discount_type='percent',
            discount_value=Decimal('10.00'),
            min_order_amount=Decimal('0.00'),
            per_user_limit=1,
            is_active=True,
        )

    def test_place_order_restores_stock_and_coupon_on_razorpay_failure(self):
        payload = {
            'items': [
                {
                    'name': self.product.name,
                    'quantity': 2,
                    'size': 'M',
                    'image': '/media/test.jpg',
                }
            ],
            'shipping': {
                'full_name': 'Test Buyer',
                'phone': '9999999999',
                'address_line1': '123 Test Street',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400001',
            },
            'email': 'buyer@example.com',
            'payment_method': 'razorpay',
            'coupon_code': self.coupon.code,
        }

        with patch('razorpay.Client') as mock_client:
            mock_client.return_value.order.create.side_effect = Exception('gateway down')
            response = self.client.post(
                reverse('place_order'),
                data=json.dumps(payload),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['ok'])
        self.assertEqual(Order.objects.count(), 0)

        self.product.refresh_from_db()
        self.coupon.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)
        self.assertEqual(self.coupon.used_count, 0)
