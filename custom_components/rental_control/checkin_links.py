# SPDX-FileCopyrightText: 2025 LekkeSlaap Integration Contributors
# SPDX-License-Identifier: Apache-2.0

"""Generate HMAC-signed, expiring check-in links for guests.

This module ports the link generation logic from the Cloudflare Worker
(self-checkin-worker/generate_link.js) to Python for use in Home Assistant.
"""

import hmac
import hashlib
import time
from typing import Optional


def normalize_path(path: str) -> str:
    """Normalize path by removing trailing slash (except for root).

    Args:
        path: URL path to normalize

    Returns:
        Normalized path string

    """
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1 and path.endswith("/"):
        return path[:-1]
    return path


def ensure_trailing_slash(path: str) -> str:
    """Ensure path has a trailing slash (except for root).

    Args:
        path: URL path to process

    Returns:
        Path with trailing slash

    """
    if path == "/":
        return path
    return path if path.endswith("/") else f"{path}/"


def generate_checkin_link(
    base_url: str,
    path: str,
    secret: str,
    expires_in_seconds: int = 86400,
) -> Optional[str]:
    """Generate a signed, expiring check-in link for guests.

    Creates an HMAC-SHA256 signed URL that expires after the specified duration.
    The signature is computed over the normalized path and expiry timestamp.

    Args:
        base_url: Base URL (e.g., "https://karooandko.co.za")
        path: Check-in page path (e.g., "/checkin/cottage")
        secret: HMAC signing secret (must match Cloudflare Worker secret)
        expires_in_seconds: Link validity duration in seconds (default: 86400 = 24 hours)

    Returns:
        Signed URL string, or None if inputs are invalid

    Raises:
        ValueError: If expires_in_seconds is not a positive number

    """
    if not isinstance(expires_in_seconds, int) or expires_in_seconds <= 0:
        raise ValueError("expires_in_seconds must be a positive integer")

    if not base_url or not path or not secret:
        return None

    # Normalize path for signature computation
    norm_path = normalize_path(path)

    # Calculate expiry timestamp
    expiry = int(time.time()) + expires_in_seconds

    # Create HMAC signature: HMAC-SHA256("{path}|{expiry}", secret)
    message = f"{norm_path}|{expiry}"
    sig = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # Build final URL with trailing slash
    out_path = ensure_trailing_slash(norm_path)
    return f"{base_url.rstrip('/')}{out_path}?t={expiry}&sig={sig}"
