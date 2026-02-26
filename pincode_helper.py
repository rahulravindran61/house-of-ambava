"""
PINCODE AVAILABILITY HELPER SCRIPT
==================================

This script demonstrates how to use the pincode checking functionality.
Run: python manage.py shell < pincode_helper.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct, PincodeAvailability

print("=" * 70)
print("PINCODE AVAILABILITY - HELPER FUNCTIONS")
print("=" * 70)

# Example 1: Add pincodes for a product
print("\n[EXAMPLE 1] Adding pincodes for a product:\n")
try:
    product = ShowcaseProduct.objects.first()
    if product:
        # Add sample pincodes
        sample_pincodes = ['110001', '110002', '110005', '110007']
        for pincode in sample_pincodes:
            availability, created = PincodeAvailability.objects.get_or_create(
                product=product,
                pincode=pincode,
                defaults={
                    'is_available': True,
                    'delivery_days': 3,
                    'extra_charge': 0
                }
            )
            status = "Created" if created else "Already exists"
            print(f"  Pincode {pincode}: {status}")
        print(f"\n✓ Sample pincodes added for: {product.name}")
except Exception as e:
    print(f"  Error: {e}")

# Example 2: Check if product is available in a pincode
print("\n[EXAMPLE 2] Check product availability in a pincode:\n")
try:
    product = ShowcaseProduct.objects.first()
    if product:
        test_pincodes = ['110001', '110080', '110090']  # 110080 doesn't exist
        for pincode in test_pincodes:
            is_avail, delivery_days, charge = PincodeAvailability.is_product_available_in_pincode(
                product.id, pincode
            )
            status = "✓ Available" if is_avail else "✗ Not Available"
            info = f"{delivery_days} days, ₹{charge} extra" if is_avail else ""
            print(f"  {product.name} in {pincode}: {status} {info}")
except Exception as e:
    print(f"  Error: {e}")

# Example 3: Get all available pincodes for a product
print("\n[EXAMPLE 3] Get all available pincodes for a product:\n")
try:
    product = ShowcaseProduct.objects.first()
    if product:
        pincodes = PincodeAvailability.get_pincodes_for_product(product.id)
        pincode_list = list(pincodes)
        if pincode_list:
            print(f"  Product: {product.name}")
            print(f"  Available in: {', '.join(pincode_list)}")
        else:
            print(f"  No pincodes added yet for: {product.name}")
except Exception as e:
    print(f"  Error: {e}")

# Example 4: Query pincodes with custom filters
print("\n[EXAMPLE 4] Advanced queries:\n")
try:
    # Find all available products in a specific pincode
    test_pincode = '110001'
    availabilities = PincodeAvailability.objects.filter(
        pincode=test_pincode,
        is_available=True
    )
    print(f"  Products available in {test_pincode}:")
    for avail in availabilities:
        print(f"    - {avail.product.name} ({avail.delivery_days} days, ₹{avail.extra_charge})")
    
    # Find products with premium delivery (extra charge)
    print(f"\n  Products with extra shipping charges:")
    expensive_shipping = PincodeAvailability.objects.filter(
        extra_charge__gt=0,
        is_available=True
    )
    for avail in expensive_shipping:
        print(f"    - {avail.product.name} to {avail.pincode}: ₹{avail.extra_charge}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 70)
print("USEFUL CODE SNIPPETS:")
print("=" * 70)

code_snippet = '''
# In your views.py, check pincode availability:
from store.models import PincodeAvailability

def check_delivery(request, product_id):
    pincode = request.POST.get('pincode')
    
    is_available, delivery_days, extra_charge = PincodeAvailability.is_product_available_in_pincode(
        product_id, pincode
    )
    
    if is_available:
        return JsonResponse({
            'available': True,
            'delivery_days': delivery_days,
            'extra_charge': float(extra_charge)
        })
    else:
        return JsonResponse({
            'available': False,
            'message': f'Not available in pincode {pincode}'
        })

# Or get all pincodes for a product:
available_pincodes = PincodeAvailability.get_pincodes_for_product(product_id)
'''

print(code_snippet)
print("=" * 70)
