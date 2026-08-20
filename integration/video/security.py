"""RTSP URL sanitization for the SIH1349 video runtime."""
from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse


def sanitize_rtsp_url(url: str) -> str:
    """Sanitize an RTSP URL by replacing credentials with placeholders.

    Example:
        Input:  rtsp://admin:secret123@192.168.1.10/stream
        Output: rtsp://***:***@192.168.1.10/stream

    Never logs or exposes the original username/password.
    """
    try:
        parsed = urlparse(url)
        if parsed.username or parsed.password:
            sanitized = parsed._replace(
                netloc=f"***:***@{parsed.hostname}"
                + (f":{parsed.port}" if parsed.port else "")
            )
            return urlunparse(sanitized)
        return url
    except Exception:
        # If URL parsing fails, mask everything after rtsp://
        return re.sub(r"(rtsp://)[^@]+@", r"\1***:***@", url)


def has_credentials(url: str) -> bool:
    """Check if an RTSP URL contains embedded credentials."""
    try:
        parsed = urlparse(url)
        return bool(parsed.username or parsed.password)
    except Exception:
        return False
