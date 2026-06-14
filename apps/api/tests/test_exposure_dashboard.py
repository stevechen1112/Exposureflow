"""Unit tests for exposure dashboard aggregation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from exposureflow_api.exposure.dashboard import build_dashboard_metrics


def _scalar_result(value: int | float) -> MagicMock:
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _rows_result(rows: list) -> MagicMock:
    result = MagicMock()
    result.all.return_value = rows
    return result


def _clusters_result(clusters: list) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = clusters
    return result


@pytest.mark.asyncio
async def test_build_dashboard_metrics_empty_site() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _scalar_result(0),  # current impressions
            _scalar_result(0),  # previous impressions
            _scalar_result(0),  # query coverage
            _scalar_result(0),  # indexed assets
            _rows_result([]),  # position rows
            _scalar_result(0),  # serp slots
            _scalar_result(0),  # ai citations
            _scalar_result(0),  # open opps
            _scalar_result(0),  # critical blockers
            _clusters_result([]),
        ]
    )
    data = await build_dashboard_metrics(db, uuid4(), uuid4())
    assert data["total_impressions"] == 0
    assert data["impressions_delta_pct"] == 0.0
    assert data["open_opportunity_count"] == 0
    assert data["topic_cluster_performance"] == []


@pytest.mark.asyncio
async def test_build_dashboard_metrics_delta_pct() -> None:
    db = AsyncMock()
    db.execute = AsyncMock(
        side_effect=[
            _scalar_result(150),
            _scalar_result(100),
            _scalar_result(5),
            _scalar_result(3),
            _rows_result([( "q1", 2.5), ("q2", 12.0)]),
            _scalar_result(1),
            _scalar_result(2),
            _scalar_result(4),
            _scalar_result(1),
            _clusters_result([SimpleNamespace(
                id=uuid4(),
                name="Cluster A",
                total_impressions=1000,
                coverage_score=0.8,
                ai_visibility_score=0.5,
                status="active",
            )]),
        ]
    )
    data = await build_dashboard_metrics(db, uuid4(), uuid4())
    assert data["total_impressions"] == 150
    assert data["impressions_delta_pct"] == 50.0
    assert data["top_3_count"] == 1
    assert data["top_10_count"] == 1
    assert data["top_20_count"] == 2
    assert len(data["topic_cluster_performance"]) == 1
    assert data["topic_cluster_performance"][0]["name"] == "Cluster A"
