"""
Development settings — DEBUG=True, console email, relaxed security.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

X_FRAME_OPTIONS = 'SAMEORIGIN'

# Console email for local dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
