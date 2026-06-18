"""Tests for URL safety validation."""

import pytest

from exposureflow_api.common.errors import APIError
from exposureflow_api.common.url_safety import validate_safe_http_url


def test_validate_safe_http_url_accepts_https() -> None:
    assert validate_safe_http_url("https://example.com/page").startswith("https://")


def test_validate_safe_http_url_rejects_localhost() -> None:
    with pytest.raises(APIError) as exc:
        validate_safe_http_url("http://localhost/admin")
    assert exc.value.status_code == 400


def test_validate_safe_http_url_rejects_file_scheme() -> None:
    with pytest.raises(APIError):
        validate_safe_http_url("file:///etc/passwd")


def test_assert_url_host_allowed_matches_managed_site() -> None:
    from exposureflow_api.common.url_safety import assert_url_host_allowed

    url = assert_url_host_allowed(
        "https://ezfix.com.tw/blog/post",
        "https://ezfix.com.tw",
    )
    assert url.startswith("https://ezfix.com.tw")


def test_assert_url_host_allowed_rejects_foreign_host() -> None:
    from exposureflow_api.common.url_safety import assert_url_host_allowed

    with pytest.raises(APIError) as exc:
        assert_url_host_allowed("https://evil.example.com/blog", "https://ezfix.com.tw")
    assert exc.value.status_code == 400
