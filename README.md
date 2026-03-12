# House of Ambava

A luxury lehenga e-commerce website built with Django.

## Features

- **Product Catalog** — 58+ luxury lehenga products with categories, filtering, and search
- **Product Detail** — Image gallery, size guide, pincode availability checker
- **Shopping Cart** — Drawer-based cart with localStorage persistence
- **Multi-step Checkout** — Account → Shipping → Review flow
- **Authentication** — Username/password login, Phone OTP login, signup
- **Customer Portal** — Profile management, addresses, order history, order tracking, returns & exchanges
- **Admin Panel** — Django admin for managing products, orders, hero section, collections, and more
- **Dark Mode** — System-aware theme toggle with smooth transitions
- **Responsive Design** — Fully mobile-optimized with hamburger menu, collapsible sections
- **Smooth Animations** — Page transitions, scroll effects, parallax sections

## Tech Stack

- **Backend:** Django 5.x, Python 3.10+
- **Database:** SQLite (development)
- **Frontend:** Vanilla HTML/CSS/JS, Font Awesome icons
- **Smooth Scroll:** Lenis

## Setup (safe, non-breaking)

```bash
# Clone the repo
git clone https://github.com/rahulravindran61/house-of-ambava.git
cd house-of-ambava

# Create an isolated virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Install all pinned app dependencies
python -m pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser

# Optional: populate products
python manage.py populate_shop

# Run the server
python manage.py runserver
```

### If dependency install fails in restricted/proxy environments

Use the app venv and proxy-aware variables rather than global/system Python:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If your environment blocks outbound package downloads, configure an internal package index and retry:

```bash
source .venv/bin/activate
python -m pip install --index-url <your-internal-pypi-url> -r requirements.txt
```

## Project Structure

```
├── mysite/              # Django project settings & main views
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── static/          # CSS, JS, images
├── store/               # Django app — models, admin, migrations
├── templates/           # HTML templates
├── media/               # User-uploaded content (not tracked)
└── manage.py
```
