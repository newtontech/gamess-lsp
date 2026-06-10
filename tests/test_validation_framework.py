"""Validation accuracy tests driven by the fixture corpus.

These tests load JSON fixture files from tests/validation/ and verify
that the validator produces the expected diagnostics for each case.

This framework is designed to be extended: add new .json fixtures to
the appropriate subdirectory and they will be automatically discovered.
"""

import json

import pytest

from gamess_lsp.parser import parse_gamess_input
from gamess_lsp.validator import validate_semantics

from validation.conftest import (
    compute_accuracy_report,
    load_fixtures,
    run_fixture,
)


def _fixture_ids():
    """Generate test IDs from fixture names."""
    return [f.name for f in load_fixtures()]


@pytest.fixture(params=load_fixtures(), ids=_fixture_ids())
def fixture_case(request):
    """Parametrized fixture providing each test case."""
    return request.param


class TestFixtureCorpus:
    """Run all fixture cases from the validation corpus."""

    def test_fixture(self, fixture_case):
        """Each fixture should produce exactly the expected diagnostics."""
        passed, mismatches = run_fixture(fixture_case)
        assert passed, f"Fixture {fixture_case.name} failed:\n" + "\n".join(
            f"  - {m}" for m in mismatches
        )


class TestAccuracyReport:
    """Verify that the overall accuracy meets the minimum threshold."""

    def test_overall_accuracy_above_90_percent(self):
        """Overall accuracy across all fixture categories must be >= 90%."""
        report = compute_accuracy_report()
        assert report.overall_accuracy >= 0.90, (
            f"Overall accuracy {report.overall_accuracy:.2%} is below 90%.\n"
            f"Details: {json.dumps(report.to_dict(), indent=2)}"
        )

    def test_no_empty_categories(self):
        """Every category directory should have at least one fixture."""
        report = compute_accuracy_report()
        for cat_name, cat in report.categories.items():
            assert cat.total > 0, f"Category '{cat_name}' has no fixtures"

    def test_report_is_serializable(self):
        """The accuracy report should be JSON-serializable for CI reporting."""
        report = compute_accuracy_report()
        data = report.to_dict()
        json_str = json.dumps(data)
        assert json_str
        parsed_back = json.loads(json_str)
        assert "total_fixtures" in parsed_back
        assert "categories" in parsed_back


class TestCategoryAccuracy:
    """Per-category accuracy thresholds."""

    def test_mutually_exclusive_accuracy(self):
        """Mutually exclusive detection should be accurate."""
        report = compute_accuracy_report()
        cat = report.categories.get("mutually_exclusive")
        if cat and cat.total > 0:
            assert cat.precision >= 0.90, f"mutually_exclusive precision {cat.precision:.2%} < 90%"
            assert cat.recall >= 0.90, f"mutually_exclusive recall {cat.recall:.2%} < 90%"

    def test_chemical_constraints_accuracy(self):
        """Chemical constraint detection should be accurate."""
        report = compute_accuracy_report()
        cat = report.categories.get("chemical_constraints")
        if cat and cat.total > 0:
            assert (
                cat.precision >= 0.90
            ), f"chemical_constraints precision {cat.precision:.2%} < 90%"
            assert cat.recall >= 0.90, f"chemical_constraints recall {cat.recall:.2%} < 90%"

    def test_valid_inputs_no_errors(self):
        """Valid inputs should produce zero error-level diagnostics."""
        fixtures = load_fixtures()
        valid_cases = [f for f in fixtures if f.category == "valid_inputs"]
        for case in valid_cases:
            parsed = parse_gamess_input(case.input_text)
            diagnostics = validate_semantics(parsed)
            errors = [d for d in diagnostics if d.severity == "error"]
            assert (
                len(errors) == 0
            ), f"Valid input fixture {case.name} produced unexpected errors: " + ", ".join(
                d.code for d in errors
            )
