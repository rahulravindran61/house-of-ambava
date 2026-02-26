"""
Update existing showcase products with descriptions, sizes, fabric, and slugs.
Run: python manage.py shell < update_products.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct

# Map product names to rich details
PRODUCT_DETAILS = {
    'Royal Crimson Bridal Lehenga': {
        'description': 'A breathtaking bridal lehenga in deep crimson red, adorned with intricate zardozi work and hand-embroidered motifs. The voluminous flared skirt features cascading floral patterns in gold thread, paired with a beautifully crafted choli and a sheer dupatta with scalloped borders. Perfect for the modern bride who cherishes tradition.',
        'fabric': 'Pure Silk with Zardozi',
        'sizes': 'S,M,L,XL,XXL',
        'care': 'Professional dry clean only',
    },
    'Golden Embroidered Bridal Set': {
        'description': 'An opulent bridal set featuring heavy golden embroidery on rich fabric. The lehenga showcases elaborate kundan and sequin work with a matching blouse adorned with intricate thread work. Comes with a luxurious net dupatta embellished with golden tassels and pearl borders.',
        'fabric': 'Raw Silk with Kundan Work',
        'sizes': 'XS,S,M,L,XL,XXL',
        'care': 'Professional dry clean only',
    },
    'Ivory Pearl Bridal Ensemble': {
        'description': 'A graceful ivory bridal ensemble that exudes timeless elegance. Delicately embellished with hand-sewn pearls. The ethereal silhouette combines classic charm with contemporary design, featuring a pearl-studded blouse, flowing lehenga, and a gossamer dupatta with pearl-drop borders.',
        'fabric': 'Organza with Pearl Work',
        'sizes': 'S,M,L,XL',
        'care': 'Professional dry clean only',
    },
    'Midnight Velvet Designer Lehenga': {
        'description': 'A stunning designer lehenga in rich midnight blue velvet. Features contemporary geometric patterns in silver thread with scattered Swarovski crystals. The structured blouse has a modern cut with sheer sleeves, creating a perfect fusion of tradition and avant-garde design.',
        'fabric': 'Italian Velvet',
        'sizes': 'XS,S,M,L,XL',
        'care': 'Dry clean recommended',
    },
    'Rose Gold Sequin Designer Set': {
        'description': 'A show-stopping designer set drenched in rose gold sequins that catch every ray of light. The fluid silhouette moves gracefully, while the intricate sequin pattern creates a mesmerizing ombré effect from blush to deep rose. Perfect for receptions and cocktail evenings.',
        'fabric': 'Georgette with Sequin Work',
        'sizes': 'S,M,L,XL',
        'care': 'Dry clean only',
    },
    'Sapphire Blue Couture Lehenga': {
        'description': 'A couture masterpiece in sapphire blue, handcrafted with intricate resham thread embroidery. The sophisticated colour story pairs with delicate silver thread work creating subtle floral medallions. The layered net dupatta adds an ethereal touch to this striking ensemble.',
        'fabric': 'Banarasi Silk',
        'sizes': 'S,M,L,XL,XXL',
        'care': 'Professional dry clean only',
    },
    'Diwali Collection Floral Lehenga': {
        'description': 'Celebrate the festival of lights in this vibrant floral lehenga from our exclusive Diwali collection. Hand-painted floral motifs in jewel tones dance across the fabric, accented with delicate gota patti work. Light yet lavish — perfect for festive celebrations.',
        'fabric': 'Chanderi Silk',
        'sizes': 'XS,S,M,L,XL',
        'care': 'Gentle dry clean',
    },
    'Navratri Special Chaniya Choli': {
        'description': 'Dance through nine nights of Navratri in this vibrant chaniya choli. Traditional bandhani patterns merge with contemporary embellishments — mirror work that catches the light with every twirl. The flared chaniya gives a perfect spin-worthy silhouette.',
        'fabric': 'Cotton Silk with Mirror Work',
        'sizes': 'S,M,L,XL,XXL',
        'care': 'Hand wash separately, dry clean recommended',
    },
    'Festive Magenta Mirror Work': {
        'description': 'A vivid magenta lehenga that commands attention. Covered in traditional mirror work (abhla bharat) interspersed with colorful thread embroidery. The playful yet elegant design makes it perfect for mehendi ceremonies, sangeet nights, and festive gatherings.',
        'fabric': 'Dupion Silk with Mirrors',
        'sizes': 'S,M,L,XL',
        'care': 'Dry clean only',
    },
    'Champagne Cocktail Lehenga': {
        'description': 'An ultra-chic cocktail lehenga in effervescent champagne gold. The lightweight fabric features subtle shimmer throughout, with a modern shorter-length skirt and a contemporary crop-top style blouse. Ideal for cocktail parties, receptions, and glamorous evenings.',
        'fabric': 'Shimmer Georgette',
        'sizes': 'XS,S,M,L,XL',
        'care': 'Dry clean recommended',
    },
    'Starlight Black Shimmer Set': {
        'description': 'A dramatic party set in midnight black with all-over shimmer that mimics a starlit sky. The structured blouse features a sweetheart neckline, while the A-line lehenga creates a sleek silhouette. Scattered crystal embellishments add just the right amount of sparkle.',
        'fabric': 'Lycra Net with Crystal Work',
        'sizes': 'S,M,L,XL',
        'care': 'Dry clean only',
    },
    'Blush Pink Party Lehenga': {
        'description': 'A dreamy party lehenga in soft blush pink that flatters every skin tone. Delicate threadwork in self-tone creates an elegant texture, while the layered tulle skirt adds romantic volume. The matching dupatta with scalloped edges completes this fairy-tale look.',
        'fabric': 'Tulle with Thread Work',
        'sizes': 'S,M,L,XL,XXL',
        'care': 'Dry clean recommended',
    },
    'Cotton Pastel Summer Lehenga': {
        'description': 'A breezy summer lehenga in soft pastel hues, crafted from premium cotton for all-day comfort. Block-printed floral motifs in muted tones create a relaxed yet refined look. Perfect for day functions, temple visits, and casual celebrations under the sun.',
        'fabric': 'Premium Cotton',
        'sizes': 'XS,S,M,L,XL,XXL',
        'care': 'Machine wash cold, line dry',
    },
    'Linen Everyday Comfort Set': {
        'description': 'Everyday elegance meets supreme comfort in this linen lehenga set. The natural linen fabric breathes beautifully, while subtle hand-block prints add artisanal charm. A minimalist design that transitions effortlessly from casual outings to relaxed gatherings.',
        'fabric': 'Pure Linen',
        'sizes': 'S,M,L,XL',
        'care': 'Machine wash gentle, iron while damp',
    },
    'Indigo Block Print Lehenga': {
        'description': 'A stunning indigo lehenga featuring traditional Rajasthani block printing techniques passed down through generations. Natural indigo dye creates rich, deep tones while hand-stamped patterns tell stories of heritage. Eco-friendly and artisanal — fashion with a conscience.',
        'fabric': 'Handloom Cotton',
        'sizes': 'S,M,L,XL,XXL',
        'care': 'Hand wash separately in cold water',
    },
}

updated = 0
for product in ShowcaseProduct.objects.all():
    details = PRODUCT_DETAILS.get(product.name)
    if details:
        product.description = details['description']
        product.fabric = details['fabric']
        product.available_sizes = details['sizes']
        product.care_instructions = details['care']
        # Force slug regeneration
        product.slug = ''
        product.save()
        updated += 1
        print(f'  ✓ Updated: {product.name}  →  /shop/{product.slug}/')

print(f'\nDone! Updated {updated} products.')
