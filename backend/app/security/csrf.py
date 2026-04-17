import hashlib
import hmac
import time

from app.config import settings

_MAX_AGE_SEC = 900


def create_csrf_token() -> str:
    ts = str(int(time.time()))
    sig = hmac.new(
        settings.secret_key.encode(),
        ts.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{ts}.{sig}"


def validate_csrf_token(token: str) -> bool:
    if not token or "." not in token:
        return False
    ts_str, sig = token.split(".", 1)
    try:
        ts = int(ts_str)
    except ValueError:
        return False
    if abs(int(time.time()) - ts) > _MAX_AGE_SEC:
        return False
    expected = hmac.new(
        settings.secret_key.encode(),
        ts_str.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig)
