"""
URL configuration for mysite project.
https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from .views import home, about

from store.urls import (
    shop_urlpatterns,
    api_urlpatterns,
    account_urlpatterns,
    checkout_urlpatterns,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Top-level pages
    path('', home, name='home'),
    path('about/', about, name='about'),

    # Grouped route sets from store app
    path('shop/', include(shop_urlpatterns)),
    path('api/', include(api_urlpatterns)),
    path('account/', include(account_urlpatterns)),
    path('checkout/', include(checkout_urlpatterns)),
]

# Serve media in development; WhiteNoise handles static automatically
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers (used when DEBUG=False)
handler404 = 'mysite.views.custom_404'
handler500 = 'mysite.views.custom_500'
