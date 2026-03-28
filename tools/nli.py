#!/usr/bin/env python3
"""
SHawn-Bio-Search Natural Language Interface
자연어 -> CLI 명령 변환
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List


def _default_skill_path() -> Path:
    env_path = os.getenv("SHAWN_BIO_SKILL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / "github/shawn-bio-search"


def _low_info_claim(claim: str) -> bool:
    x = (claim or "").strip().lower()
    if not x:
        return True
    if len(x) <= 3:
        return True
    return x in {"검증", "검증해", "확인", "확인해", "verify", "check", "prove"}


def _load_json_if_exists(path: str) -> Dict | None:
    try:
        p = Path(path)
        if not p.exists():
            return None
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _paper_explanation(p: Dict) -> str:
    evidence = float(p.get("evidence_score") or 0.0)
    support = float(p.get("support_score") or 0.0)
    contra = float(p.get("contradiction_score") or 0.0)
    claim_ov = float(p.get("claim_overlap") or 0.0)
    hyp_ov = float(p.get("hypothesis_overlap") or 0.0)
    sent = str(p.get("best_support_sentence") or "").strip()
    if sent:
        sent = sent[:220]
    if sent:
        return (
            f"evidence={evidence:.2f}, support={support:.2f}, contradiction={contra:.2f}, "
            f"claim_overlap={claim_ov:.2f}, hypothesis_overlap={hyp_ov:.2f}; "
            f"best_support_sentence: {sent}"
        )
    return (
        f"evidence={evidence:.2f}, support={support:.2f}, contradiction={contra:.2f}, "
        f"claim_overlap={claim_ov:.2f}, hypothesis_overlap={hyp_ov:.2f}"
    )


def _paper_refs_with_metadata(payload: Dict | None) -> List[Dict[str, str]]:
    if not payload:
        return []
    papers = payload.get("papers")
    if not isinstance(papers, list):
        return []
    refs: List[Dict[str, str]] = []
    for p in papers:
        if not isinstance(p, dict):
            continue
        title = str(p.get("title") or "").strip()
        if not title:
            continue
        authors = p.get("authors")
        if isinstance(authors, list):
            author_text = ", ".join([str(a).strip() for a in authors if str(a).strip()]) or "N/A"
        else:
            author_text = "N/A"
        year_val = p.get("year")
        year_text = str(year_val) if isinstance(year_val, int) and year_val > 0 else "N/A"
        doi = str(p.get("doi") or "").strip() or "N/A"
        refs.append(
            {
                "authors": author_text,
                "year": year_text,
                "title": title,
                "doi": doi,
                "explanation": _paper_explanation(p),
            }
        )
    return refs


class BioSearchNLI:
    """Natural Language Interface for bio search."""

    def __init__(self, skill_path: str | None = None):
        if skill_path is None:
            self.skill_path = _default_skill_path()
        else:
            self.skill_path = Path(skill_path).expanduser()
        self.scripts_path = self.skill_path / "scripts"

    def _script(self, name: str) -> Path:
        p = self.scripts_path / name
        if not p.exists():
            raise FileNotFoundError(f"script not found: {p}")
        return p

    def parse_intent(self, text: str) -> Dict:
        """자연어에서 의도와 엔티티 추출."""
        text_lower = text.lower()
        result = {
            "intent": "search_papers",
            "query": None,
            "claim": None,
            "hypothesis": None,
            "organism": None,
            "assay": None,
            "max_results": 10,
            "output_format": "json",
        }

        if any(kw in text_lower for kw in ["데이터셋", "dataset", "accession", "geo", "sra"]):
            result["intent"] = "search_datasets"
        elif any(kw in text_lower for kw in ["리뷰", "review", "인용목록", "citation list"]):
            result["intent"] = "review_pipeline"
        elif any(kw in text_lower for kw in ["벤치마크", "benchmark", "비교", "compare"]):
            result["intent"] = "benchmark"

        query_patterns = [
            r'(?:about|regarding|concerning)?\s*([^,.。]+)(?:관련|related)?\s*(?:논문|papers?|article|study|연구)',
            r'(?:찾아|검색|search|find|look for)\s*(?:줘|해|해줘)?\s*([^,.。]{3,80})',
            r'^([^,.。]{3,80})(?:관련|에 대해|에 관한)',
        ]
        for pattern in query_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["query"] = match.group(1).strip()
                break

        if not result["query"]:
            bio_keywords = re.findall(
                r"\b(endometrial|organoid|progesterone|estrogen|decidualization|implantation|embryo|stromal|epithelial|rna-?seq|scrna|microarray)\w*\b",
                text,
                re.IGNORECASE,
            )
            if bio_keywords:
                result["query"] = " ".join(sorted(set(bio_keywords)))
            else:
                words = re.findall(r"\b[A-Za-z]{3,}\b", text)
                if len(words) >= 2:
                    result["query"] = " ".join(words[:3])

        claim_patterns = [
            r'(?:주장|claim|assertion|argue that)[:\s]*["\']?([^"\'.。]{4,200})["\']?',
        ]
        for pattern in claim_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["claim"] = match.group(1).strip()
                break

        if ("주장" in text_lower or "claim" in text_lower) and _low_info_claim(result["claim"]):
            result["claim"] = result["query"]

        hypo_patterns = [
            r'(?:가설|hypothesis|추정|speculate|suggest that)[:\s]*["\']?([^"\'.。]{4,200})["\']?',
            r"(?:기여한다|contribute to|cause|lead to)[^,.。]*([^,.。]{10,80})",
        ]
        for pattern in hypo_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["hypothesis"] = match.group(1).strip()
                break

        organism_map = [
            ("human", "Homo sapiens"),
            ("사람", "Homo sapiens"),
            ("mouse", "Mus musculus"),
            ("rat", "Rattus norvegicus"),
            ("pig", "Sus scrofa"),
            ("cow", "Bos taurus"),
        ]
        for key, value in organism_map:
            if key in text_lower:
                result["organism"] = value
                break

        assay_patterns = [
            r"\b(RNA-seq|RNAseq|RNASeq)\b",
            r"\b(scRNA-seq|single cell RNA|single-cell)\b",
            r"\b(microarray|마이크로어레이)\b",
            r"\b(ChIP-seq|ChIPseq)\b",
            r"\b(ATAC-seq|ATACseq)\b",
            r"\b(proteomics|프로테오믹스)\b",
            r"\b(metabolomics|메타볼로믹스)\b",
        ]
        for pattern in assay_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["assay"] = match.group(1)
                break

        num_match = re.search(r"(\d+)\s*(?:개|건|편|results?|papers?)", text)
        if num_match:
            result["max_results"] = int(num_match.group(1))

        return result

    def build_command(self, parsed: Dict) -> List[str]:
        intent = parsed["intent"]
        if intent == "search_datasets":
            cmd = [
                "python3",
                str(self._script("dataset_search.py")),
                "--query",
                parsed["query"] or "endometrial organoid",
                "--max-per-source",
                str(parsed["max_results"]),
                "--out",
                "/tmp/shawn_bio_datasets.json",
            ]
            if parsed["organism"]:
                cmd.extend(["--organism", parsed["organism"]])
            if parsed["assay"]:
                cmd.extend(["--assay", parsed["assay"]])
            return cmd

        if intent == "review_pipeline":
            return [
                str(self._script("run_review_pipeline.sh")),
                parsed["query"] or "endometrial organoid",
                parsed["claim"] or "",
                parsed["hypothesis"] or "",
                parsed["organism"] or "Homo sapiens",
                parsed["assay"] or "RNA-Seq",
                "/tmp/shawn_bio_review",
            ]

        if intent == "benchmark":
            return [
                "python3",
                str(self._script("benchmark_search.py")),
                "--query",
                parsed["query"] or "endometrial organoid",
            ]

        cmd = [
            "python3",
            str(self._script("gather_papers.py")),
            "--query",
            parsed["query"] or "endometrial organoid",
            "--max-per-source",
            str(parsed["max_results"]),
            "--out",
            "/tmp/shawn_bio_papers.json",
        ]
        if parsed["claim"]:
            cmd.extend(["--claim", parsed["claim"]])
        return cmd

    def execute(self, text: str) -> Dict:
        parsed = self.parse_intent(text)
        try:
            cmd = self.build_command(parsed)
            timeout_map = {
                "search_papers": 60,
                "search_datasets": 60,
                "benchmark": 120,
                "review_pipeline": 300,
            }
            timeout = timeout_map.get(parsed["intent"], 60)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            references: List[Dict[str, str]] = []
            if parsed["intent"] == "search_papers":
                out_payload = _load_json_if_exists("/tmp/shawn_bio_papers.json")
                references = _paper_refs_with_metadata(out_payload)
            return {
                "success": result.returncode == 0,
                "command": " ".join(cmd),
                "parsed": parsed,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "references": references,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "parsed": parsed}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SHawn-BIO natural language runner (text -> CLI routing)."
    )
    parser.add_argument("text", nargs="*", help='natural language request, e.g. "RNA-Seq datasets 찾아"')
    parser.add_argument("--skill-path", default=None, help="skill root path (contains scripts/)")
    parser.add_argument("--dry-run", action="store_true", help="parse and print command only")
    parser.add_argument("--json", action="store_true", help="print full result as JSON")
    args = parser.parse_args()

    text = " ".join(args.text).strip()
    if not text:
        text = input("검색어를 입력하세요: ").strip()
    if not text:
        parser.error("empty input")

    nli = BioSearchNLI(skill_path=args.skill_path)
    parsed = nli.parse_intent(text)
    if args.dry_run:
        payload = {
            "success": True,
            "command": " ".join(nli.build_command(parsed)),
            "parsed": parsed,
            "stdout": "",
            "stderr": "",
        }
    else:
        payload = nli.execute(text)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload.get("success") else 1

    print(f"\n📝 입력: {text}")
    print("-" * 50)
    print("\n🔍 파싱 결과:")
    print(json.dumps(payload["parsed"], indent=2, ensure_ascii=False))
    print("\n⚙️ 실행 명령:")
    print(payload.get("command", "N/A"))
    print("\n✅ 결과:")
    if payload.get("success"):
        print("성공!")
        if payload.get("stdout"):
            print(payload["stdout"][:500])
        refs = payload.get("references") or []
        if payload.get("parsed", {}).get("intent") == "search_papers":
            print("\n📚 References (Authors / Year / Title / DOI / Explanation)")
        if refs:
            for i, ref in enumerate(refs, start=1):
                print(f"{i}. {ref['authors']} ({ref['year']})")
                print(f"   Title: {ref['title']}")
                print(f"   DOI: {ref['doi']}")
                print(f"   Explanation: {ref['explanation']}")
        elif payload.get("parsed", {}).get("intent") == "search_papers":
            print("- No references found.")
        return 0
    print(f"실패: {payload.get('error', 'Unknown error')}")
    if payload.get("stderr"):
        print(payload["stderr"][:500])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
