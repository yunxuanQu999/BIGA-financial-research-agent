#!/usr/bin/env python3
"""
Lightweight report evaluator.

Usage:
  python evals/run_eval.py --report output/sample_report.md
  python evals/run_eval.py --report output/sample_report.md --cases evals/test_cases.json
"""
import argparse
import json
import re
from pathlib import Path


def _has_citation(text: str) -> bool:
    return bool(re.search(r"\[\d+\]|来源[:：]|page/block|页码", text))


def score_report(report: str, case: dict) -> dict:
    expected = case.get("expected_keywords", [])
    found = [kw for kw in expected if kw in report]
    missing = [kw for kw in expected if kw not in report]
    citation_ok = True
    if case.get("requires_citation"):
        citation_ok = _has_citation(report)

    checks = {
        "keywords": len(found) / max(len(expected), 1),
        "citation": 1.0 if citation_ok else 0.0,
        "risk_warning": 1.0 if "风险" in report else 0.0,
    }
    score = round(sum(checks.values()) / len(checks), 3)
    return {
        "case_id": case.get("id", "unknown"),
        "score": score,
        "checks": checks,
        "missing_keywords": missing,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate generated research report quality.")
    parser.add_argument("--report", required=True, help="Path to a generated report text/markdown file")
    parser.add_argument("--cases", default="evals/test_cases.json", help="Path to eval case JSON")
    args = parser.parse_args()

    report = Path(args.report).read_text(encoding="utf-8")
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    results = [score_report(report, case) for case in cases]
    avg = round(sum(item["score"] for item in results) / max(len(results), 1), 3)
    print(json.dumps({"average_score": avg, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
