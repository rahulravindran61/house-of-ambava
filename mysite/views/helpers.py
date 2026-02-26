"""Shared helper utilities used across view modules."""

import re
from django.core.cache import cache as _cache

# ── Phone normalisation ──────────────────────────────────────────

def normalize_phone(raw):
    """Normalize a phone number to +91XXXXXXXXXX format (13 chars, no spaces).
    Returns (normalized, error) — error is None if valid."""
    digits = re.sub(r'[^\d]', '', raw)
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith('0'):
        digits = digits[1:]
    if len(digits) != 10:
        return None, 'Enter a valid 10-digit phone number.'
    return f'+91{digits}', None


# ── OTP helpers (cache-backed — works across workers) ────────────

_OTP_TTL = 300          # OTP valid for 5 minutes
_OTP_RATE_WINDOW = 60   # 1 request per phone per minute


def _otp_key(phone):
    return f'otp:{phone}'


def _otp_rate_key(phone):
    return f'otp_rate:{phone}'


def store_otp(phone, otp, raw_phone=None):
    _cache.set(_otp_key(phone), otp, _OTP_TTL)
    if raw_phone and raw_phone != phone:
        _cache.set(_otp_key(raw_phone), otp, _OTP_TTL)


def get_otp(phone, raw_phone=None):
    return _cache.get(_otp_key(phone)) or (
        _cache.get(_otp_key(raw_phone)) if raw_phone else None
    )


def clear_otp(phone, raw_phone=None):
    _cache.delete(_otp_key(phone))
    if raw_phone:
        _cache.delete(_otp_key(raw_phone))


def is_rate_limited(phone):
    key = _otp_rate_key(phone)
    if _cache.get(key):
        return True
    _cache.set(key, 1, _OTP_RATE_WINDOW)
    return False
