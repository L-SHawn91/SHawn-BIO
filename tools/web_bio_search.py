"""
Web-based bio literature search adapter.

⚠️ DEPRECATED: This module is deprecated in favor of shawn_bio_search.
Use shawn_bio_search for direct multi-source literature search.

Primary source: SHawn-WEB API (/api/papers/search-parallel).
"""

import warnings

warnings.warn(
    "web_bio_search is deprecated. Use shawn_bio_search instead. "
    "Install: pip install shawn-bio-search",
    DeprecationWarning,
    stacklevel=2
)

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from loguru import logger


def search_with_shawn_bio_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Redirect to shawn_bio_search if available."""
    try:
        from shawn_bio_search import search_papers
        result = search_papers(query=query, max_results=max_results)
        return result.papers if hasattr(result, 'papers') else result.get('papers', [])
    except ImportError:
        logger.warning("shawn_bio_search not installed. Falling back to web search.")
        return []


class BioWebSearchClient:
    """Adapter client for SHawn-WEB paper search API."""

    def __init__(self, base_url: Optional[str] = None, timeout_sec: Optional[int] = None):
        self.base_url = (base_url or os.environ.get("SHAWN_WEB_API_BASE") or "http://localhost:3000").rstrip("/")
        self.timeout_sec = int(timeout_sec or os.environ.get("SHAWN_WEB_API_TIMEOUT", "20"))
        self.endpoint = f"{self.base_url}/api/papers/search-parallel"

    @staticmethod
    def _normalize_query(query: str) -> str:
        q = (query or "").strip()
        q = re.sub(r"\s+", " ", q)
        return q

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        norm = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", (text or "").lower())
        return [t for t in norm.split() if len(t) >= 2]

    def _build_query_variants(self, query: str) -> List[str]:
        tokens = self._tokenize(query)
        variants: List[str] = [self._normalize_query(query)]
        variants.extend(tokens)
        for i in range(len(tokens) - 1):
            variants.append(f"{tokens[i]} {tokens[i + 1]}")

        # 짧은 쿼리 fallback(엄격 쿼리 실패 대비)
        if len(tokens) >= 3:
            variants.append(" ".join(tokens[:2]))
            variants.append(" ".join(tokens[-2:]))

        deduped: List[str] = []
        seen = set()
        for v in variants:
            v = self._normalize_query(v)
            if not v or v in seen:
                continue
            deduped.append(v)
            seen.add(v)
        return deduped[:6]

    @staticmethod
    def _safe_text(value: object) -> str:
        return str(value or "").strip()

    @staticmethod
    def _paper_key(paper: Dict) -> str:
        pid = BioWebSearchClient._safe_text(paper.get("id"))
        if pid:
            return pid
        url = BioWebSearchClient._safe_text(paper.get("url"))
        if url:
            return url
        title = BioWebSearchClient._safe_text(paper.get("title")).lower()
        source = BioWebSearchClient._safe_text(paper.get("source")).lower()
        return f"{source}|{title}"

    @staticmethod
    def _to_hit(paper: Dict, rank: int, variant_hit_count: int, total_variants: int) -> Dict:
        title = BioWebSearchClient._safe_text(paper.get("title"))
        abstract = BioWebSearchClient._safe_text(paper.get("abstract"))
        source = BioWebSearchClient._safe_text(paper.get("source"))
        url = BioWebSearchClient._safe_text(paper.get("url"))
        year = BioWebSearchClient._safe_text(paper.get("year"))
        authors = paper.get("authors") or []
        authors_text = ", ".join([str(a) for a in authors[:8]])

        source_label = source if source else "shawn-web"
        if year:
            source_label = f"{source_label} | {year}"

        content_parts = [title, abstract]
        if authors_text:
            content_parts.append(f"Authors: {authors_text}")
        if url:
            content_parts.append(f"URL: {url}")

        # SHawn-WEB 응답 score가 없으므로:
        # - 기본 순위 점수 + query variant 일치수 가중치
        base_rank_score = 1.0 / float(rank + 1)
        variant_score = float(variant_hit_count) / float(max(total_variants, 1))
        score = (base_rank_score * 0.8) + (variant_score * 0.2)

        return {
            "source": source_label,
            "title": title,
            "content": "\n".join([p for p in content_parts if p])[:2500],
            "distance": 0.0,
            "score": score,
            "token_hits": variant_hit_count,
            "variant_hit_count": variant_hit_count,
            "url": url,
        }

    def _search_once(
        self,
        query: str,
        limit: int,
        mode: str = "broad",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict], Dict[str, Any], bool]:
        payload: Dict[str, Any] = {"query": query, "mode": mode, "filters": dict(filters or {})}
        if limit > 0:
            payload["filters"]["limit"] = int(limit)
        try:
            resp = requests.post(self.endpoint, json=payload, timeout=self.timeout_sec)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning(f"SHawn-WEB paper search failed ({self.endpoint}): {e}")
            return [], {}, False

        papers = data.get("papers") or []
        meta = data.get("meta") or {}
        if not isinstance(papers, list):
            return [], meta, True
        return [p for p in papers[: max(1, limit)] if isinstance(p, dict)], meta, True

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search papers via SHawn-WEB API (query variants + relaxed recall) and normalize hits."""
        normalized = self._normalize_query(query)
        if not normalized or limit <= 0:
            return []

        variants = self._build_query_variants(normalized)
        if not variants:
            variants = [normalized]

        raw_per_call = max(limit, 10)
        total_variants = len(variants)
        merged: Dict[str, Dict] = {}

        for variant in variants:
            papers, _, ok = self._search_once(
                variant,
                limit=raw_per_call,
                mode="broad",
                filters={},
            )
            if not ok:
                break
            for rank, paper in enumerate(papers):
                key = self._paper_key(paper)
                if key not in merged:
                    merged[key] = {
                        "paper": paper,
                        "best_rank": rank,
                        "variant_hits": {variant},
                    }
                else:
                    merged[key]["best_rank"] = min(merged[key]["best_rank"], rank)
                    merged[key]["variant_hits"].add(variant)

        if not merged:
            return []

        ranked: List[Tuple[float, Dict]] = []
        for item in merged.values():
            best_rank = int(item["best_rank"])
            vhits = len(item["variant_hits"])
            hit = self._to_hit(item["paper"], rank=best_rank, variant_hit_count=vhits, total_variants=total_variants)
            ranked.append((float(hit["score"]), hit))

        ranked.sort(key=lambda x: x[0], reverse=True)
        return [hit for _, hit in ranked[:limit] if hit.get("content")]

    def search_author_disambiguated(
        self,
        query: str,
        author_names: List[str],
        limit: int = 20,
        first_author_only: bool = False,
        profile_merge_threshold: float = 0.5,
        use_best_profile: bool = True,
    ) -> Dict[str, Any]:
        """
        Author-mode search with homonym profile recommendation and optional auto-refine.
        Returns raw papers + profile metadata + normalized hits.
        """
        normalized = self._normalize_query(query)
        aliases = [self._normalize_query(a) for a in (author_names or []) if self._normalize_query(a)]
        if not normalized or not aliases:
            return {"papers": [], "meta": {}, "profiles": [], "hits": []}

        base_filters: Dict[str, Any] = {
            "authorNames": aliases,
            "firstAuthorOnly": bool(first_author_only),
            "profileMergeThreshold": max(0.3, min(0.9, float(profile_merge_threshold))),
        }
        papers, meta, ok = self._search_once(
            normalized,
            limit=max(10, limit),
            mode="author",
            filters=base_filters,
        )
        if not ok:
            return {"papers": [], "meta": {}, "profiles": [], "hits": []}

        profiles = meta.get("homonymProfiles") or []
        selected_profile_id = ""
        if use_best_profile and profiles:
            top = profiles[0] if isinstance(profiles[0], dict) else {}
            selected_profile_id = self._safe_text(top.get("profileId"))
            if selected_profile_id:
                refined_filters = dict(base_filters)
                refined_filters["profileIds"] = [selected_profile_id]
                rp, rm, rok = self._search_once(
                    normalized,
                    limit=max(10, limit),
                    mode="author",
                    filters=refined_filters,
                )
                if rok and isinstance(rp, list) and rp:
                    papers, meta = rp, rm
                    profiles = meta.get("homonymProfiles") or profiles

        hits = [
            self._to_hit(
                paper=p,
                rank=i,
                variant_hit_count=1,
                total_variants=1,
            )
            for i, p in enumerate(papers[: max(1, limit)])
            if isinstance(p, dict)
        ]
        return {
            "papers": papers[: max(1, limit)],
            "meta": meta,
            "profiles": profiles,
            "selectedProfileId": selected_profile_id,
            "hits": [h for h in hits if h.get("content")],
        }
