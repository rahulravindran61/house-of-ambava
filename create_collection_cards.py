"""
Dynamically create collection cards from shop products.
This script creates CollectionCard entries from products.
"""

import os
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct, CollectionCard
from django.core.files import File


def create_collection_cards():
    """Create collection cards from products."""
    
    # Get all active products, ordered by creation date (most recent first)
    products = ShowcaseProduct.objects.filter(is_active=True).order_by('-created_at')
    
    if not products.exists():
        print("❌ No products found!")
        return
    
    print(f"\n{'='*60}")
    print(f"🎨 Creating Collection Cards from Products")
    print(f"{'='*60}\n")
    
    # Clear existing collection cards and recreate
    existing_count = CollectionCard.objects.count()
    if existing_count > 0:
        print(f"⚠️  Clearing {existing_count} existing collection cards...")
        CollectionCard.objects.all().delete()
        print("✅ Cleared existing collection cards\n")
    
    created_count = 0
    updated_count = 0
    
    # Create collection cards from products (limit to 8)
    for idx, product in enumerate(products[:8], 1):
        print(f"[{idx}] Processing: {product.name}")
        
        # Use product name as card name
        # Description on the back will be the product description or category
        back_text = product.description or f"Exquisite {product.get_category_display()} Collection"
        if len(back_text) > 255:
            back_text = back_text[:252] + "..."
        
        # Check if collection card already exists for this product
        card, created = CollectionCard.objects.get_or_create(
            product=product,
            defaults={
                'name': product.name,
                'description': back_text,
                'display_order': idx - 1,
                'is_active': True,
            }
        )
        
        # Add the image if product has one
        if product.image:
            try:
                image_path = product.image.path
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as img_file:
                        card.image.save(
                            f'collections/{product.image.name.split("/")[-1]}',
                            File(img_file),
                            save=False
                        )
                
                # Update other fields
                card.description = back_text
                card.display_order = idx - 1
                card.save()
                
                if created:
                    print(f"   ✅ Created collection card")
                    created_count += 1
                else:
                    print(f"   🔄 Updated collection card")
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
    total_cards = CollectionCard.objects.count()
    active_cards = CollectionCard.objects.filter(is_active=True).count()
    
    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"{'='*60}")
    print(f"   • Created: {created_count}")
    print(f"   • Updated: {updated_count}")
    print(f"   • Total Collection Cards: {total_cards}")
    print(f"   • Active Cards: {active_cards}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    create_collection_cards()
