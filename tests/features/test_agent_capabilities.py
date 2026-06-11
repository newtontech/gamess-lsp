"""Tests for agent API capabilities (issues #58, #59, #60, #76).

Covers domain language description, section/keyword schema lookup,
minimal examples, next-token guidance, rule manifest, and OpenQC smoke.
"""

import json

import pytest

from gamess_lsp.features.agent_api import AgentAPIProvider


@pytest.fixture
def api() -> AgentAPIProvider:
    return AgentAPIProvider()


# ------------------------------------------------------------------
# Issue #58: Domain language description API
# ------------------------------------------------------------------


class TestDomainDescription:
    """get_domain_description returns GAMESS domain metadata."""

    def test_returns_dict(self, api: AgentAPIProvider) -> None:
        result = api.get_domain_description()
        assert isinstance(result, dict)

    def test_has_language_key(self, api: AgentAPIProvider) -> None:
        result = api.get_domain_description()
        assert "language" in result
        assert "GAMESS" in result["language"]

    def test_has_description(self, api: AgentAPIProvider) -> None:
        result = api.get_domain_description()
        assert "description" in result
        assert len(result["description"]) > 50

    def test_has_conventions(self, api: AgentAPIProvider) -> None:
        result = api.get_domain_description()
        assert "conventions" in result
        assert isinstance(result["conventions"], list)
        assert len(result["conventions"]) > 0

    def test_has_file_extensions(self, api: AgentAPIProvider) -> None:
        result = api.get_domain_description()
        assert "file_extensions" in result
        assert ".inp" in result["file_extensions"]

    def test_has_common_groups(self, api: AgentAPIProvider) -> None:
        result = api.get_domain_description()
        assert "common_groups" in result
        assert "CONTRL" in result["common_groups"]
        assert "DATA" in result["common_groups"]

    def test_json_output(self, api: AgentAPIProvider) -> None:
        json_str = api.get_domain_description_json()
        parsed = json.loads(json_str)
        assert "language" in parsed

    def test_immutable_copy(self, api: AgentAPIProvider) -> None:
        """Returned dict is a copy, not the internal reference."""
        r1 = api.get_domain_description()
        r1["language"] = "MODIFIED"
        r2 = api.get_domain_description()
        assert r2["language"] != "MODIFIED"


# ------------------------------------------------------------------
# Issue #59: Section and keyword schema lookup
# ------------------------------------------------------------------


class TestSectionSchema:
    """get_section_info and get_keyword_info return schema data."""

    def test_contrl_section(self, api: AgentAPIProvider) -> None:
        info = api.get_section_info("CONTRL")
        assert info is not None
        assert "description" in info
        assert "keywords" in info

    def test_unknown_section_returns_none(self, api: AgentAPIProvider) -> None:
        info = api.get_section_info("BOGUS_SECTION")
        assert info is None

    def test_case_insensitive_section(self, api: AgentAPIProvider) -> None:
        info = api.get_section_info("contrl")
        assert info is not None

    def test_contrl_has_scftyp(self, api: AgentAPIProvider) -> None:
        info = api.get_keyword_info("CONTRL", "SCFTYP")
        assert info is not None
        assert "doc" in info
        assert "values" in info
        assert "RHF" in info["values"]

    def test_contrl_has_runtyp(self, api: AgentAPIProvider) -> None:
        info = api.get_keyword_info("CONTRL", "RUNTYP")
        assert info is not None
        assert "OPTIMIZE" in info["values"]

    def test_basis_has_gbasis(self, api: AgentAPIProvider) -> None:
        info = api.get_keyword_info("BASIS", "GBASIS")
        assert info is not None
        assert "STO" in info["values"]

    def test_unknown_keyword_returns_none(self, api: AgentAPIProvider) -> None:
        info = api.get_keyword_info("CONTRL", "NONEXISTENT")
        assert info is None

    def test_unknown_section_keyword_returns_none(self, api: AgentAPIProvider) -> None:
        info = api.get_keyword_info("BOGUS", "SCFTYP")
        assert info is None

    def test_all_sections_json(self, api: AgentAPIProvider) -> None:
        json_str = api.get_all_sections_json()
        parsed = json.loads(json_str)
        assert "CONTRL" in parsed
        assert "BASIS" in parsed

    def test_section_info_json(self, api: AgentAPIProvider) -> None:
        json_str = api.get_section_info_json("CONTRL")
        parsed = json.loads(json_str)
        assert "keywords" in parsed

    def test_unknown_section_info_json(self, api: AgentAPIProvider) -> None:
        json_str = api.get_section_info_json("BOGUS")
        parsed = json.loads(json_str)
        assert "error" in parsed


# ------------------------------------------------------------------
# Issue #60: Minimal examples and next-token guidance
# ------------------------------------------------------------------


class TestMinimalExamples:
    """get_minimal_example and get_all_examples provide sample inputs."""

    def test_energy_example(self, api: AgentAPIProvider) -> None:
        example = api.get_minimal_example("energy")
        assert example is not None
        assert "$CONTRL" in example
        assert "RUNTYP=ENERGY" in example

    def test_optimize_example(self, api: AgentAPIProvider) -> None:
        example = api.get_minimal_example("optimize")
        assert example is not None
        assert "RUNTYP=OPTIMIZE" in example

    def test_dft_example(self, api: AgentAPIProvider) -> None:
        example = api.get_minimal_example("dft")
        assert example is not None
        assert "DFTTYP" in example

    def test_mp2_example(self, api: AgentAPIProvider) -> None:
        example = api.get_minimal_example("mp2")
        assert example is not None
        assert "MPLEVL=2" in example

    def test_unknown_type_returns_none(self, api: AgentAPIProvider) -> None:
        assert api.get_minimal_example("nonexistent") is None

    def test_case_insensitive(self, api: AgentAPIProvider) -> None:
        assert api.get_minimal_example("ENERGY") is not None
        assert api.get_minimal_example("Energy") is not None

    def test_all_examples(self, api: AgentAPIProvider) -> None:
        examples = api.get_all_examples()
        assert "energy" in examples
        assert "optimize" in examples
        assert "dft" in examples
        assert "mp2" in examples

    def test_all_examples_json(self, api: AgentAPIProvider) -> None:
        json_str = api.get_all_examples_json()
        parsed = json.loads(json_str)
        assert len(parsed) >= 4


class TestNextTokenGuidance:
    """get_next_token_guidance returns context-aware suggestions."""

    def test_after_dollar(self, api: AgentAPIProvider) -> None:
        guide = api.get_next_token_guidance("after_dollar")
        assert guide is not None
        assert "CONTRL" in guide["suggestions"]
        assert "BASIS" in guide["suggestions"]

    def test_in_contrl(self, api: AgentAPIProvider) -> None:
        guide = api.get_next_token_guidance("in_contrl")
        assert guide is not None
        assert "SCFTYP" in guide["suggestions"]
        assert "RUNTYP" in guide["suggestions"]

    def test_in_basis(self, api: AgentAPIProvider) -> None:
        guide = api.get_next_token_guidance("in_basis")
        assert guide is not None
        assert "GBASIS" in guide["suggestions"]

    def test_scftyp_values(self, api: AgentAPIProvider) -> None:
        guide = api.get_next_token_guidance("scftyp_values")
        assert guide is not None
        assert "RHF" in guide["suggestions"]
        assert "UHF" in guide["suggestions"]

    def test_runtyp_values(self, api: AgentAPIProvider) -> None:
        guide = api.get_next_token_guidance("runtyp_values")
        assert guide is not None
        assert "ENERGY" in guide["suggestions"]
        assert "OPTIMIZE" in guide["suggestions"]

    def test_unknown_context_returns_none(self, api: AgentAPIProvider) -> None:
        assert api.get_next_token_guidance("nonexistent") is None

    def test_all_guidance(self, api: AgentAPIProvider) -> None:
        guidance = api.get_all_guidance()
        assert len(guidance) >= 4

    def test_all_guidance_json(self, api: AgentAPIProvider) -> None:
        json_str = api.get_all_guidance_json()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


# ------------------------------------------------------------------
# Issue #76: OpenQC smoke (get_rule_manifest + openqc_smoke)
# ------------------------------------------------------------------


class TestRuleManifest:
    """get_rule_manifest returns all GAMESS-prefixed rules."""

    def test_returns_dict(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        assert isinstance(manifest, dict)

    def test_has_provider(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        assert manifest["provider"] == "gamess-lsp"

    def test_has_version(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        assert "version" in manifest

    def test_has_rules(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        assert "rules" in manifest
        assert len(manifest["rules"]) == 8

    def test_rule_count_matches(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        assert manifest["rule_count"] == len(manifest["rules"])

    def test_all_rules_have_code(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        for rule in manifest["rules"]:
            assert "code" in rule
            assert rule["code"].startswith("GAMESS-")

    def test_all_rules_have_severity(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        for rule in manifest["rules"]:
            assert "severity" in rule
            assert rule["severity"] in ("error", "warning")

    def test_all_rules_have_description(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        for rule in manifest["rules"]:
            assert "description" in rule
            assert len(rule["description"]) > 0

    def test_json_output(self, api: AgentAPIProvider) -> None:
        json_str = api.get_rule_manifest_json()
        parsed = json.loads(json_str)
        assert "rules" in parsed

    def test_expected_codes_present(self, api: AgentAPIProvider) -> None:
        manifest = api.get_rule_manifest()
        codes = {r["code"] for r in manifest["rules"]}
        expected = {
            "GAMESS-E050", "GAMESS-E051", "GAMESS-E052", "GAMESS-E053",
            "GAMESS-E054", "GAMESS-W050", "GAMESS-E055", "GAMESS-E056",
        }
        assert codes == expected


class TestOpenQCSmoke:
    """openqc_smoke runs a full parse-and-lint cycle."""

    def test_default_smoke(self, api: AgentAPIProvider) -> None:
        result = api.openqc_smoke()
        assert result["status"] == "ok"
        assert "parsed_groups" in result
        assert "diagnostic_count" in result
        assert "manifest" in result

    def test_smoke_with_valid_input(self, api: AgentAPIProvider) -> None:
        source = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$BASIS GBASIS=STO NGAUSS=3 $END\n"
            "$DATA\nTitle\nC1\nH 1.0 0.0 0.0 0.0\n$END\n"
        )
        result = api.openqc_smoke(source)
        assert result["status"] == "ok"

    def test_smoke_with_invalid_input(self, api: AgentAPIProvider) -> None:
        source = "$CONTRL SCFTYP=INVALID $END\n"
        result = api.openqc_smoke(source)
        assert result["status"] == "ok"
        assert result["diagnostic_count"] > 0

    def test_smoke_json(self, api: AgentAPIProvider) -> None:
        json_str = api.openqc_smoke_json()
        parsed = json.loads(json_str)
        assert parsed["status"] == "ok"

    def test_smoke_manifest_matches(self, api: AgentAPIProvider) -> None:
        result = api.openqc_smoke()
        manifest = api.get_rule_manifest()
        assert result["manifest"]["rule_count"] == manifest["rule_count"]

    def test_smoke_parses_groups(self, api: AgentAPIProvider) -> None:
        source = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$BASIS GBASIS=STO NGAUSS=3 $END\n"
            "$DATA\nTitle\nC1\nH 1.0 0.0 0.0 0.0\n$END\n"
        )
        result = api.openqc_smoke(source)
        assert "CONTRL" in result["parsed_groups"]
        assert "BASIS" in result["parsed_groups"]
        assert "DATA" in result["parsed_groups"]
