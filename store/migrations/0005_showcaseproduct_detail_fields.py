"""
Custom migration: add slug, description, sizes, fabric, care fields to ShowcaseProduct.
Handles existing data by populating slugs before enforcing uniqueness.
"""
from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    ShowcaseProduct = apps.get_model('store', 'ShowcaseProduct')
    existing_slugs = set()
    for product in ShowcaseProduct.objects.all():
        base_slug = slugify(product.name)
        slug = base_slug
        counter = 1
        while slug in existing_slugs:
            slug = f'{base_slug}-{counter}'
            counter += 1
        existing_slugs.add(slug)
        product.slug = slug
        product.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_showcaseproduct_category'),
    ]

    operations = [
        # Step 1: Add slug field WITHOUT unique constraint (allows default '')
        migrations.AddField(
            model_name='showcaseproduct',
            name='slug',
            field=models.SlugField(max_length=120, blank=True, default=''),
            preserve_default=False,
        ),
        # Step 2: Add other fields
        migrations.AddField(
            model_name='showcaseproduct',
            name='description',
            field=models.TextField(blank=True, default='', help_text='Detailed product description'),
        ),
        migrations.AddField(
            model_name='showcaseproduct',
            name='available_sizes',
            field=models.CharField(blank=True, default='S,M,L,XL', help_text='Comma-separated sizes e.g. S,M,L,XL,XXL', max_length=100),
        ),
        migrations.AddField(
            model_name='showcaseproduct',
            name='fabric',
            field=models.CharField(blank=True, default='', help_text='e.g. Pure Silk, Georgette', max_length=100),
        ),
        migrations.AddField(
            model_name='showcaseproduct',
            name='care_instructions',
            field=models.CharField(blank=True, default='Dry clean only', help_text='Care instructions', max_length=255),
        ),
        # Step 3: Populate slugs for existing products
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        # Step 4: Now make slug unique
        migrations.AlterField(
            model_name='showcaseproduct',
            name='slug',
            field=models.SlugField(max_length=120, unique=True, blank=True, help_text='Auto-generated from name if left blank'),
        ),
    ]
