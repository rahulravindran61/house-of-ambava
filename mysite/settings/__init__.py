"""
Settings package — defaults to dev for local development.
Uses prod when DJANGO_DEBUG is false.
"""

import os

_debug = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

if _debug:
    from .dev import *   # noqa: F401,F403
else:
    from .prod import *  # noqa: F401,F403
