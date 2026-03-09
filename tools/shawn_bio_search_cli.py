#!/usr/bin/env python3
"""
SHawn-BIO <-> SHawn-WEB search bridge CLI.

This wrapper can return raw SHawn-WEB payload (default) or a normalized
OpenClaw-ready bundle format (`--as-bundle`) for downstream scripts.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from web_bio_search import BioWebSearchClient


def parse_aliases(raw: str) -> List[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def _to_bundle(raw: Dict[str, Any], query: str, mode: str) -> Dict[str, Any]:
    # Accept both legacy payload and normalized output from web client.
    hits = raw.get("hits") or []
    papers = []
    for item in hits:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or ""
        year = item.get("year") or item.get("pubYear") or 0
        try:
            year = int(year)
        except Exception:
            year = 0
        papers.append(
            {
                "source": item.get("source") or "shawn-web",
                "id": item.get("id") or item.get("paperId") or item.get("doi") or "",
                "title": title,
                "authors": item.get("authors") or [],
                "year": year,
                "doi": item.get("doi") or "",
                "url": item.get("url") or item.get("link") or "",
                "abstract": item.get("abstract") or "",
                "citations": int(item.get("citations") or 0),
                "claim_overlap": item.get("claim_overlap") or "",
                "hypothesis_overlap": item.get("hypothesis_overlap") or "",
                "stage1_score": float(item.get("stage1_score") or 0.0),
                "stage2_score": float(item.get("stage2_score") or 0.0),
                "support_score": float(item.get("support_score") or 0.0),
                "contradiction_score": float(item.get("contradiction_score") or 0.0),
                "best_support_sentence": item.get("best_support_sentence") or "",
                "best_contradict_sentence": item.get("best_contradict_sentence") or "",
                "hypothesis_sentence_overlap": float(item.get("hypothesis_sentence_overlap") or 0.0),
                "evidence_score": float(item.get("evidence_score") or 0.0),
            }
        )

    return {
        "query": query,
        "mode": mode,
        "count": len(papers),
        "warnings": raw.get("warnings", []),
        "papers": papers,
        "raw": {
            "meta": raw.get("meta", {}),
            "profiles": raw.get("profiles", []),
            "selectedProfileId": raw.get("selectedProfileId", ""),
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run SHawn-BIO search via SHawn-WEB API.")
    p.add_argument("--query", required=True, help="search query")
    p.add_argument("--mode", choices=["broad", "author"], default="broad")
    p.add_argument("--author-aliases", default="", help="comma-separated author aliases for author mode")
    p.add_argument("--first-author-only", action="store_true")
    p.add_argument("--merge-threshold", type=float, default=0.5)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--as-bundle", action="store_true", help="output normalized paper bundle")
    p.add_argument("--no-best-profile", action="store_true")
    p.add_argument("--out", default="", help="output json path")
    args = p.parse_args()

    client = BioWebSearchClient()
    if args.mode == "author":
        aliases = parse_aliases(args.author_aliases)
        result = client.search_author_disambiguated(
            query=args.query,
            author_names=aliases,
            limit=max(1, args.limit),
            first_author_only=bool(args.first_author_only),
            profile_merge_threshold=float(args.merge_threshold),
            use_best_profile=not args.no_best_profile,
        )
    else:
        hits = client.search(args.query, limit=max(1, args.limit))
        result = {"hits": hits, "papers": [], "meta": {}, "profiles": []}

    if args.as_bundle:
        result = _to_bundle(result, query=args.query, mode=args.mode)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
