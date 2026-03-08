#!/usr/bin/env python3
"""
SHawn-Bio-Search Natural Language Interface
자연어 → CLI 명령 변환
"""

import re
import sys
import json
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

class BioSearchNLI:
    """Natural Language Interface for bio search"""
    
    def __init__(self, skill_path: str = None):
        if skill_path is None:
            self.skill_path = Path.home() / ".openclaw/workspace/skills/shawn-bio-search"
        else:
            self.skill_path = Path(skill_path)
        self.scripts_path = self.skill_path / "scripts"
    
    def parse_intent(self, text: str) -> Dict:
        """자연어에서 의도와 엔티티 추출"""
        text_lower = text.lower()
        result = {
            "intent": "search_papers",  # default
            "query": None,
            "claim": None,
            "hypothesis": None,
            "organism": None,
            "assay": None,
            "max_results": 10,
            "output_format": "json"
        }
        
        # 의도 파악
        if any(kw in text_lower for kw in ["데이터셋", "dataset", "accession", "geo", "sra"]):
            result["intent"] = "search_datasets"
        elif any(kw in text_lower for kw in ["리뷰", "review", "인용목록", "citation list"]):
            result["intent"] = "review_pipeline"
        elif any(kw in text_lower for kw in ["벤치마크", "benchmark", "비교", "compare"]):
            result["intent"] = "benchmark"
        
        # 쿼리 추출 (주제)
        query_patterns = [
            r'(?:关于|about|regarding|concerning)?\s*([^,.。]+)(?:관련|相关|related|有关的?)?\s*(?:논문|论文|papers?|article|study|연구|研究)',
            r'(?:찾아|검색|search|find|look for)\s*(?:줘|해|해줘|一下)?\s*([^,.。]{3,50})',
            r'^([^,.。]{3,50})(?:관련|相关|에 대해|について|에 관한)',
        ]
        
        for pattern in query_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["query"] = match.group(1).strip()
                break
        
        # 쿼리가 없으면 전체 텍스트에서 핵심 용어 추출
        if not result["query"]:
            # 생물학 키워드 우선
            bio_keywords = re.findall(r'\b(endometrial|organoid|progesterone|estrogen|decidualization|implantation|embryo|stromal|epithelial|RNA-seq|scRNA|microarray)\w*\b', text, re.IGNORECASE)
            if bio_keywords:
                result["query"] = " ".join(set(bio_keywords))
            else:
                # 일반 명사 추출 (2단어 이상)
                words = re.findall(r'\b[A-Za-z]{3,}\b', text)
                if len(words) >= 2:
                    result["query"] = " ".join(words[:3])
        
        # 주장(claim) 추출
        claim_patterns = [
            r'(?:주장|claim|assertion|argue that)[,:]?\s*["\']?([^"\'.。]+)["\']?',
            r'(?:~이다|~입니다|is|are|was|were)\s+([^,.。]{10,100})',
        ]
        for pattern in claim_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["claim"] = match.group(1).strip()
                break
        
        # 가설(hypothesis) 추출
        hypo_patterns = [
            r'(?:가설|hypothesis|추정|speculate|suggest that)[,:]?\s*["\']?([^"\'.。]+)["\']?',
            r'(?:기여한다|contribute to|cause|lead to)[^,.。]*([^,.。]{10,80})',
        ]
        for pattern in hypo_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["hypothesis"] = match.group(1).strip()
                break
        
        # 생물체(organism) 추출
        organism_map = {
            "human": "Homo sapiens",
            "human": "Human",
            "human": "人",
            "mouse": "Mus musculus",
            "rat": "Rattus norvegicus",
            "pig": "Sus scrofa",
            "cow": "Bos taurus",
        }
        for key, value in organism_map.items():
            if key in text_lower:
                result["organism"] = value
                break
        
        # 실험 방법(assay) 추출
        assay_patterns = [
            r'\b(RNA-seq|RNAseq|RNASeq)\b',
            r'\b(scRNA-seq|single cell RNA|single-cell)\b',
            r'\b(microarray|마이크로어레이)\b',
            r'\b(ChIP-seq|ChIPseq)\b',
            r'\b(ATAC-seq|ATACseq)\b',
            r'\b(proteomics|프로테오믹스)\b',
            r'\b(metabolomics|메타볼로믹스)\b',
        ]
        for pattern in assay_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["assay"] = match.group(1)
                break
        
        # 결과 수 추출
        num_match = re.search(r'(\d+)\s*(?:개|건|편|results?|papers?)', text)
        if num_match:
            result["max_results"] = int(num_match.group(1))
        
        return result
    
    def execute(self, text: str) -> Dict:
        """자연어 명령 실행"""
        parsed = self.parse_intent(text)
        
        if parsed["intent"] == "search_datasets":
            return self._search_datasets(parsed)
        elif parsed["intent"] == "review_pipeline":
            return self._review_pipeline(parsed)
        elif parsed["intent"] == "benchmark":
            return self._benchmark(parsed)
        else:
            return self._search_papers(parsed)
    
    def _search_papers(self, parsed: Dict) -> Dict:
        """논문 검색 실행"""
        cmd = [
            "python3",
            str(self.scripts_path / "gather_papers.py"),
            "--query", parsed["query"] or "endometrial organoid",
            "--max-per-source", str(parsed["max_results"]),
            "--out", "/tmp/shawn_bio_papers.json"
        ]
        
        if parsed["claim"]:
            cmd.extend(["--claim", parsed["claim"]])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "success": result.returncode == 0,
                "command": " ".join(cmd),
                "parsed": parsed,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e), "parsed": parsed}
    
    def _search_datasets(self, parsed: Dict) -> Dict:
        """데이터셋 검색 실행"""
        cmd = [
            "python3",
            str(self.scripts_path / "dataset_search.py"),
            "--query", parsed["query"] or "endometrial organoid",
            "--max-per-source", str(parsed["max_results"]),
            "--out", "/tmp/shawn_bio_datasets.json"
        ]
        
        if parsed["organism"]:
            cmd.extend(["--organism", parsed["organism"]])
        if parsed["assay"]:
            cmd.extend(["--assay", parsed["assay"]])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "success": result.returncode == 0,
                "command": " ".join(cmd),
                "parsed": parsed,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e), "parsed": parsed}
    
    def _review_pipeline(self, parsed: Dict) -> Dict:
        """리뷰 파이프라인 실행"""
        cmd = [
            str(self.scripts_path / "run_review_pipeline.sh"),
            parsed["query"] or "endometrial organoid",
            parsed["claim"] or "",
            parsed["hypothesis"] or "",
            parsed["organism"] or "Homo sapiens",
            parsed["assay"] or "RNA-Seq",
            "/tmp/shawn_bio_review"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": result.returncode == 0,
                "command": " ".join(cmd),
                "parsed": parsed,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e), "parsed": parsed}
    
    def _benchmark(self, parsed: Dict) -> Dict:
        """벤치마크 실행"""
        cmd = [
            "python3",
            str(self.scripts_path / "benchmark_search.py"),
            "--query", parsed["query"] or "endometrial organoid",
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return {
                "success": result.returncode == 0,
                "command": " ".join(cmd),
                "parsed": parsed,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e), "parsed": parsed}


def main():
    """CLI 인터페이스"""
    nli = BioSearchNLI()
    
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = input("검색어를 입력하세요: ")
    
    print(f"\n📝 입력: {text}")
    print("-" * 50)
    
    result = nli.execute(text)
    
    print(f"\n🔍 파싱 결과:")
    print(json.dumps(result["parsed"], indent=2, ensure_ascii=False))
    
    print(f"\n⚙️ 실행 명령:")
    print(result.get("command", "N/A"))
    
    print(f"\n✅ 결과:")
    if result.get("success"):
        print("성공!")
        if result.get("stdout"):
            print(result["stdout"][:500])
    else:
        print(f"실패: {result.get('error', 'Unknown error')}")
        if result.get("stderr"):
            print(result["stderr"][:500])


if __name__ == "__main__":
    main()
