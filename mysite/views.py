from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.cache import cache_page
import random, json, re, uuid, requests as http_requests, logging
from store.models import (
    HeroSection, FeaturedCollection, ShowcaseProduct, ProductImage,
    CollectionCard, ParallaxSection, ShopBanner, StatItem, ContactInfo, AboutPage,
    PincodeAvailability, Address, Order, OrderItem, ReturnExchange, UserProfile,
)

logger = logging.getLogger(__name__)


# ── Custom error handlers ──────────────────────────────────────
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)


def normalize_phone(raw):
    """Normalize a phone number to +91XXXXXXXXXX format (13 chars, no spaces).
    Returns (normalized, error) — error is None if valid."""
    digits = re.sub(r'[^\d]', '', raw)          # strip everything except digits
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]                      # remove country code
    if digits.startswith('0'):
        digits = digits[1:]                      # remove leading 0
    if len(digits) != 10:
        return None, 'Enter a valid 10-digit phone number.'
    return f'+91{digits}', None


def home(request):
    featured_collections = list(FeaturedCollection.objects.filter(is_active=True))
    collection_cards = list(CollectionCard.objects.filter(is_active=True))

    # Batch-fetch product slugs in one query instead of N+1
    all_names = [fc.name for fc in featured_collections] + [cc.name for cc in collection_cards]
    slug_map = dict(
        ShowcaseProduct.objects.filter(name__in=all_names, is_active=True)
        .values_list('name', 'slug')
    )
    for fc in featured_collections:
        fc.product_slug = slug_map.get(fc.name)
    for cc in collection_cards:
        cc.product_slug = slug_map.get(cc.name)

    context = {
        'hero': HeroSection.objects.filter(is_active=True).first(),
        'featured_collections': featured_collections,
        'showcase_products': ShowcaseProduct.objects.filter(is_active=True).only(
            'name', 'slug', 'image', 'price', 'discount_percent', 'discounted_price', 'category',
        ),
        'collection_cards': collection_cards,
        'parallax': ParallaxSection.objects.filter(is_active=True).first(),
        'stats': StatItem.objects.filter(is_active=True),
        'contact': ContactInfo.objects.filter(is_active=True).first(),
    }
    return render(request, 'home.html', context)


def about(request):
    """About page — founder story and brand mission."""
    context = {
        'about': AboutPage.objects.filter(is_active=True).first(),
        'contact': ContactInfo.objects.filter(is_active=True).first(),
    }
    return render(request, 'about.html', context)


def shop(request):
    """Shop page — all products with category sidebar filtering."""
    category = request.GET.get('category', 'all')
    products = ShowcaseProduct.objects.filter(is_active=True).only(
        'name', 'slug', 'image', 'price', 'discount_percent', 'discounted_price', 'category',
    )
    if category and category != 'all':
        products = products.filter(category=category)
    context = {
        'products': products,
        'categories': ShowcaseProduct.CATEGORY_CHOICES,
        'active_category': category,
        'shop_banner': ShopBanner.objects.filter(is_active=True).first(),
        'contact': ContactInfo.objects.filter(is_active=True).first(),
    }
    return render(request, 'shop.html', context)


def product_detail(request, slug):
    """Individual product detail page."""
    product = get_object_or_404(ShowcaseProduct, slug=slug, is_active=True)
    gallery_images = product.images.only('image', 'alt_text', 'display_order')
    related_products = ShowcaseProduct.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk).only(
        'name', 'slug', 'image', 'price', 'discount_percent', 'discounted_price',
    )[:4]
    context = {
        'product': product,
        'gallery_images': gallery_images,
        'related_products': related_products,
        'contact': ContactInfo.objects.filter(is_active=True).first(),
    }
    return render(request, 'product_detail.html', context)


def search_api(request):
    """AJAX search endpoint — searches featured collections, showcase products, and collection cards."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    results = []

    # Search Featured Collections
    for item in FeaturedCollection.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        is_active=True
    )[:6]:
        results.append({
            'name': item.name,
            'description': item.description,
            'price': item.formatted_price,
            'discounted_price': item.formatted_discounted_price if item.has_discount else '',
            'discount': item.discount_percent if item.has_discount else 0,
            'image': item.image.url if item.image else '',
            'category': 'Featured Collection',
            'section': '#collection',
        })

    # Search Showcase Products
    for item in ShowcaseProduct.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        is_active=True
    )[:6]:
        results.append({
            'name': item.name,
            'price': item.formatted_price,
            'discounted_price': item.formatted_discounted_price if item.has_discount else '',
            'discount': item.discount_percent if item.has_discount else 0,
            'image': item.image.url if item.image else '',
            'category': item.get_category_display(),
            'section': '#showcase',
            'url': f'/shop/{item.slug}/',
        })

    # Search Collection Cards
    for item in CollectionCard.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        is_active=True
    )[:4]:
        results.append({
            'name': item.name,
            'description': item.description,
            'image': item.image.url if item.image else '',
            'category': 'Collection',
            'section': '#collection',
        })

    return JsonResponse({'results': results[:12]})


# ── OTP helpers (cache-backed — works across workers) ──
from django.core.cache import cache as _cache

_OTP_TTL = 300          # OTP valid for 5 minutes
_OTP_RATE_WINDOW = 60   # 1 request per phone per minute

def _otp_key(phone):
    return f'otp:{phone}'

def _otp_rate_key(phone):
    return f'otp_rate:{phone}'

def _store_otp(phone, otp, raw_phone=None):
    _cache.set(_otp_key(phone), otp, _OTP_TTL)
    if raw_phone and raw_phone != phone:
        _cache.set(_otp_key(raw_phone), otp, _OTP_TTL)

def _get_otp(phone, raw_phone=None):
    return _cache.get(_otp_key(phone)) or (
        _cache.get(_otp_key(raw_phone)) if raw_phone else None
    )

def _clear_otp(phone, raw_phone=None):
    _cache.delete(_otp_key(phone))
    if raw_phone:
        _cache.delete(_otp_key(raw_phone))

def _is_rate_limited(phone):
    key = _otp_rate_key(phone)
    if _cache.get(key):
        return True
    _cache.set(key, 1, _OTP_RATE_WINDOW)
    return False


def customer_login(request):
    """Customer login & signup page (not admin)."""
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.POST.get('_ajax') == '1'
        or request.headers.get('Accept', '').startswith('application/json')
    )

    if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
        if is_ajax:
            return JsonResponse({'ok': True, 'redirect': '/'})
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action', 'login')

        if action == 'login':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')

            errors = {}
            if not username:
                errors['username'] = 'Username is required.'
            if not password:
                errors['password'] = 'Password is required.'
            if errors:
                if is_ajax:
                    return JsonResponse({'ok': False, 'errors': errors})
                for msg in errors.values():
                    messages.error(request, msg)
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    if user.is_superuser or user.is_staff:
                        err = 'Please use the admin panel to sign in.'
                        if is_ajax:
                            return JsonResponse({'ok': False, 'errors': {'__all__': err}})
                        messages.error(request, err)
                    else:
                        login(request, user)
                        next_url = request.GET.get('next', '/')
                        if is_ajax:
                            return JsonResponse({
                                'ok': True,
                                'redirect': next_url,
                                'message': f'Welcome back, {user.first_name or user.username}!',
                            })
                        return redirect(next_url)
                else:
                    err = 'Invalid username or password.'
                    if is_ajax:
                        return JsonResponse({'ok': False, 'errors': {'__all__': err}})
                    messages.error(request, err)

        elif action == 'signup':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            confirm = request.POST.get('confirm_password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()

            errors = {}
            if not username:
                errors['username'] = 'Username is required.'
            if not email:
                errors['email'] = 'Email is required.'
            if not password:
                errors['password'] = 'Password is required.'
            elif len(password) < 6:
                errors['password'] = 'Password must be at least 6 characters.'
            if password and confirm and password != confirm:
                errors['confirm_password'] = 'Passwords do not match.'
            if not confirm:
                errors['confirm_password'] = 'Please confirm your password.'
            if username and User.objects.filter(username=username).exists():
                errors['username'] = 'Username already taken.'
            if email and User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered.'

            if errors:
                if is_ajax:
                    return JsonResponse({'ok': False, 'errors': errors})
                for msg in errors.values():
                    messages.error(request, msg)
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                # Create UserProfile so future phone/social logins find this user
                UserProfile.objects.get_or_create(user=user)
                login(request, user)
                welcome = f'Welcome, {first_name or username}! Your account has been created.'
                if is_ajax:
                    return JsonResponse({'ok': True, 'redirect': '/', 'message': welcome})
                messages.success(request, welcome)
                return redirect('home')

        elif action == 'phone_login':
            raw_phone = request.POST.get('phone', '').strip()
            otp = request.POST.get('otp', '').strip()

            errors = {}
            phone = None
            if not raw_phone:
                errors['phone'] = 'Phone number is required.'
            else:
                phone, phone_err = normalize_phone(raw_phone)
                if phone_err:
                    errors['phone'] = phone_err
            if not otp:
                errors['otp'] = 'OTP is required.'

            # Try matching OTP with both raw and normalized phone (in case OTP was stored with raw value)
            stored_otp = _get_otp(phone, raw_phone)
            print(f"[PHONE_LOGIN] raw={raw_phone!r} normalized={phone!r} otp={otp!r} stored={stored_otp!r}")

            if errors:
                if is_ajax:
                    return JsonResponse({'ok': False, 'errors': errors})
                for msg in errors.values():
                    messages.error(request, msg)
            elif stored_otp != otp:
                err = 'Invalid or expired OTP.'
                if is_ajax:
                    return JsonResponse({'ok': False, 'errors': {'otp': err}})
                messages.error(request, err)
            else:
                # OTP valid — find or create user by phone
                _clear_otp(phone, raw_phone)
                # 1. Check UserProfile for existing account with this phone
                profile = UserProfile.objects.filter(phone=phone).select_related('user').first()
                if profile:
                    user = profile.user
                    # Fix username if it's still a legacy format
                    phone_digits = re.sub(r'[^\\d]', '', phone)[-10:]
                    if (user.username.startswith('user_') or user.username.startswith('phone_')) and len(phone_digits) == 10:
                        if not User.objects.filter(username=phone_digits).exclude(pk=user.pk).exists():
                            user.username = phone_digits
                            user.save(update_fields=['username'])
                else:
                    # Extract 10-digit number for username
                    phone_digits = re.sub(r'[^\d]', '', phone)[-10:]
                    # 2. Fall back to legacy phone_ username
                    phone_username = f'phone_{phone}'
                    user = User.objects.filter(username=phone_username).first()
                    if user:
                        # Migrate legacy username to phone digits
                        user.username = phone_digits
                        user.save(update_fields=['username'])
                    if not user:
                        # Check if username with these digits already exists
                        user = User.objects.filter(username=phone_digits).first()
                    if not user:
                        # 3. Create new user with phone number as username
                        user = User.objects.create_user(
                            username=phone_digits,
                        )
                        user.set_unusable_password()
                        user.save()
                    # Save phone to UserProfile for future lookups
                    prof, _ = UserProfile.objects.get_or_create(user=user, defaults={'phone': phone})
                    if not prof.phone:
                        prof.phone = phone
                        prof.save(update_fields=['phone'])
                if user.is_superuser or user.is_staff:
                    err = 'Please use the admin panel to sign in.'
                    if is_ajax:
                        return JsonResponse({'ok': False, 'errors': {'__all__': err}})
                    messages.error(request, err)
                else:
                    login(request, user)
                    print(f"[PHONE_LOGIN] Login SUCCESS for user={user.username}")
                    if is_ajax:
                        return JsonResponse({'ok': True, 'redirect': '/', 'message': 'Signed in successfully!'})
                    return redirect('home')

    # Catch-all: if somehow an AJAX POST fell through without returning
    if request.method == 'POST' and is_ajax:
        return JsonResponse({'ok': False, 'errors': {'__all__': 'Something went wrong. Please try again.'}})

    return render(request, 'login.html')


def customer_logout(request):
    """Logout customer and redirect to home."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ── Profile ──

def profile(request):
    """Customer profile page — edit name & manage addresses."""
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('customer_login')

    user = request.user
    addresses = Address.objects.filter(user=user)
    user_profile, _ = UserProfile.objects.get_or_create(user=user)

    return render(request, 'profile.html', {
        'addresses': addresses,
        'user_phone': user_profile.phone or '',
    })


def profile_update(request):
    """AJAX: update user's first_name / last_name / email."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Not logged in.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    user = request.user
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()

    errors = {}
    if not first_name:
        errors['first_name'] = 'First name is required.'
    if not email:
        errors['email'] = 'Email is required.'
    elif User.objects.filter(email=email).exclude(pk=user.pk).exists():
        errors['email'] = 'This email is already in use.'
    if phone:
        phone, phone_err = normalize_phone(phone)
        if phone_err:
            errors['phone'] = phone_err
        else:
            existing_profile = UserProfile.objects.filter(phone=phone).exclude(user=user).first()
            if existing_profile:
                errors['phone'] = 'This phone number is linked to another account.'
    if errors:
        return JsonResponse({'ok': False, 'errors': errors})

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save()

    # Save phone to UserProfile
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    if phone:
        profile_obj.phone = phone
        profile_obj.save(update_fields=['phone'])

    # Clean up legacy username — set to phone digits
    if user.username.startswith('phone_') or user.username.startswith('user_'):
        if phone:
            digits = re.sub(r'[^\d]', '', phone)[-10:]
            if digits and len(digits) == 10 and not User.objects.filter(username=digits).exclude(pk=user.pk).exists():
                user.username = digits
                user.save(update_fields=['username'])

    return JsonResponse({'ok': True, 'message': 'Profile updated successfully!'})


def address_save(request):
    """AJAX: create or update an address."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Not logged in.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    addr_id = request.POST.get('address_id', '').strip()
    errors = {}
    full_name = request.POST.get('full_name', '').strip()
    phone = request.POST.get('phone', '').strip()
    line1 = request.POST.get('address_line1', '').strip()
    line2 = request.POST.get('address_line2', '').strip()
    city = request.POST.get('city', '').strip()
    state = request.POST.get('state', '').strip()
    pincode = request.POST.get('pincode', '').strip()
    label = request.POST.get('label', 'home').strip()
    is_default = request.POST.get('is_default') == 'on'

    if not full_name:
        errors['full_name'] = 'Full name is required.'
    if not line1:
        errors['address_line1'] = 'Address is required.'
    if not city:
        errors['city'] = 'City is required.'
    if not state:
        errors['state'] = 'State is required.'
    if not pincode or len(pincode) < 5:
        errors['pincode'] = 'Valid pincode is required.'
    if errors:
        return JsonResponse({'ok': False, 'errors': errors})

    if addr_id:
        addr = Address.objects.filter(pk=addr_id, user=request.user).first()
        if not addr:
            return JsonResponse({'ok': False, 'error': 'Address not found.'}, status=404)
    else:
        addr = Address(user=request.user)

    addr.label = label
    addr.full_name = full_name
    addr.phone = phone
    addr.address_line1 = line1
    addr.address_line2 = line2
    addr.city = city
    addr.state = state
    addr.pincode = pincode
    addr.is_default = is_default
    addr.save()

    return JsonResponse({
        'ok': True,
        'message': 'Address saved!',
        'address': {
            'id': addr.pk,
            'label': addr.label,
            'full_name': addr.full_name,
            'phone': addr.phone,
            'address_line1': addr.address_line1,
            'address_line2': addr.address_line2,
            'city': addr.city,
            'state': addr.state,
            'pincode': addr.pincode,
            'is_default': addr.is_default,
        },
    })


def address_delete(request):
    """AJAX: delete an address."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Not logged in.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    addr_id = request.POST.get('address_id', '')
    addr = Address.objects.filter(pk=addr_id, user=request.user).first()
    if not addr:
        return JsonResponse({'ok': False, 'error': 'Address not found.'}, status=404)
    addr.delete()
    return JsonResponse({'ok': True, 'message': 'Address deleted.'})


# ── Order History ──

def order_history(request):
    """Customer order history page."""
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('customer_login')

    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'items__product')
    return render(request, 'order_history.html', {'orders': orders})


# ── Track Order ──

def track_order(request):
    """Track order page — lookup by order number."""
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('customer_login')

    order = None
    error = ''
    order_number = request.GET.get('order_number', '').strip()

    if order_number:
        order = Order.objects.filter(
            order_number__iexact=order_number, user=request.user
        ).prefetch_related('items').first()
        if not order:
            error = 'Order not found. Please check the order number and try again.'

    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'items__product')

    return render(request, 'track_order.html', {
        'order': order,
        'order_number': order_number,
        'error': error,
        'orders': orders,
    })


# ── Returns & Exchanges ──

def returns_exchanges(request):
    """Returns & Exchanges page — view existing requests and create new ones."""
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('customer_login')

    returns = ReturnExchange.objects.filter(user=request.user).select_related('order', 'order_item')
    # Get delivered orders eligible for return
    eligible_orders = Order.objects.filter(
        user=request.user, status='delivered'
    ).prefetch_related('items')

    return render(request, 'returns_exchanges.html', {
        'returns': returns,
        'eligible_orders': eligible_orders,
        'reason_choices': ReturnExchange.REASON_CHOICES,
    })


def return_request_create(request):
    """AJAX: create a return/exchange request."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Not logged in.'}, status=401)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    order_id = request.POST.get('order_id', '').strip()
    item_id = request.POST.get('item_id', '').strip()
    request_type = request.POST.get('request_type', 'return').strip()
    reason = request.POST.get('reason', 'other').strip()
    details = request.POST.get('details', '').strip()

    errors = {}
    if not order_id:
        errors['order_id'] = 'Please select an order.'
    if not reason:
        errors['reason'] = 'Please select a reason.'

    if errors:
        return JsonResponse({'ok': False, 'errors': errors})

    order = Order.objects.filter(pk=order_id, user=request.user, status='delivered').first()
    if not order:
        return JsonResponse({'ok': False, 'error': 'Order not found or not eligible for return.'}, status=404)

    order_item = None
    if item_id:
        order_item = OrderItem.objects.filter(pk=item_id, order=order).first()

    # Check for existing active request
    existing = ReturnExchange.objects.filter(
        order=order, user=request.user
    ).exclude(status__in=['completed', 'rejected']).exists()
    if existing:
        return JsonResponse({'ok': False, 'error': 'An active return/exchange request already exists for this order.'})

    ret = ReturnExchange.objects.create(
        user=request.user,
        order=order,
        order_item=order_item,
        request_type=request_type,
        reason=reason,
        details=details,
    )

    return JsonResponse({
        'ok': True,
        'message': f'{ret.get_request_type_display()} request submitted successfully!',
        'request': {
            'id': ret.pk,
            'type': ret.get_request_type_display(),
            'reason': ret.get_reason_display(),
            'status': ret.get_status_display(),
            'order_number': order.order_number,
            'created_at': ret.created_at.strftime('%b %d, %Y'),
        },
    })


# ── OTP API ──

@csrf_exempt
def send_otp(request):
    """Generate a 6-digit OTP for a phone number.
    Currently returns demo OTP in response.
    TODO: Integrate MSG91 to send real SMS — credentials are in settings.py.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    raw_phone = body.get('phone', '').strip()
    if not raw_phone:
        return JsonResponse({'ok': False, 'error': 'Enter a valid phone number.'})
    phone, phone_err = normalize_phone(raw_phone)
    if phone_err:
        return JsonResponse({'ok': False, 'error': phone_err})

    # Rate-limit: 1 OTP per phone per minute
    if _is_rate_limited(phone):
        return JsonResponse({'ok': False, 'error': 'Please wait before requesting another OTP.'}, status=429)

    otp = str(random.randint(100000, 999999))
    _store_otp(phone, otp, raw_phone)

    # Demo mode: return OTP in response so the front-end can show it.
    # When ready to send real SMS, replace this with MSG91 integration
    # using MSG91_AUTH_KEY and MSG91_TEMPLATE_ID from settings.py.
    return JsonResponse({'ok': True, 'message': f'OTP sent to {phone}', 'demo_otp': otp})


# ── Social OAuth helpers ──

def google_login(request):
    """Redirect to Google OAuth consent screen."""
    from django.conf import settings
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    redirect_uri = request.build_absolute_uri('/account/google/callback/')
    scope = 'openid email profile'
    url = (
        f'https://accounts.google.com/o/oauth2/v2/auth?'
        f'client_id={client_id}&redirect_uri={redirect_uri}'
        f'&response_type=code&scope={scope}&access_type=offline&prompt=consent'
    )
    if not client_id:
        messages.error(request, 'Google login is not configured yet.')
        return redirect('customer_login')
    return redirect(url)


def google_callback(request):
    """Handle Google OAuth callback — exchange code for user info."""
    import urllib.request, urllib.parse
    from django.conf import settings

    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Google login failed.')
        return redirect('customer_login')

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
    redirect_uri = request.build_absolute_uri('/account/google/callback/')

    # Exchange code for tokens
    token_data = urllib.parse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }).encode()
    try:
        token_req = urllib.request.Request('https://oauth2.googleapis.com/token', data=token_data)
        token_resp = urllib.request.urlopen(token_req)
        tokens = json.loads(token_resp.read())
        access_token = tokens['access_token']
    except Exception:
        messages.error(request, 'Failed to authenticate with Google.')
        return redirect('customer_login')

    # Get user info
    try:
        info_req = urllib.request.Request('https://www.googleapis.com/oauth2/v2/userinfo')
        info_req.add_header('Authorization', f'Bearer {access_token}')
        info_resp = urllib.request.urlopen(info_req)
        info = json.loads(info_resp.read())
    except Exception:
        messages.error(request, 'Failed to get Google profile.')
        return redirect('customer_login')

    email = info.get('email', '')
    google_id = info.get('id', '')

    # 1. Try to find by google_id in UserProfile
    user = None
    profile = UserProfile.objects.filter(google_id=google_id).select_related('user').first() if google_id else None
    if profile:
        user = profile.user
    # 2. Try by email
    if not user and email:
        user = User.objects.filter(email=email).first()
    # 3. Create new user if neither found
    if not user:
        username = email.split('@')[0] if email else f'google_{google_id}'
        # Ensure unique username
        base = username
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=info.get('given_name', ''),
            last_name=info.get('family_name', ''),
        )
        user.set_unusable_password()
        user.save()
    # Fill in any missing profile fields from Google data
    changed_fields = []
    if not user.first_name and info.get('given_name'):
        user.first_name = info['given_name']
        changed_fields.append('first_name')
    if not user.last_name and info.get('family_name'):
        user.last_name = info['family_name']
        changed_fields.append('last_name')
    if not user.email and email:
        user.email = email
        changed_fields.append('email')
    if changed_fields:
        user.save(update_fields=changed_fields)
    # Ensure UserProfile exists and has google_id stored
    prof, _ = UserProfile.objects.get_or_create(user=user)
    if google_id and not prof.google_id:
        prof.google_id = google_id
        prof.save(update_fields=['google_id'])
    if user.is_superuser or user.is_staff:
        messages.error(request, 'Admin accounts cannot log in here. Please use the admin panel.')
        return redirect('customer_login')
    login(request, user)
    messages.success(request, f'Welcome, {user.first_name or user.username}!')
    return redirect('home')


def facebook_login(request):
    """Redirect to Facebook OAuth consent screen."""
    from django.conf import settings
    app_id = getattr(settings, 'FACEBOOK_APP_ID', '')
    redirect_uri = request.build_absolute_uri('/account/facebook/callback/')
    url = (
        f'https://www.facebook.com/v18.0/dialog/oauth?'
        f'client_id={app_id}&redirect_uri={redirect_uri}'
        f'&scope=email,public_profile'
    )
    if not app_id:
        messages.error(request, 'Facebook login is not configured yet.')
        return redirect('customer_login')
    return redirect(url)


def facebook_callback(request):
    """Handle Facebook OAuth callback."""
    import urllib.request, urllib.parse
    from django.conf import settings

    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Facebook login failed.')
        return redirect('customer_login')

    app_id = getattr(settings, 'FACEBOOK_APP_ID', '')
    app_secret = getattr(settings, 'FACEBOOK_APP_SECRET', '')
    redirect_uri = request.build_absolute_uri('/account/facebook/callback/')

    # Exchange code for token
    token_url = (
        f'https://graph.facebook.com/v18.0/oauth/access_token?'
        f'client_id={app_id}&redirect_uri={urllib.parse.quote(redirect_uri)}'
        f'&client_secret={app_secret}&code={code}'
    )
    try:
        token_resp = urllib.request.urlopen(token_url)
        tokens = json.loads(token_resp.read())
        access_token = tokens['access_token']
    except Exception:
        messages.error(request, 'Failed to authenticate with Facebook.')
        return redirect('customer_login')

    # Get user info
    try:
        info_url = f'https://graph.facebook.com/me?fields=id,first_name,last_name,email&access_token={access_token}'
        info_resp = urllib.request.urlopen(info_url)
        info = json.loads(info_resp.read())
    except Exception:
        messages.error(request, 'Failed to get Facebook profile.')
        return redirect('customer_login')

    email = info.get('email', '')
    fb_id = info.get('id', '')

    # 1. Try to find by facebook_id in UserProfile
    user = None
    profile = UserProfile.objects.filter(facebook_id=fb_id).select_related('user').first() if fb_id else None
    if profile:
        user = profile.user
    # 2. Try by email
    if not user and email:
        user = User.objects.filter(email=email).first()
    # 3. Try legacy fb_ username
    if not user and fb_id:
        user = User.objects.filter(username=f'fb_{fb_id}').first()
    # 4. Create new user if none found
    if not user:
        username = email.split('@')[0] if email else f'fb_{fb_id}'
        base = username
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=info.get('first_name', ''),
            last_name=info.get('last_name', ''),
        )
        user.set_unusable_password()
        user.save()
    # Fill in any missing profile fields from Facebook data
    changed_fields = []
    if not user.first_name and info.get('first_name'):
        user.first_name = info['first_name']
        changed_fields.append('first_name')
    if not user.last_name and info.get('last_name'):
        user.last_name = info['last_name']
        changed_fields.append('last_name')
    if not user.email and email:
        user.email = email
        changed_fields.append('email')
    if changed_fields:
        user.save(update_fields=changed_fields)
    # Ensure UserProfile exists and has facebook_id stored
    prof, _ = UserProfile.objects.get_or_create(user=user)
    if fb_id and not prof.facebook_id:
        prof.facebook_id = fb_id
        prof.save(update_fields=['facebook_id'])
    if user.is_superuser or user.is_staff:
        messages.error(request, 'Admin accounts cannot log in here. Please use the admin panel.')
        return redirect('customer_login')
    login(request, user)
    messages.success(request, f'Welcome, {user.first_name or user.username}!')
    return redirect('home')


def check_pincode_availability(request):
    """AJAX endpoint to check product availability in a pincode."""
    pincode = request.GET.get('pincode', '').strip()
    product_id = request.GET.get('product_id', '')
    
    # Validate inputs
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return JsonResponse({
            'available': False,
            'message': 'Please enter a valid 6-digit pincode'
        }, status=400)
    
    if not product_id:
        return JsonResponse({
            'available': False,
            'message': 'Product not found'
        }, status=400)
    
    try:
        product = ShowcaseProduct.objects.get(id=product_id)
    except ShowcaseProduct.DoesNotExist:
        return JsonResponse({
            'available': False,
            'message': 'Product not found'
        }, status=404)
    
    # Check availability
    is_available, delivery_days, extra_charge = PincodeAvailability.is_product_available_in_pincode(
        product_id, pincode
    )
    
    if is_available:
        message = f'Delivery in {delivery_days} days'
        if extra_charge > 0:
            message += f' • Shipping: ₹{extra_charge:.0f}'
        
        return JsonResponse({
            'available': True,
            'delivery_days': delivery_days,
            'extra_charge': float(extra_charge),
            'message': message
        })
    else:
        return JsonResponse({
            'available': False,
            'message': f'Currently not available for this area'
        })


# ── Checkout ──

@ensure_csrf_cookie
def checkout(request):
    """Checkout page — renders the multi-step checkout form.
    Cart data lives in localStorage and is passed via JS.
    If logged in, pre-fill saved addresses.
    """
    # Admin/staff should not use the customer checkout
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        messages.info(request, 'You are browsing as an admin. To checkout, please log in with a customer account.')
        return redirect('home')

    addresses = []
    user_phone = ''
    if request.user.is_authenticated:
        addresses = list(
            Address.objects.filter(user=request.user).values(
                'id', 'label', 'full_name', 'phone',
                'address_line1', 'address_line2', 'city', 'state', 'pincode', 'is_default',
            )
        )
        prof = UserProfile.objects.filter(user=request.user).first()
        if prof and prof.phone:
            user_phone = prof.phone

    return render(request, 'checkout.html', {
        'saved_addresses': json.dumps(addresses),
        'user_phone': user_phone,
    })


@csrf_exempt
def checkout_update_profile(request):
    """AJAX: update user profile fields from checkout shipping step.
    Only updates first_name/last_name if currently blank.
    Email and phone are immutable once set.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Login required.'}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)

    user = request.user
    full_name = body.get('full_name', '').strip()
    changed_fields = []

    if full_name:
        parts = full_name.split(None, 1)
        # Always update first_name/last_name from checkout shipping name
        new_first = parts[0]
        new_last = parts[1] if len(parts) > 1 else ''
        if user.first_name != new_first:
            user.first_name = new_first
            changed_fields.append('first_name')
        if user.last_name != new_last:
            user.last_name = new_last
            changed_fields.append('last_name')

    if changed_fields:
        user.save(update_fields=changed_fields)

    return JsonResponse({
        'ok': True,
        'user': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        },
    })


@csrf_exempt
def checkout_login(request):
    """AJAX: login from checkout page without losing cart."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    action = request.POST.get('action', 'login')

    if action == 'login':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        errors = {}
        if not username:
            errors['username'] = 'Username is required.'
        if not password:
            errors['password'] = 'Password is required.'
        if errors:
            return JsonResponse({'ok': False, 'errors': errors})

        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({'ok': False, 'errors': {'__all__': 'Invalid credentials.'}})
        if user.is_superuser or user.is_staff:
            return JsonResponse({'ok': False, 'errors': {'__all__': 'Please use the admin panel.'}})

        login(request, user)
        prof = UserProfile.objects.filter(user=user).first()
        user_phone = prof.phone if prof else ''
        addresses = list(
            Address.objects.filter(user=user).values(
                'id', 'label', 'full_name', 'phone',
                'address_line1', 'address_line2', 'city', 'state', 'pincode', 'is_default',
            )
        )
        return JsonResponse({
            'ok': True,
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'phone': user_phone,
            },
            'addresses': addresses,
        })

    elif action == 'signup':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        errors = {}
        if not username:
            errors['username'] = 'Username is required.'
        if not email:
            errors['email'] = 'Email is required.'
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters.'
        if password and confirm and password != confirm:
            errors['confirm_password'] = 'Passwords do not match.'
        if username and User.objects.filter(username=username).exists():
            errors['username'] = 'Username already taken.'
        if email and User.objects.filter(email=email).exists():
            errors['email'] = 'Email already registered.'
        if errors:
            return JsonResponse({'ok': False, 'errors': errors})

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        # Create UserProfile so future phone/social logins find this user
        UserProfile.objects.get_or_create(user=user)
        login(request, user)
        return JsonResponse({
            'ok': True,
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'phone': '',
            },
            'addresses': [],
        })

    elif action == 'phone_login':
        raw_phone = request.POST.get('phone', '').strip()
        otp = request.POST.get('otp', '').strip()
        errors = {}
        phone = None
        if not raw_phone:
            errors['phone'] = 'Phone number is required.'
        else:
            phone, phone_err = normalize_phone(raw_phone)
            if phone_err:
                errors['phone'] = phone_err
        if not otp:
            errors['otp'] = 'OTP is required.'
        if errors:
            return JsonResponse({'ok': False, 'errors': errors})

        stored_otp = _get_otp(phone, raw_phone)
        if stored_otp != otp:
            return JsonResponse({'ok': False, 'errors': {'otp': 'Invalid or expired OTP.'}})

        # OTP valid — find or create user by phone
        _clear_otp(phone, raw_phone)
        phone_digits = re.sub(r'[^\d]', '', phone)[-10:]
        # 1. Check UserProfile for existing account with this phone
        profile = UserProfile.objects.filter(phone=phone).select_related('user').first()
        if profile:
            user = profile.user
            # Fix username if it's still a legacy format
            if (user.username.startswith('user_') or user.username.startswith('phone_')) and len(phone_digits) == 10:
                if not User.objects.filter(username=phone_digits).exclude(pk=user.pk).exists():
                    user.username = phone_digits
                    user.save(update_fields=['username'])
        else:
            # 2. Fall back to legacy phone_ username
            phone_username = f'phone_{phone}'
            user = User.objects.filter(username=phone_username).first()
            if user:
                user.username = phone_digits
                user.save(update_fields=['username'])
            if not user:
                user = User.objects.filter(username=phone_digits).first()
            if not user:
                # 3. Create new user with phone number as username
                user = User.objects.create_user(
                    username=phone_digits,
                )
                user.set_unusable_password()
                user.save()
            # Save phone to UserProfile for future lookups
            prof, _ = UserProfile.objects.get_or_create(user=user, defaults={'phone': phone})
            if not prof.phone:
                prof.phone = phone
                prof.save(update_fields=['phone'])
        if user.is_superuser or user.is_staff:
            return JsonResponse({'ok': False, 'errors': {'__all__': 'Please use the admin panel.'}})

        login(request, user)
        addresses = list(
            Address.objects.filter(user=user).values(
                'id', 'label', 'full_name', 'phone',
                'address_line1', 'address_line2', 'city', 'state', 'pincode', 'is_default',
            )
        )
        prof_obj = UserProfile.objects.filter(user=user).first()
        user_phone = prof_obj.phone if prof_obj else phone
        return JsonResponse({
            'ok': True,
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'phone': user_phone,
            },
            'addresses': addresses,
        })

    return JsonResponse({'ok': False, 'error': 'Invalid action.'}, status=400)


@csrf_exempt
def place_order(request):
    """AJAX: create an order from cart JSON payload."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Login required.'}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON.'}, status=400)

    items = body.get('items', [])
    shipping = body.get('shipping', {})
    email = body.get('email', '').strip()
    save_address = body.get('save_address', False)

    errors = {}
    if not items:
        errors['items'] = 'Cart is empty.'
    if not shipping.get('full_name'):
        errors['full_name'] = 'Full name is required.'
    if not shipping.get('phone'):
        errors['phone'] = 'Phone number is required.'
    if not shipping.get('address_line1'):
        errors['address_line1'] = 'Address is required.'
    if not shipping.get('city'):
        errors['city'] = 'City is required.'
    if not shipping.get('state'):
        errors['state'] = 'State is required.'
    if not shipping.get('pincode') or len(shipping.get('pincode', '')) < 5:
        errors['pincode'] = 'Valid pincode is required.'
    if not email:
        errors['email'] = 'Email is required.'

    if errors:
        return JsonResponse({'ok': False, 'errors': errors})

    # Fill in any missing user profile fields from checkout data
    user = request.user
    changed_fields = []
    full_name = shipping.get('full_name', '').strip()
    if full_name:
        name_parts = full_name.split(None, 1)
        if not user.first_name:
            user.first_name = name_parts[0]
            changed_fields.append('first_name')
        if not user.last_name and len(name_parts) > 1:
            user.last_name = name_parts[1]
            changed_fields.append('last_name')
    if not user.email and email:
        user.email = email
        changed_fields.append('email')
    if changed_fields:
        user.save(update_fields=changed_fields)

    # Save phone to UserProfile if missing
    checkout_phone = shipping.get('phone', '').strip()
    if checkout_phone:
        prof, _ = UserProfile.objects.get_or_create(user=user)
        if not prof.phone:
            prof.phone = checkout_phone
            prof.save(update_fields=['phone'])

    # Save address for future if requested
    if save_address:
        Address.objects.create(
            user=user,
            label=shipping.get('label', 'home'),
            full_name=shipping['full_name'],
            phone=shipping.get('phone', ''),
            address_line1=shipping['address_line1'],
            address_line2=shipping.get('address_line2', ''),
            city=shipping['city'],
            state=shipping['state'],
            pincode=shipping['pincode'],
            is_default=not Address.objects.filter(user=user).exists(),
        )

    # Calculate totals
    subtotal = 0
    order_items_data = []
    for it in items:
        price = int(it.get('price', 0))
        qty = int(it.get('quantity', 1))
        subtotal += price * qty
        order_items_data.append({
            'product_name': it.get('name', 'Unknown'),
            'price': price,
            'quantity': qty,
            'total': price * qty,
            'image': it.get('image', ''),
        })

    shipping_charge = 0 if subtotal >= 5000 else 199
    total = subtotal + shipping_charge

    order = Order.objects.create(
        user=user,
        status='confirmed',
        payment_status='paid',
        shipping_full_name=shipping['full_name'],
        shipping_phone=shipping.get('phone', ''),
        shipping_address=f"{shipping['address_line1']}, {shipping.get('address_line2', '')}".rstrip(', '),
        shipping_city=shipping['city'],
        shipping_state=shipping['state'],
        shipping_pincode=shipping['pincode'],
        subtotal=subtotal,
        shipping_charge=shipping_charge,
        total=total,
    )

    for oi in order_items_data:
        product = ShowcaseProduct.objects.filter(name=oi['product_name']).first()
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=oi['product_name'],
            price=oi['price'],
            quantity=oi['quantity'],
            total=oi['total'],
        )

    return JsonResponse({
        'ok': True,
        'order_number': order.order_number,
        'total': str(order.total),
        'message': 'Order placed successfully!',
    })