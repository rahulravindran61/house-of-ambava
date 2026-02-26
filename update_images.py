import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct

# Intelligent mapping based on color/style matching
image_mapping = {
    1: "showcase/Red_Girija_Lehenga_Set.jpg",  # Royal Crimson Bridal
    2: "showcase/Ochre_Yellow_Gold_Brocade_Jamawar_Lehenga_Set.jpg",  # Golden Embroidered
    3: "showcase/Off_White_Daneliya_Lehenga_Set.jpg",  # Ivory Pearl Bridal
    4: "showcase/Black_Multi_Pushvapan_Ensemble.jpg",  # Midnight Velvet Designer
    5: "showcase/Coral_Pink_Keya_Lehenga_Set.jpg",  # Rose Gold Sequin Designer
    6: "showcase/Royal_Blue_Antique_Floral_Lehenga.jpg",  # Sapphire Blue Couture
    7: "showcase/Fire_Yellow_Peach_Kesari_Lehenga_Set.jpg",  # Diwali Collection Floral
    8: "showcase/Yellow_Purple_Morina_Lehenga.jpeg",  # Navratri Special Chaniya Choli
    9: "showcase/Fuschia_Kulah_Lehenga_Set.jpg",  # Festive Magenta Mirror Work
    10: "showcase/Ecru_Chanda_Lehenga_Set.jpg",  # Champagne Cocktail
    11: "showcase/Black_Golden_Yellow_Roshafi_Lehenga_Set.jpg",  # Starlight Black Shimmer
    12: "showcase/Coral_Orange_Sana_Lehenga_Set.jpg",  # Blush Pink Party
    13: "showcase/Grey_Off_White_Vedam_Lehenga_Set.jpg",  # Cotton Pastel Summer
    14: "showcase/Off_White_Multi_Rajwadi_Lehenga_Set.jpg",  # Linen Everyday Comfort
    15: "showcase/Jade_Sea_Green_Tania_Zardozi_Lehenga_Set.jpg",  # Indigo Block Print
}

print("Updating product images...\n")

for product_id, image_path in image_mapping.items():
    try:
        product = ShowcaseProduct.objects.get(id=product_id)
        old_image = product.image.name
        product.image = image_path
        product.save()
        print(f"✓ Product {product_id}: {product.name}")
        print(f"  Old: {old_image}")
        print(f"  New: {image_path}\n")
    except ShowcaseProduct.DoesNotExist:
        print(f"✗ Product {product_id} not found\n")

print("✓ All products updated successfully!")
