"""Sitemaps for SEO — tells search engines about all pages."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from store.models import ShowcaseProduct


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['home', 'about', 'shop', 'customer_login',
                'privacy_policy', 'terms_conditions',
                'refund_policy', 'shipping_policy']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return ShowcaseProduct.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/shop/{obj.slug}/'
