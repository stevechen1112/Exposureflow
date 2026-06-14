from exposureflow_api.integrations.error_sanitizer import sanitize_sync_error


def test_sanitize_sync_error_redacts_api_key() -> None:
    raw = "HTTP 403 for https://api.example.com?apikey=secret-key-123&site=1"
    assert "secret-key-123" not in sanitize_sync_error(raw)
    assert "apikey=***" in sanitize_sync_error(raw)
