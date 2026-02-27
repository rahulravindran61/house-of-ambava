"""
mysite.views — re-exports all view functions so existing URL
config (``from . import views; views.home``) keeps working.
"""

from .errors import custom_404, custom_500                          # noqa: F401
from .pages import home, about, shop, product_detail                # noqa: F401
from .api import search_api, check_pincode_availability, send_otp   # noqa: F401
from .auth import (                                                 # noqa: F401
    customer_login, customer_logout,
    google_login, google_callback,
    facebook_login, facebook_callback,
)
from .account import (                                              # noqa: F401
    profile, profile_update,
    address_save, address_delete,
    order_history, track_order,
    returns_exchanges, return_request_create,
)
from .checkout import (                                             # noqa: F401
    checkout, checkout_update_profile,
    checkout_login, place_order,
    verify_razorpay_payment, razorpay_payment_failed,
)
