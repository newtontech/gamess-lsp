"""Validation accuracy testing framework for GAMESS LSP.

This module loads fixture corpora, runs the validator, and computes
accuracy metrics (TP, FP, FN, precision, recall, F1) per category.

It does NOT claim exhaustive scientific coverage. The fixture corpus
represents a safe, tested subset of GAMESS parameter constraints.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

from gamess_lsp.parser import parse_gamess_input
from gamess_lsp.validator import validate_semantics

FIXTURE_ROOT = Path(__file__).parent


@dataclass
class FixtureCase:
    name: str
    category: str
    input_text: str
    expected_diagnostics: List[Dict[str, Any]]
    description: str = ""


@dataclass
class CategoryMetrics:
    category: str
    total: int = 0
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 1.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "total": self.total,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


@dataclass
class AccuracyReport:
    total_fixtures: int = 0
    passed: int = 0
    failed: int = 0
    categories: Dict[str, CategoryMetrics] = field(default_factory=dict)

    @property
    def overall_accuracy(self) -> float:
        return self.passed / self.total_fixtures if self.total_fixtures > 0 else 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_fixtures": self.total_fixtures,
            "passed": self.passed,
            "failed": self.failed,
            "overall_accuracy": f"{self.overall_accuracy:.2%}",
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
        }


def load_fixtures() -> List[FixtureCase]:
    fixtures = []
    for category_dir in sorted(FIXTURE_ROOT.iterdir()):
        if not category_dir.is_dir():
            continue
        if category_dir.name.startswith("_") or category_dir.name == "__pycache__":
            continue
        category = category_dir.name
        for fixture_file in sorted(category_dir.glob("*.json")):
            with open(fixture_file) as f:
                data = json.load(f)
            fixtures.append(
                FixtureCase(
                    name=f"{category}/{fixture_file.stem}",
                    category=category,
                    input_text=data["input"],
                    expected_diagnostics=data.get("expected_diagnostics", []),
                    description=data.get("description", ""),
                )
            )
    return fixtures


def run_fixture(case: FixtureCase) -> Tuple[bool, List[str]]:
    parsed = parse_gamess_input(case.input_text)
    actual = validate_semantics(parsed)
    actual_by_code: Dict[str, List] = {}
    for d in actual:
        actual_by_code.setdefault(d.code, []).append(d)
    mismatches = []
    all_passed = True
    for expected in case.expected_diagnostics:
        code = expected["code"]
        severity = expected.get("severity", "error")
        matching = actual_by_code.get(code, [])
        if not matching:
            mismatches.append(f"MISSING: expected {code} ({severity}), not found")
            all_passed = False
        elif not any(d.severity == severity for d in matching):
            actual_sevs = [d.severity for d in matching]
            mismatches.append(f"WRONG SEVERITY: expected {code} ({severity}), got {actual_sevs}")
            all_passed = False
    if not case.expected_diagnostics and actual:
        error_diags = [d for d in actual if d.severity == "error"]
        if error_diags:
            codes_str = ", ".join(d.code for d in error_diags)
            mismatches.append(f"FALSE POSITIVE: unexpected errors: {codes_str}")
            all_passed = False
    return all_passed, mismatches


def compute_accuracy_report() -> AccuracyReport:
    fixtures = load_fixtures()
    report = AccuracyReport()
    category_metrics: Dict[str, CategoryMetrics] = {}
    for case in fixtures:
        if case.category not in category_metrics:
            category_metrics[case.category] = CategoryMetrics(category=case.category)
        passed, _ = run_fixture(case)
        cat = category_metrics[case.category]
        cat.total += 1
        report.total_fixtures += 1
        if passed:
            report.passed += 1
            cat.true_positives += 1
        else:
            report.failed += 1
            cat.false_negatives += 1
    report.categories = category_metrics
    return report
