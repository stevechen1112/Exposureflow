"""Topic graph clustering primitives (union-find, similarity)."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from urllib.parse import urlparse


_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1}


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def url_path_prefix(url: str, depth: int = 2) -> str:
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    return "/".join(parts[:depth])


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def add(self, node: str) -> None:
        if node not in self.parent:
            self.parent[node] = node
            self.rank[node] = 0

    def find(self, node: str) -> str:
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def groups(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = defaultdict(list)
        for node in self.parent:
            result[self.find(node)].append(node)
        return dict(result)


@dataclass
class QueryPageRow:
    query: str
    page: str
    impressions: int
    clicks: int
    position: float


@dataclass
class QueryStats:
    query: str
    total_impressions: int = 0
    total_clicks: int = 0
    best_url: str | None = None
    best_url_impressions: int = 0
    best_position: float | None = None
    urls: dict[str, int] = field(default_factory=dict)


def aggregate_query_stats(rows: list[QueryPageRow]) -> dict[str, QueryStats]:
    stats: dict[str, QueryStats] = {}
    for row in rows:
        if row.query not in stats:
            stats[row.query] = QueryStats(query=row.query)
        s = stats[row.query]
        s.total_impressions += row.impressions
        s.total_clicks += row.clicks
        s.urls[row.page] = s.urls.get(row.page, 0) + row.impressions
        if row.impressions > s.best_url_impressions:
            s.best_url_impressions = row.impressions
            s.best_url = row.page
            s.best_position = row.position
    return stats


def build_query_graph(
    rows: list[QueryPageRow],
    *,
    serp_keyword_urls: dict[str, list[str]] | None = None,
    semantic_threshold: float = 0.55,
    serp_overlap_threshold: float = 0.3,
) -> UnionFind:
    """Cluster queries via co-occurrence, SERP overlap, URL hierarchy, and token similarity."""
    uf = UnionFind()
    page_queries: dict[str, list[str]] = defaultdict(list)
    query_tokens: dict[str, set[str]] = {}

    for row in rows:
        uf.add(row.query)
        page_queries[row.page].append(row.query)
        query_tokens[row.query] = tokenize(row.query)

    # GSC co-occurrence on same page
    for queries in page_queries.values():
        unique = list(dict.fromkeys(queries))
        for i, q1 in enumerate(unique):
            for q2 in unique[i + 1 :]:
                uf.union(q1, q2)

    # URL hierarchy: queries on pages sharing path prefix
    prefix_queries: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        prefix = url_path_prefix(row.page)
        if prefix:
            prefix_queries[prefix].append(row.query)
    for queries in prefix_queries.values():
        unique = list(dict.fromkeys(queries))
        for i, q1 in enumerate(unique):
            for q2 in unique[i + 1 :]:
                uf.union(q1, q2)

    # Semantic similarity (token Jaccard as embedding proxy)
    queries = list(query_tokens.keys())
    for i, q1 in enumerate(queries):
        for q2 in queries[i + 1 :]:
            if jaccard_similarity(query_tokens[q1], query_tokens[q2]) >= semantic_threshold:
                uf.union(q1, q2)

    # SERP top-10 URL overlap
    if serp_keyword_urls:
        keyword_list = list(serp_keyword_urls.keys())
        for i, k1 in enumerate(keyword_list):
            urls1 = set(serp_keyword_urls[k1])
            for k2 in keyword_list[i + 1 :]:
                urls2 = set(serp_keyword_urls[k2])
                if not urls1 or not urls2:
                    continue
                overlap = len(urls1 & urls2) / min(len(urls1), len(urls2))
                if overlap >= serp_overlap_threshold:
                    uf.union(k1, k2)

    return uf


def keyword_level(keyword: str) -> str:
    tokens = tokenize(keyword)
    n = len(tokens)
    if n <= 2:
        return "head"
    if n <= 5:
        return "mid_tail"
    return "long_tail"


def pillar_candidate_score(
    url: str,
    impressions: int,
    max_impressions: int,
    *,
    asset_type: str = "page",
    internal_link_count: int = 0,
) -> float:
    norm_imp = impressions / max_impressions if max_impressions > 0 else 0
    norm_links = min(1.0, internal_link_count / 10)
    depth = len([p for p in urlparse(url).path.split("/") if p])
    depth_score = max(0.0, 1.0 - depth / 6)
    type_bonus = {
        "pillar_page": 0.3,
        "guide": 0.2,
        "comparison_page": 0.2,
        "product_page": 0.1,
    }.get(asset_type, 0.0)
    return norm_imp + norm_links + depth_score + type_bonus


def coverage_score(covered: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100.0 * covered / total, 2)
