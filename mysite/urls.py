"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('shop/<slug:slug>/', views.product_detail, name='product_detail'),
    path('about/', views.about, name='about'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/check-pincode/', views.check_pincode_availability, name='check_pincode_availability'),
    path('account/login/', views.customer_login, name='customer_login'),
    path('account/logout/', views.customer_logout, name='customer_logout'),
    path('account/profile/', views.profile, name='profile'),
    path('account/profile/update/', views.profile_update, name='profile_update'),
    path('account/address/save/', views.address_save, name='address_save'),
    path('account/address/delete/', views.address_delete, name='address_delete'),
    path('account/orders/', views.order_history, name='order_history'),
    path('account/track-order/', views.track_order, name='track_order'),
    path('account/returns/', views.returns_exchanges, name='returns_exchanges'),
    path('account/returns/create/', views.return_request_create, name='return_request_create'),
    path('account/send-otp/', views.send_otp, name='send_otp'),
    path('account/google/', views.google_login, name='google_login'),
    path('account/google/callback/', views.google_callback, name='google_callback'),
    path('account/facebook/', views.facebook_login, name='facebook_login'),
    path('account/facebook/callback/', views.facebook_callback, name='facebook_callback'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/login/', views.checkout_login, name='checkout_login'),
    path('checkout/update-profile/', views.checkout_update_profile, name='checkout_update_profile'),
    path('checkout/place-order/', views.place_order, name='place_order'),
]

# Serve media in development; WhiteNoise handles static automatically
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers (used when DEBUG=False)
handler404 = 'mysite.views.custom_404'
handler500 = 'mysite.views.custom_500'
