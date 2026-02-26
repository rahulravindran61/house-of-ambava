"""
Generate dummy gallery images for each ShowcaseProduct.
Creates 3 extra views per product: Back View, Detail View, Close-up.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import ContentFile
from store.models import ShowcaseProduct, ProductImage

# Color palettes per category
PALETTES = {
    'bridal': [
        {'bg': (210, 165, 120), 'accent': (180, 130, 85)},
        {'bg': (200, 155, 115), 'accent': (170, 120, 80)},
        {'bg': (190, 145, 105), 'accent': (160, 110, 70)},
    ],
    'designer': [
        {'bg': (120, 100, 140), 'accent': (90, 70, 110)},
        {'bg': (130, 110, 150), 'accent': (100, 80, 120)},
        {'bg': (140, 120, 160), 'accent': (110, 90, 130)},
    ],
    'festival': [
        {'bg': (180, 100, 100), 'accent': (150, 70, 70)},
        {'bg': (170, 110, 90), 'accent': (140, 80, 60)},
        {'bg': (175, 95, 105), 'accent': (145, 65, 75)},
    ],
    'party': [
        {'bg': (100, 130, 150), 'accent': (70, 100, 120)},
        {'bg': (110, 140, 160), 'accent': (80, 110, 130)},
        {'bg': (90, 120, 140), 'accent': (60, 90, 110)},
    ],
    'casual': [
        {'bg': (140, 160, 130), 'accent': (110, 130, 100)},
        {'bg': (150, 170, 140), 'accent': (120, 140, 110)},
        {'bg': (130, 150, 120), 'accent': (100, 120, 90)},
    ],
}

VIEW_LABELS = ['Back View', 'Detail View', 'Close-up']


def create_gallery_image(product_name, view_label, bg_color, accent_color, width=600, height=800):
    """Create a styled placeholder gallery image."""
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Decorative pattern — diagonal lines
    for i in range(-height, width + height, 40):
        draw.line([(i, 0), (i + height, height)], fill=accent_color, width=1)

    # Central diamond
    cx, cy = width // 2, height // 2
    diamond_size = 120
    diamond = [
        (cx, cy - diamond_size),
        (cx + diamond_size, cy),
        (cx, cy + diamond_size),
        (cx - diamond_size, cy),
    ]
    draw.polygon(diamond, fill=accent_color, outline=(255, 255, 255, 180))

    # Inner diamond
    inner = 60
    inner_diamond = [
        (cx, cy - inner),
        (cx + inner, cy),
        (cx, cy + inner),
        (cx - inner, cy),
    ]
    draw.polygon(inner_diamond, fill=bg_color, outline=(255, 255, 255))

    # View label text
    try:
        font_large = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = font_large

    # View label at top
    bbox = draw.textbbox((0, 0), view_label, font=font_large)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, 50), view_label, fill=(255, 255, 255), font=font_large)

    # Product name at bottom
    short_name = product_name[:30]
    bbox2 = draw.textbbox((0, 0), short_name, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((width - tw2) // 2, height - 60), short_name, fill=(255, 255, 255), font=font_small)

    # Border frame
    draw.rectangle([(10, 10), (width - 11, height - 11)], outline=(255, 255, 255, 128), width=2)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer


def run():
    products = ShowcaseProduct.objects.filter(is_active=True)
    total_created = 0

    for product in products:
        # Skip if already has gallery images
        existing = product.images.count()
        if existing > 0:
            print(f'  ⏭ {product.name} — already has {existing} gallery images, skipping')
            continue

        palette = PALETTES.get(product.category, PALETTES['bridal'])

        for idx, (view_label, colors) in enumerate(zip(VIEW_LABELS, palette)):
            img_buffer = create_gallery_image(
                product.name,
                view_label,
                colors['bg'],
                colors['accent'],
            )
            filename = f"{product.slug}-{view_label.lower().replace(' ', '-')}.jpg"

            gallery_img = ProductImage(
                product=product,
                alt_text=f'{product.name} — {view_label}',
                display_order=idx + 1,
            )
            gallery_img.image.save(filename, ContentFile(img_buffer.read()), save=True)
            total_created += 1

        print(f'  ✓ {product.name} — 3 gallery images created')

    print(f'\nDone! Created {total_created} gallery images for {products.count()} products.')


if __name__ == '__main__':
    run()
