import json

import pytest

from exposureflow_api.common.errors import APIError
from exposureflow_api.integrations.credential_validation import validate_integration_payload


def test_validate_contentflow_payload_accepts_public_site() -> None:
    payload = json.dumps(
        {
            "site_url": "https://ezfix.com.tw",
            "secret": "test-secret",
        }
    )
    validate_integration_payload("contentflow", payload)


def test_validate_contentflow_payload_rejects_localhost() -> None:
    payload = json.dumps(
        {
            "site_url": "http://localhost:3000",
            "secret": "test-secret",
        }
    )
    with pytest.raises(APIError) as exc:
        validate_integration_payload("contentflow", payload)
    assert exc.value.detail["error"]["code"] == "UNSAFE_URL"


def test_validate_contentflow_payload_requires_secret() -> None:
    payload = json.dumps({"site_url": "https://ezfix.com.tw"})
    with pytest.raises(APIError) as exc:
        validate_integration_payload("contentflow", payload)
    assert exc.value.detail["error"]["code"] == "INVALID_CREDENTIAL"
