#!/usr/bin/env python3
"""
SHawn-BIO <-> SHawn-WEB search bridge CLI.
"""

from __future__ import annotations

import argparse
import json
from typing import List

from web_bio_search import BioWebSearchClient


def parse_aliases(raw: str) -> List[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Run SHawn-BIO search via SHawn-WEB API.")
    p.add_argument("--query", required=True, help="search query")
    p.add_argument("--mode", choices=["broad", "author"], default="broad")
    p.add_argument("--author-aliases", default="", help="comma-separated author aliases for author mode")
    p.add_argument("--first-author-only", action="store_true")
    p.add_argument("--merge-threshold", type=float, default=0.5)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--no-best-profile", action="store_true")
    p.add_argument("--out", default="", help="output json path")
    args = p.parse_args()

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

