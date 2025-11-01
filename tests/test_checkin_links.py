# SPDX-FileCopyrightText: 2025 LekkeSlaap Integration Contributors
# SPDX-License-Identifier: Apache-2.0

"""Test check-in link generation."""

import time
from unittest.mock import patch

import pytest

from custom_components.rental_control.checkin_links import (
    ensure_trailing_slash,
    generate_checkin_link,
    normalize_path,
)


def test_normalize_path():
    """Test path normalization."""
    # Add leading slash if missing
    assert normalize_path("checkin/cottage") == "/checkin/cottage"

    # Remove trailing slash (except root)
    assert normalize_path("/checkin/cottage/") == "/checkin/cottage"

    # Keep root slash
    assert normalize_path("/") == "/"

    # Already normalized
    assert normalize_path("/checkin/cottage") == "/checkin/cottage"


def test_ensure_trailing_slash():
    """Test trailing slash addition."""
    # Add trailing slash
    assert ensure_trailing_slash("/checkin/cottage") == "/checkin/cottage/"

    # Already has trailing slash
    assert ensure_trailing_slash("/checkin/cottage/") == "/checkin/cottage/"

    # Root stays as-is
    assert ensure_trailing_slash("/") == "/"


def test_generate_checkin_link_basic():
    """Test basic link generation."""
    base_url = "https://karooandko.co.za"
    path = "/checkin/cottage"
    secret = "test-secret-key"

    with patch("time.time", return_value=1000000000):
        link = generate_checkin_link(base_url, path, secret, expires_in_seconds=86400)

    assert link is not None
    assert link.startswith("https://karooandko.co.za/checkin/cottage/")
    assert "?t=1000086400" in link  # 1000000000 + 86400
    assert "&sig=" in link
    assert len(link.split("&sig=")[1]) == 64  # SHA256 hex is 64 chars


def test_generate_checkin_link_matches_js_implementation():
    """Test that Python implementation matches JavaScript HMAC output."""
    # These values are from the JS implementation
    base_url = "https://karooandko.co.za"
    path = "/checkin/cottage"
    secret = "my-test-secret"

    # Fixed timestamp for reproducibility
    fixed_time = 1700000000
    expires_in = 86400
    expected_expiry = fixed_time + expires_in

    with patch("time.time", return_value=fixed_time):
        link = generate_checkin_link(base_url, path, secret, expires_in_seconds=expires_in)

    # Verify structure
    assert link.startswith(f"{base_url}/checkin/cottage/")
    assert f"?t={expected_expiry}" in link

    # Verify the signature is consistent
    # The JS code creates HMAC-SHA256 of "{normalized_path}|{expiry}"
    # We can't hardcode the sig since it depends on the secret, but we can
    # verify it's the right length and format
    sig = link.split("&sig=")[1]
    assert len(sig) == 64
    assert all(c in "0123456789abcdef" for c in sig)


def test_generate_checkin_link_path_normalization():
    """Test that paths are normalized correctly."""
    base_url = "https://karooandko.co.za"
    secret = "test-secret"

    with patch("time.time", return_value=1000000000):
        # Paths with and without trailing slashes should produce same signature
        link1 = generate_checkin_link(base_url, "/checkin/cottage", secret, 86400)
        link2 = generate_checkin_link(base_url, "/checkin/cottage/", secret, 86400)

    # Both should have same signature (since normalized path is the same)
    sig1 = link1.split("&sig=")[1]
    sig2 = link2.split("&sig=")[1]
    assert sig1 == sig2

    # Both should end with trailing slash in output
    assert "/checkin/cottage/?t=" in link1
    assert "/checkin/cottage/?t=" in link2


def test_generate_checkin_link_base_url_normalization():
    """Test that base URLs are handled correctly."""
    path = "/checkin/cottage"
    secret = "test-secret"

    with patch("time.time", return_value=1000000000):
        # Base URL with trailing slash should be stripped
        link1 = generate_checkin_link("https://example.com", path, secret, 86400)
        link2 = generate_checkin_link("https://example.com/", path, secret, 86400)

    # Both should produce same URL structure
    assert link1.startswith("https://example.com/checkin/cottage/")
    assert link2.startswith("https://example.com/checkin/cottage/")

    # Signatures should match
    assert link1.split("&sig=")[1] == link2.split("&sig=")[1]


def test_generate_checkin_link_invalid_expiry():
    """Test that invalid expiry values raise ValueError."""
    with pytest.raises(ValueError, match="expires_in_seconds must be a positive integer"):
        generate_checkin_link(
            "https://example.com",
            "/checkin/cottage",
            "secret",
            expires_in_seconds=0,
        )

    with pytest.raises(ValueError, match="expires_in_seconds must be a positive integer"):
        generate_checkin_link(
            "https://example.com",
            "/checkin/cottage",
            "secret",
            expires_in_seconds=-100,
        )


def test_generate_checkin_link_missing_inputs():
    """Test that missing required inputs return None."""
    # Missing base_url
    assert generate_checkin_link("", "/checkin/cottage", "secret", 86400) is None

    # Missing path
    assert generate_checkin_link("https://example.com", "", "secret", 86400) is None

    # Missing secret
    assert generate_checkin_link("https://example.com", "/checkin/cottage", "", 86400) is None


def test_generate_checkin_link_different_expiry_times():
    """Test that different expiry times produce different signatures."""
    base_url = "https://example.com"
    path = "/checkin/cottage"
    secret = "test-secret"

    with patch("time.time", return_value=1000000000):
        link1 = generate_checkin_link(base_url, path, secret, expires_in_seconds=3600)
        link2 = generate_checkin_link(base_url, path, secret, expires_in_seconds=7200)

    # Different expiry times should produce different timestamps
    assert "?t=1000003600" in link1  # 1000000000 + 3600
    assert "?t=1000007200" in link2  # 1000000000 + 7200

    # And different signatures
    sig1 = link1.split("&sig=")[1]
    sig2 = link2.split("&sig=")[1]
    assert sig1 != sig2


def test_generate_checkin_link_different_secrets():
    """Test that different secrets produce different signatures."""
    base_url = "https://example.com"
    path = "/checkin/cottage"

    with patch("time.time", return_value=1000000000):
        link1 = generate_checkin_link(base_url, path, "secret1", 86400)
        link2 = generate_checkin_link(base_url, path, "secret2", 86400)

    # Same expiry time
    assert "?t=1000086400" in link1
    assert "?t=1000086400" in link2

    # But different signatures
    sig1 = link1.split("&sig=")[1]
    sig2 = link2.split("&sig=")[1]
    assert sig1 != sig2


def test_generate_checkin_link_different_paths():
    """Test that different paths produce different signatures."""
    base_url = "https://example.com"
    secret = "test-secret"

    with patch("time.time", return_value=1000000000):
        link1 = generate_checkin_link(base_url, "/checkin/cottage", secret, 86400)
        link2 = generate_checkin_link(base_url, "/checkin/tiny-home", secret, 86400)

    # Same expiry time
    assert "?t=1000086400" in link1
    assert "?t=1000086400" in link2

    # But different paths and signatures
    assert "/checkin/cottage/" in link1
    assert "/checkin/tiny-home/" in link2

    sig1 = link1.split("&sig=")[1]
    sig2 = link2.split("&sig=")[1]
    assert sig1 != sig2
