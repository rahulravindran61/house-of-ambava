"""
Add remaining showcase products that don't have gallery images.
"""

import os
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct
from django.core.files import File
from django.utils.text import slugify
import re


def extract_product_name(filename):
    """Extract product name from filename."""
    name_without_ext = os.path.splitext(filename)[0]
    name = re.sub(r'\s+\(\d+\)$', '', name_without_ext)
    return name


def add_remaining_products():
    """Add product images that don't have gallery images."""
    
    showcase_path = Path('media/showcase')
    
    if not showcase_path.exists():
        print("❌ Showcase path not found!")
        return
    
    # Get all product image files
    product_images = []
    for filename in os.listdir(showcase_path):
        filepath = showcase_path / filename
        if os.path.isfile(filepath) and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            product_images.append(filename)
    
    print(f"\n📦 Found {len(product_images)} product images\n")
    
    # Get already processed products
    existing_products = set(p.name for p in ShowcaseProduct.objects.all())
    print(f"✅ Already have {len(existing_products)} products\n")
    
    created_count = 0
    skipped_count = 0
    
    for idx, image_file in enumerate(sorted(product_images), 1):
        product_name = extract_product_name(image_file)
        
        if product_name in existing_products:
            skipped_count += 1
            continue
        
        print(f"[{idx}] Adding: {product_name}")
        
        slug = slugify(product_name)
        
        try:
            # Create product
            product = ShowcaseProduct.objects.create(
                name=product_name,
                slug=slug,
                category='designer',  # Different category for these
                price=12000,
                discount_percent=0,
                fabric='Silk Blend',
                available_sizes='S,M,L,XL,XXL',
            )
            
            # Add image
            image_path = showcase_path / image_file
            with open(image_path, 'rb') as img_file:
                product.image.save(
                    f'showcase/{image_file}',
                    File(img_file),
                    save=True
                )
            
            product.save()
            print(f"   ✅ Created successfully")
            created_count += 1
            existing_products.add(product_name)
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Complete!")
    print(f"   • Added: {created_count} new products")
    print(f"   • Skipped: {skipped_count} existing products")
    print(f"   • Total products now: {len(existing_products)}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    add_remaining_products()
