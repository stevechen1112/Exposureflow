"""Security and reliability unit tests."""

import uuid

import pytest

from exposureflow_api.common.crypto import decrypt_secret, encrypt_secret
from exposureflow_api.integrations.error_sanitizer import sanitize_sync_error
from exposureflow_api.reliability.circuit_breaker import (
    assert_provider_available,
    record_provider_failure,
    record_provider_success,
)
from exposureflow_api.reliability.rate_limit import check_rate_limit
from exposureflow_api.common.errors import APIError


def test_encrypt_decrypt_roundtrip() -> None:
    plaintext = "super-secret-gsc-token"
    ciphertext = encrypt_secret(plaintext)
    assert plaintext not in ciphertext
    assert decrypt_secret(ciphertext) == plaintext


def test_sanitize_sync_error_redacts_tokens() -> None:
    raw = "Failed: https://api.example.com?api_key=abc123&access_token=xyz"
    sanitized = sanitize_sync_error(raw)
    assert "abc123" not in sanitized
    assert "xyz" not in sanitized
    assert "***" in sanitized


def test_rate_limit_blocks_burst() -> None:
    key = f"test-ip-burst-{uuid.uuid4()}"
    for _ in range(5):
        check_rate_limit(key=key, limit=5, window_seconds=60)
    with pytest.raises(APIError) as exc:
        check_rate_limit(key=key, limit=5, window_seconds=60)
    assert exc.value.status_code == 429


def test_circuit_breaker_opens_after_failures() -> None:
    provider = "test-provider-circuit"
    record_provider_success(provider)
    for _ in range(5):
        record_provider_failure(provider)
    with pytest.raises(APIError) as exc:
        assert_provider_available(provider)
    assert exc.value.status_code == 503
