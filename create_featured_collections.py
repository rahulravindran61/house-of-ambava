"""
Dynamically create featured collections from shop products.
This script creates FeaturedCollection entries from the best products.
"""

import os
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct, FeaturedCollection
from django.core.files import File


def create_featured_collections():
    """Create featured collections from top products."""
    
    # Get all active products
    products = ShowcaseProduct.objects.filter(is_active=True).order_by('display_order', '-created_at')[:8]
    
    if not products.exists():
        print("❌ No products found!")
        return
    
    print(f"\n{'='*60}")
    print(f"✨ Creating Featured Collections from Products")
    print(f"{'='*60}\n")
    
    created_count = 0
    updated_count = 0
    
    # Limit to 6 featured collections
    for idx, product in enumerate(products[:6], 1):
        print(f"[{idx}] Processing: {product.name}")
        
        # Check if featured collection already exists for this product (by name)
        featured, created = FeaturedCollection.objects.get_or_create(
            name=product.name,
            defaults={
                'description': product.description or f'Beautiful {product.name}',
                'price': product.price,
                'discount_percent': product.discount_percent,
                'discounted_price': product.discounted_price,
                'display_order': idx - 1,
                'is_active': True,
            }
        )
        
        # Update or set the image if product has one
        if product.image:
            try:
                # Copy the image from product to featured collection
                image_path = product.image.path
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as img_file:
                        featured.image.save(
                            f'featured/{product.image.name.split("/")[-1]}',
                            File(img_file),
                            save=False
                        )
                
                # Update other fields
                featured.description = product.description or f'Beautiful {product.name}'
                featured.price = product.price
                featured.discount_percent = product.discount_percent
                featured.discounted_price = product.discounted_price
                featured.display_order = idx - 1
                featured.save()
                
                if created:
                    print(f"   ✅ Created featured collection")
                    created_count += 1
                else:
                    print(f"   🔄 Updated featured collection")
                    updated_count += 1
            
            except Exception as e:
                print(f"   ❌ Error processing image: {e}")
        else:
            if created:
                print(f"   ✅ Created (no image)")
                created_count += 1
            else:
                print(f"   🔄 Updated (no image)")
                updated_count += 1
    
    # Get summary
    total_featured = FeaturedCollection.objects.count()
    
    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"{'='*60}")
    print(f"   • Created: {created_count}")
    print(f"   • Updated: {updated_count}")
    print(f"   • Total Featured Collections: {total_featured}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    create_featured_collections()
