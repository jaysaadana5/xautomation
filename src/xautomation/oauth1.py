from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import quote, urlsplit


def _escape(value: str) -> str:
    return quote(value, safe="~-._")


def authorization_header(
    method: str,
    url: str,
    consumer_key: str,
    consumer_secret: str,
    token: str,
    token_secret: str,
    *,
    nonce: str | None = None,
    timestamp: str | None = None,
) -> str:
    """Create an OAuth 1.0a HMAC-SHA1 Authorization header."""
    oauth = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp or str(int(time.time())),
        "oauth_token": token,
        "oauth_version": "1.0",
    }
    parts = urlsplit(url)
    base_url = f"{parts.scheme}://{parts.netloc}{parts.path}"
    normalized = "&".join(
        f"{_escape(key)}={_escape(value)}" for key, value in sorted(oauth.items())
    )
    signature_base = "&".join(
        (_escape(method.upper()), _escape(base_url), _escape(normalized))
    )
    signing_key = f"{_escape(consumer_secret)}&{_escape(token_secret)}"
    digest = hmac.new(
        signing_key.encode(), signature_base.encode(), hashlib.sha1
    ).digest()
    oauth["oauth_signature"] = base64.b64encode(digest).decode()
    values = ", ".join(
        f'{_escape(key)}="{_escape(value)}"' for key, value in sorted(oauth.items())
    )
    return f"OAuth {values}"

