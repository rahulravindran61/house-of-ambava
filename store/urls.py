"""store app — URL patterns, included from mysite.urls."""

from django.urls import path
from mysite.views import (
    # Pages
    shop, product_detail, about,
    # API
    search_api, check_pincode_availability,
    # Auth
    customer_login, customer_logout, send_otp,
    google_login, google_callback,
    facebook_login, facebook_callback,
    # Account
    profile, profile_update,
    address_save, address_delete,
    order_history, track_order,
    returns_exchanges, return_request_create,
    # Checkout
    checkout, checkout_update_profile, checkout_login, place_order,
)

# ── Shop / product pages ──
shop_urlpatterns = [
    path('', shop, name='shop'),
    path('<slug:slug>/', product_detail, name='product_detail'),
]

# ── API endpoints ──
api_urlpatterns = [
    path('search/', search_api, name='search_api'),
    path('check-pincode/', check_pincode_availability, name='check_pincode_availability'),
]

# ── Account / auth ──
account_urlpatterns = [
    path('login/', customer_login, name='customer_login'),
    path('logout/', customer_logout, name='customer_logout'),
    path('profile/', profile, name='profile'),
    path('profile/update/', profile_update, name='profile_update'),
    path('address/save/', address_save, name='address_save'),
    path('address/delete/', address_delete, name='address_delete'),
    path('orders/', order_history, name='order_history'),
    path('track-order/', track_order, name='track_order'),
    path('returns/', returns_exchanges, name='returns_exchanges'),
    path('returns/create/', return_request_create, name='return_request_create'),
    path('send-otp/', send_otp, name='send_otp'),
    path('google/', google_login, name='google_login'),
    path('google/callback/', google_callback, name='google_callback'),
    path('facebook/', facebook_login, name='facebook_login'),
    path('facebook/callback/', facebook_callback, name='facebook_callback'),
]

# ── Checkout ──
checkout_urlpatterns = [
    path('', checkout, name='checkout'),
    path('login/', checkout_login, name='checkout_login'),
    path('update-profile/', checkout_update_profile, name='checkout_update_profile'),
    path('place-order/', place_order, name='place_order'),
]
