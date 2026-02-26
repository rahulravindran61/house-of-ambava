"""
Auto-populate products from gallery images.
This script scans the media/showcase/gallery/ folder and creates products
with matching images from the showcase folder.
"""

import os
import re
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct, ProductImage
from django.core.files import File
from django.utils.text import slugify


def extract_product_name(filename):
    """Extract product name from gallery filename by removing numbering."""
    # Remove the image extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Remove patterns like " (1)", " (2)", etc.
    name = re.sub(r'\s+\(\d+\)$', '', name_without_ext)
    
    return name


def get_gallery_images_for_product(product_name, gallery_path):
    """Get all gallery images matching a product name."""
    images = []
    
    if not os.path.exists(gallery_path):
        return images
    
    for filename in sorted(os.listdir(gallery_path)):
        if extract_product_name(filename) == product_name:
            images.append(filename)
    
    return images


def get_main_image_for_product(product_name, showcase_path):
    """Get the main product image (without number suffix)."""
    for filename in os.listdir(showcase_path):
        if os.path.isfile(os.path.join(showcase_path, filename)):
            if extract_product_name(filename) == product_name:
                # Check if this is the "base" image (exact match, no numbers)
                name_without_ext = os.path.splitext(filename)[0]
                if not re.search(r'\s+\(\d+\)$', filename):
                    return filename
    
    # If no base image found, return the first one
    for filename in sorted(os.listdir(showcase_path)):
        if os.path.isfile(os.path.join(showcase_path, filename)):
            if extract_product_name(filename) == product_name:
                return filename
    
    return None


def auto_populate_products():
    """Main function to create products and link images."""
    
    gallery_path = Path('media/showcase/gallery')
    showcase_path = Path('media/showcase')
    
    if not gallery_path.exists():
        print("❌ Gallery path not found!")
        return
    
    # Extract unique product names
    product_names = set()
    for filename in os.listdir(gallery_path):
        if filename.endswith(('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')):
            product_name = extract_product_name(filename)
            product_names.add(product_name)
    
    product_names = sorted(product_names)
    print(f"\n📷 Found {len(product_names)} unique products\n")
    
    created_count = 0
    updated_count = 0
    
    for idx, product_name in enumerate(product_names, 1):
        print(f"[{idx}/{len(product_names)}] Processing: {product_name}")
        
        # Get main image
        main_image = get_main_image_for_product(product_name, showcase_path)
        if not main_image:
            print(f"   ⚠️  No main image found, skipping...")
            continue
        
        main_image_path = showcase_path / main_image
        
        # Check if product already exists
        slug = slugify(product_name)
        product, created = ShowcaseProduct.objects.get_or_create(
            slug=slug,
            defaults={
                'name': product_name,
                'category': 'bridal',  # Default category
                'price': 15000,  # Default price
                'discount_percent': 0,
                'fabric': 'Silk Blend',
                'available_sizes': 'S,M,L,XL,XXL',
            }
        )
        
        # Update the image if new or if the current image path is different
        if created or not product.image:
            try:
                with open(main_image_path, 'rb') as img_file:
                    product.image.save(
                        f'showcase/{main_image}',
                        File(img_file),
                        save=True
                    )
                product.save()
                print(f"   ✅ {'Created' if created else 'Updated'} product")
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                print(f"   ❌ Error saving product image: {e}")
                continue
        else:
            if not created:
                updated_count += 1
        
        # Get and link gallery images
        gallery_images = get_gallery_images_for_product(product_name, gallery_path)
        
        # Remove existing ProductImages to avoid duplicates
        if not created:
            product.images.all().delete()
        
        images_created = 0
        for display_order, gallery_image in enumerate(gallery_images, 1):
            try:
                gallery_image_path = gallery_path / gallery_image
                
                # Check if image already exists
                prod_image, img_created = ProductImage.objects.get_or_create(
                    product=product,
                    image=f'showcase/gallery/{gallery_image}',
                    defaults={
                        'display_order': display_order,
                        'alt_text': extract_product_name(gallery_image),
                    }
                )
                
                # If new, save the actual image file
                if img_created:
                    with open(gallery_image_path, 'rb') as img_file:
                        prod_image.image.save(
                            f'showcase/gallery/{gallery_image}',
                            File(img_file),
                            save=True
                        )
                    images_created += 1
            
            except Exception as e:
                print(f"      ⚠️  Error with gallery image {gallery_image}: {e}")
        
        print(f"   📸 Linked {images_created}/{len(gallery_images)} gallery images")
    
    print(f"\n{'='*60}")
    print(f"✅ Process complete!")
    print(f"   • Created: {created_count} products")
    print(f"   • Updated: {updated_count} products")
    print(f"   • Total: {len(product_names)} products")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    auto_populate_products()
