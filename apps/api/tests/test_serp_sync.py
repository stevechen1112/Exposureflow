from exposureflow_api.serp.service import should_sync_target_status


def test_should_sync_target_status_preserves_manual() -> None:
    assert should_sync_target_status("target") is True
    assert should_sync_target_status("achieved") is True
    assert should_sync_target_status("blocked") is False
    assert should_sync_target_status("not_applicable") is False
