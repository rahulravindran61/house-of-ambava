import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from store.models import ShowcaseProduct

# Remaining 12 images to create new products
new_products = [
    {
        "name": "Anarkali Classic Collection",
        "category": "bridal",
        "price": 12500,
        "image": "showcase/Anarkali_Collection.jpeg",
        "description": "Traditional Anarkali with intricate embroidery",
    },
    {
        "name": "Coral Daya Zardozi Lehenga",
        "category": "bridal",
        "price": 13000,
        "image": "showcase/Coral_Daya_Zardozi_Lehenga_Set.jpg",
        "description": "Coral lehenga with beautiful Zardozi work",
    },
    {
        "name": "Fuchsia Orange Daya Zardozi",
        "category": "designer",
        "price": 11800,
        "image": "showcase/Fuschia_Orange_Daya_Zardozi_Lehenga_Set.jpg",
        "description": "Designer piece with stunning color blend",
    },
    {
        "name": "Fuchsia Orange Jasveera Lehenga",
        "category": "designer",
        "price": 12200,
        "image": "showcase/Fuschia_Orange_Jasveera_Lehenga_Set.jpg",
        "description": "Vibrant Jasveera work in fuchsia and orange",
    },
    {
        "name": "Off-White Red Daya Zardozi",
        "category": "bridal",
        "price": 13500,
        "image": "showcase/Off_White_Red_Daya_Zardozi_Lehenga_Set.jpg",
        "description": "Elegant off-white with red accent Zardozi",
    },
    {
        "name": "Off-White Red Parampara Ari",
        "category": "festive",
        "price": 11500,
        "image": "showcase/Off_White_Red_Parampara_Ari_Lehenga_Set.jpg",
        "description": "Traditional Ari embroidery work",
    },
    {
        "name": "Purple Kanika Lehenga",
        "category": "party",
        "price": 10800,
        "image": "showcase/Purple_Kanika_Lehenga_Set.jpg",
        "description": "Royal purple with intricate Kanika design",
    },
    {
        "name": "Red Jamdani Lehenga",
        "category": "festival",
        "price": 12000,
        "image": "showcase/Red_Jamdani_Lehenga_Set.jpg",
        "description": "Rich red with traditional Jamdani weaving",
    },
    {
        "name": "Red Multi Jasveera",
        "category": "bridal",
        "price": 13200,
        "image": "showcase/Red_Multi_Jasveera_Lehenga_Set.jpg",
        "description": "Red lehenga with multi-color Jasveera work",
    },
    {
        "name": "Red Sana Lehenga",
        "category": "festive",
        "price": 11200,
        "image": "showcase/Red_Sana_Lehenga_Set.jpg",
        "description": "Deep red Sana lehenga for festive occasions",
    },
    {
        "name": "Silk Sarees Collection",
        "category": "casual",
        "price": 9500,
        "image": "showcase/Silk_Sarees.jpeg",
        "description": "Premium silk sarees for elegant occasions",
    },
]

print("Creating 11 new products with remaining images...\n")

for idx, product_data in enumerate(new_products, start=16):
    try:
        # Check if product already exists
        if ShowcaseProduct.objects.filter(name=product_data["name"]).exists():
            print(f"✓ Product already exists: {product_data['name']}")
            continue
        
        product = ShowcaseProduct.objects.create(
            name=product_data["name"],
            category=product_data["category"],
            price=product_data["price"],
            image=product_data["image"],
            description=product_data["description"],
            display_order=idx,
            is_active=True,
        )
        print(f"✓ Created Product {idx}: {product.name}")
        print(f"  Image: {product_data['image']}")
        print(f"  Price: ₹{product_data['price']}\n")
    except Exception as e:
        print(f"✗ Error creating product: {e}\n")

print("✓ All 11 new products created successfully!")
print(f"\nTotal products now: {ShowcaseProduct.objects.count()}")
