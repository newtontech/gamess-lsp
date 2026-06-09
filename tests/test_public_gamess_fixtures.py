"""Regression tests for public GAMESS input fixtures."""

from pathlib import Path

import pytest

from gamess_lsp.parser import GAMESSParser, parse_gamess_input

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gamess_public"


@pytest.mark.parametrize(
    ("fixture_name", "expected_groups"),
    [
        ("openqc_h2o_scf.inp", {"CONTRL", "SYSTEM", "BASIS", "SCF", "DATA"}),
        (
            "openqc_formaldehyde_tddft.inp",
            {"CONTRL", "SYSTEM", "BASIS", "TDDFT", "SCF", "DATA"},
        ),
        ("openqc_benzene_opt.inp", {"CONTRL", "SYSTEM", "BASIS", "STATPT", "SCF", "DATA"}),
        ("qclairvoyance_n_butane_energy.inp", {"BASIS", "CONTRL", "DATA"}),
    ],
)
def test_public_gamess_fixtures_parse_with_expected_groups(
    fixture_name: str, expected_groups: set[str]
) -> None:
    """Public real-world inputs should parse and expose their GAMESS groups."""
    content = (FIXTURE_DIR / fixture_name).read_text(encoding="utf-8")

    parsed = parse_gamess_input(content)
    assert expected_groups <= set(parsed.groups)
    assert parsed.get_group("CONTRL") is not None
    assert parsed.get_group("DATA") is not None

    parser = GAMESSParser()
    parsed_with_instance = parser.parse(content)

    assert not parser.errors
    assert expected_groups <= set(parsed_with_instance.groups)
