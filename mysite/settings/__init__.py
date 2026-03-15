"""
Settings package — defaults to dev for local development.
Override with DJANGO_SETTINGS_MODULE env var for production.
"""

import os

_env = os.environ.get('DJANGO_SETTINGS_MODULE', '')

# If no explicit module set, auto-select based on DJANGO_DEBUG
if not _env or _env == 'mysite.settings':
    _debug = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')
    if _debug:
        from .dev import *   # noqa: F401,F403
    else:
        from .prod import *  # noqa: F401,F403
elif not _env.startswith('mysite.settings.'):
    # Some platforms (e.g. Vercel) generate wrapper settings modules like
    # `_vercel_collectstatic_settings.py` that do `from mysite.settings import *`.
    # In this path, this package must still export a full settings object.
    _debug = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')
    if _debug:
        from .dev import *   # noqa: F401,F403
    else:
        from .prod import *  # noqa: F401,F403

# Vercel and other build tools may import this package via wrapper settings
# modules before submodule globals are populated. Guarding with globals()
# avoids NameError while still ensuring collectstatic command availability.
if 'INSTALLED_APPS' in globals() and 'django.contrib.staticfiles' not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS = [*INSTALLED_APPS, 'django.contrib.staticfiles']  # noqa: F405
