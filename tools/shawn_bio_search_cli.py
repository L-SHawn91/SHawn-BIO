#!/usr/bin/env python3
"""
SHawn-BIO search bridge CLI.

This module provides backward compatibility and redirects to shawn_bio_search.
For new code, use shawn_bio_search directly: `from shawn_bio_search import search_papers`
"""

from __future__ import annotations

import argparse
import json
import warnings
from typing import List

warnings.warn(
    "shawn_bio_search_cli is deprecated. Use shawn_bio_search directly.",
    DeprecationWarning,
    stacklevel=2
)


def parse_aliases(raw: str) -> List[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="SHawn-BIO search (redirects to shawn_bio_search)")
    p.add_argument("--query", required=True, help="search query")
    p.add_argument("--mode", choices=["broad", "author"], default="broad")
    p.add_argument("--author-aliases", default="", help="comma-separated author aliases")
    p.add_argument("--first-author-only", action="store_true")
    p.add_argument("--merge-threshold", type=float, default=0.5)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--no-best-profile", action="store_true")
    p.add_argument("--out", default="", help="output json path")
    args = p.parse_args()

    # Try to use shawn_bio_search first
    try:
        from shawn_bio_search import search_papers
        result_obj = search_papers(
            query=args.query,
            max_results=args.limit
        )
        # Convert to backward-compatible format
        papers = result_obj.papers if hasattr(result_obj, 'papers') else result_obj.get('papers', [])
        result = {
            "hits": len(papers),
            "papers": papers,
            "meta": {"source": "shawn_bio_search", "query": args.query},
            "profiles": []
        }
    except ImportError:
        # Fallback to web_bio_search if shawn_bio_search not available
        from web_bio_search import BioWebSearchClient
        client = BioWebSearchClient()
        if args.mode == "author":
            result = client.search_author_disambiguated(
                query=args.query,
                author_names=parse_aliases(args.author_aliases),
                limit=max(1, args.limit),
                first_author_only=bool(args.first_author_only),
                profile_merge_threshold=float(args.merge_threshold),
                use_best_profile=not args.no_best_profile,
            )
        else:
            hits = client.search(args.query, limit=max(1, args.limit))
            result = {"hits": hits, "papers": [], "meta": {}, "profiles": []}

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
