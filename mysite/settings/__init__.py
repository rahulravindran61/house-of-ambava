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
