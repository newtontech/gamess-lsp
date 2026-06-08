"""Semantic validation rules for GAMESS input files.

This module provides physics/chemistry-aware validation that goes beyond
syntax checking to detect semantically incorrect but syntactically valid inputs.

Coverage note: This validator implements a safe, tested subset of GAMESS
parameter constraints. It does NOT claim exhaustive scientific validation
of all possible GAMESS input combinations. See the validation accuracy
framework (tests/validation/) for measured coverage.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .constants import ELEMENT_ATOMIC_NUMBERS
from .parser import GAMESSGroup, GAMESSInputFile


@dataclass
class SemanticDiagnostic:
    """A semantic validation diagnostic."""

    line: int
    message: str
    severity: str  # "error" or "warning"
    code: str  # Error code for programmatic handling
    related_info: Optional[List[Dict[str, Any]]] = None


class SemanticValidator:
    """Validates GAMESS input files for semantic correctness."""

    # SCFTYP constraints
    SCFTYP_MULT_CONSTRAINTS = {
        "RHF": {
            "allowed_mult": [1],
            "description": "RHF (Restricted Hartree-Fock) 只能用于闭壳层体系",
        },
        "UHF": {
            "allowed_mult": None,  # Any multiplicity allowed
            "description": "UHF (Unrestricted Hartree-Fock) 可用于任意自旋态",
        },
        "ROHF": {
            "allowed_mult": list(range(2, 100)),  # Must be open-shell
            "description": "ROHF (Restricted Open-shell HF) 需要开壳层体系 (MULT ≥ 2)",
        },
        "MCSCF": {
            "allowed_mult": None,  # Any multiplicity allowed
            "description": "MCSCF 可用于任意自旋态",
        },
        "NONE": {
            "allowed_mult": None,
            "description": "NONE 表示不进行 SCF 计算",
        },
    }

    # Method incompatibilities -- mutually exclusive post-HF / DFT methods
    METHOD_INCOMPATIBILITIES = [
        {
            "condition": lambda kws: kws.get("DFTTYP") and kws.get("MPLEVL") == "2",
            "message": "DFT 与 MP2 不能同时使用。DFTTYP 用于 DFT 计算，MPLEVL=2 用于 MP2 计算，二者互斥。",
            "severity": "error",
            "code": "INCOMPAT_DFT_MP2",
        },
        {
            "condition": lambda kws: kws.get("DFTTYP") and kws.get("CCTYP"),
            "message": "DFT 与 Coupled Cluster 不能同时使用。请选择 DFTTYP 或 CCTYP 其中之一。",
            "severity": "error",
            "code": "INCOMPAT_DFT_CC",
        },
        {
            "condition": lambda kws: kws.get("MPLEVL") == "2" and kws.get("CCTYP"),
            "message": "MP2 与 Coupled Cluster 不能同时使用。请选择 MPLEVL=2 或 CCTYP 其中之一。",
            "severity": "error",
            "code": "INCOMPAT_MP2_CC",
        },
        {
            "condition": lambda kws: kws.get("MPLEVL") == "2" and kws.get("CITYP"),
            "message": "MP2 与 CI 不能同时使用。MPLEVL=2 启用 MP2，CITYP 启用 CI 方法，二者互斥。",
            "severity": "error",
            "code": "INCOMPAT_MP2_CI",
        },
        {
            "condition": lambda kws: kws.get("CCTYP") and kws.get("CITYP"),
            "message": "Coupled Cluster 与 CI 不能同时使用。请选择 CCTYP 或 CITYP 其中之一。",
            "severity": "error",
            "code": "INCOMPAT_CC_CI",
        },
        {
            "condition": lambda kws: kws.get("DFTTYP") and kws.get("CITYP"),
            "message": "DFT 与 CI 不能同时使用。请选择 DFTTYP 或 CITYP 其中之一。",
            "severity": "error",
            "code": "INCOMPAT_DFT_CI",
        },
        {
            "condition": lambda kws: kws.get("SCFTYP") == "ROHF" and kws.get("MPLEVL") == "2",
            "message": "ROHF 与 MP2 不兼容。GAMESS 中 MP2 不支持 ROHF 参考。请使用 RHF 或 UHF。",
            "severity": "error",
            "code": "INCOMPAT_ROHF_MP2",
        },
        {
            "condition": lambda kws: kws.get("DFTTYP") and kws.get("SCFTYP") == "ROHF",
            "message": "ROHF-DFT 通常不被推荐。大多数 DFT 泛函不支持 ROHF。建议使用 UHF (UKS) 或 RHF (RKS)。",
            "severity": "warning",
            "code": "WARN_ROHF_DFT",
        },
        {
            "condition": lambda kws: kws.get("CCTYP") and kws.get("SCFTYP") == "UHF",
            "message": "UHF-CC 计算需要特别注意自旋污染问题。建议检查结果可靠性。",
            "severity": "warning",
            "code": "WARN_UHF_CC",
        },
    ]

    # Required parameters/groups for specific run types
    RUNTYP_REQUIREMENTS = {
        "OPTIMIZE": {
            "required_groups": ["STATPT"],
            "message": "几何优化计算建议提供 $STATPT 组以控制优化参数",
            "severity": "warning",
            "code": "MISSING_STATPT",
        },
        "HESSIAN": {
            "required_groups": ["FORCE", "HESSIAN"],  # At least one
            "require_any": True,
            "message": "频率计算需要 $FORCE 或 $HESSIAN 组",
            "severity": "warning",
            "code": "MISSING_FORCE",
        },
        "SADPOINT": {
            "required_groups": ["STATPT"],
            "message": "过渡态搜索需要 $STATPT 组，建议设置 HESS=CALC 或提供初始 Hessian",
            "severity": "warning",
            "code": "MISSING_STATPT_TS",
        },
        "IRC": {
            "required_groups": ["IRC"],
            "message": "IRC 计算需要 $IRC 组",
            "severity": "error",
            "code": "MISSING_IRC",
        },
    }

    # Cross-group conflicts: groups that should not coexist
    CROSS_GROUP_CONFLICTS = [
        {
            "group_a": "SCF",
            "group_b": "MCSCF",
            "condition": lambda kws: kws.get("SCFTYP") == "MCSCF",
            "message": "$SCF 组与 $MCSCF 组不应同时出现。MCSCF 计算应使用 $MCSCF 组而非 $SCF 组。",
            "severity": "warning",
            "code": "CONFLICT_SCF_MCSCF",
        },
    ]

    # RUNTYP values that are incompatible with certain method choices
    RUNTYP_METHOD_CONSTRAINTS = [
        {
            "runtyp": "SURFACE",
            "forbidden_kws": {"CCTYP": True},
            "message": "RUNTYP=SURFACE 不支持 Coupled Cluster 计算。",
            "severity": "error",
            "code": "INCOMPAT_SURFACE_CC",
        },
        {
            "runtyp": "DRC",
            "forbidden_kws": {"MPLEVL": "2"},
            "message": "RUNTYP=DRC (经典轨迹) 不支持 MP2 方法。DRC 需要 SCF 或 DFT 级别的势能面。",
            "severity": "error",
            "code": "INCOMPAT_DRC_MP2",
        },
    ]

    def validate(self, parsed_input: GAMESSInputFile) -> List[SemanticDiagnostic]:
        """Validate a parsed GAMESS input file.

        Args:
            parsed_input: The parsed GAMESS input file.

        Returns:
            List of semantic diagnostics.
        """
        diagnostics = []

        # Get $CONTRL group
        contrl = parsed_input.get_group("CONTRL")
        if not contrl:
            return diagnostics  # No CONTRL group, can't do semantic validation

        contrl_kws = {k.upper(): v.value for k, v in contrl.keywords.items()}

        # 1. Validate SCFTYP vs MULT
        diagnostics.extend(self._validate_scftyp_mult(contrl, contrl_kws))

        # 2. Validate method compatibility
        diagnostics.extend(self._validate_method_compatibility(contrl, contrl_kws))

        # 3. Validate electron count vs multiplicity
        diagnostics.extend(self._validate_electron_mult(parsed_input, contrl, contrl_kws))

        # 4. Validate required groups
        diagnostics.extend(self._validate_required_groups(parsed_input, contrl_kws))

        # 5. Validate cross-group conflicts
        diagnostics.extend(self._validate_cross_group_conflicts(parsed_input, contrl, contrl_kws))

        # 6. Validate RUNTYP vs method constraints
        diagnostics.extend(self._validate_runtyp_method(contrl, contrl_kws))

        return diagnostics

    def _validate_scftyp_mult(
        self, contrl: GAMESSGroup, contrl_kws: Dict[str, str]
    ) -> List[SemanticDiagnostic]:
        """Validate SCFTYP and MULT compatibility."""
        diagnostics = []

        scftyp = contrl_kws.get("SCFTYP", "RHF")  # Default is RHF
        mult_str = contrl_kws.get("MULT", "1")  # Default is singlet

        try:
            mult = int(mult_str)
        except ValueError:
            return diagnostics  # Invalid MULT value, will be caught by syntax validation

        if scftyp not in self.SCFTYP_MULT_CONSTRAINTS:
            return diagnostics  # Unknown SCFTYP, skip

        constraint = self.SCFTYP_MULT_CONSTRAINTS[scftyp]
        allowed_mult = constraint["allowed_mult"]

        if allowed_mult is not None and mult not in allowed_mult:
            # Find the keyword line for better error positioning
            mult_kw = contrl.keywords.get("MULT")
            line = mult_kw.line_number if mult_kw else contrl.line_start

            diagnostics.append(
                SemanticDiagnostic(
                    line=line,
                    message=f"SCFTYP={scftyp} 不支持 MULT={mult}。{constraint['description']}"
                    + ("\n建议：对于开壳层体系，使用 UHF 或 ROHF。" if scftyp == "RHF" else ""),
                    severity="error",
                    code="SCFTYP_MULT_INCOMPAT",
                )
            )

        return diagnostics

    def _validate_method_compatibility(
        self, contrl: GAMESSGroup, contrl_kws: Dict[str, str]
    ) -> List[SemanticDiagnostic]:
        """Validate method parameter compatibility."""
        diagnostics = []

        for rule in self.METHOD_INCOMPATIBILITIES:
            if rule["condition"](contrl_kws):
                diagnostics.append(
                    SemanticDiagnostic(
                        line=contrl.line_start,
                        message=rule["message"],
                        severity=rule["severity"],
                        code=rule["code"],
                    )
                )

        return diagnostics

    def _validate_electron_mult(
        self, parsed_input: GAMESSInputFile, contrl: GAMESSGroup, contrl_kws: Dict[str, str]
    ) -> List[SemanticDiagnostic]:
        """Validate electron count vs multiplicity."""
        diagnostics = []

        # Get electron count from geometry
        geometry = parsed_input.geometry
        if not geometry:
            return diagnostics  # No geometry, can't validate

        # Calculate total electrons
        total_electrons = 0
        for atom in geometry:
            # Try to get atomic number from Z field
            z = atom.get("z", atom.get("symbol", "0"))
            try:
                if isinstance(z, str):
                    # Could be element symbol or atomic number string
                    if z.isdigit() or (z[0] == "-" and z[1:].isdigit()):
                        z_num = int(z)
                    else:
                        # Element symbol - need periodic table lookup
                        z_num = self._element_to_z(z)
                else:
                    z_num = float(z)
                total_electrons += int(z_num)
            except (ValueError, TypeError):
                continue

        # Adjust for charge
        icharg_str = contrl_kws.get("ICHARG", "0")
        try:
            icharg = int(icharg_str)
            total_electrons -= icharg
        except ValueError:
            pass

        # Get multiplicity
        mult_str = contrl_kws.get("MULT", "1")
        try:
            mult = int(mult_str)
        except ValueError:
            return diagnostics

        # Validate: unpaired electrons = mult - 1
        # Total electrons = even + unpaired (for odd mult) or even (for even mult)
        unpaired = mult - 1

        # Check if electron count is consistent with multiplicity
        # Physics:
        # - MULT=1 (singlet): 0 unpaired -> even electrons
        # - MULT=2 (doublet): 1 unpaired -> odd electrons
        # - MULT=3 (triplet): 2 unpaired -> even electrons
        # - MULT=4 (quartet): 3 unpaired -> odd electrons
        # Pattern: odd MULT -> even electrons, even MULT -> odd electrons
        # So: mult_mod_2 != electrons_mod_2 for valid combinations
        electrons_mod_2 = total_electrons % 2
        mult_mod_2 = mult % 2

        # If they are equal, there's a mismatch
        if electrons_mod_2 == mult_mod_2:
            mult_kw = contrl.keywords.get("MULT")
            line = mult_kw.line_number if mult_kw else contrl.line_start

            diagnostics.append(
                SemanticDiagnostic(
                    line=line,
                    message=f"电子数 ({total_electrons}) 与多重态 (MULT={mult}) 不一致。\n"
                    f"  - 多重态 {mult} 意味着有 {unpaired} 个未配对电子\n"
                    f"  - 当前电子数 {total_electrons} ({'偶数' if electrons_mod_2 == 0 else '奇数'})\n"
                    f"  - 多重态 {mult} 需要{'偶数' if mult_mod_2 == 1 else '奇数'}电子\n"
                    f"建议：检查 MULT、ICHARG 或几何结构是否正确。",
                    severity="error",
                    code="ELECTRON_MULT_MISMATCH",
                )
            )

        # Additional check: open-shell system with RHF
        if total_electrons % 2 == 1 and contrl_kws.get("SCFTYP", "RHF") == "RHF":
            scftyp_kw = contrl.keywords.get("SCFTYP")
            line = scftyp_kw.line_number if scftyp_kw else contrl.line_start

            diagnostics.append(
                SemanticDiagnostic(
                    line=line,
                    message=f"体系有 {total_electrons} 个电子（奇数），存在未配对电子，但 SCFTYP=RHF。\n"
                    f"RHF 只能用于闭壳层体系。建议使用 UHF 或 ROHF。",
                    severity="error",
                    code="OPEN_SHELL_RHF",
                )
            )

        return diagnostics

    def _validate_required_groups(
        self, parsed_input: GAMESSInputFile, contrl_kws: Dict[str, str]
    ) -> List[SemanticDiagnostic]:
        """Validate that required groups are present for specific run types."""
        diagnostics = []

        runtyp = contrl_kws.get("RUNTYP", "ENERGY")
        contrl = parsed_input.get_group("CONTRL")

        if runtyp not in self.RUNTYP_REQUIREMENTS:
            return diagnostics

        req = self.RUNTYP_REQUIREMENTS[runtyp]
        required_groups = req["required_groups"]

        if req.get("require_any"):
            # At least one group must be present
            has_any = any(parsed_input.get_group(g) for g in required_groups)
            if not has_any:
                diagnostics.append(
                    SemanticDiagnostic(
                        line=contrl.line_start if contrl else 1,
                        message=req["message"],
                        severity=req["severity"],
                        code=req["code"],
                    )
                )
        else:
            # All required groups must be present
            for group_name in required_groups:
                if not parsed_input.get_group(group_name):
                    diagnostics.append(
                        SemanticDiagnostic(
                            line=contrl.line_start if contrl else 1,
                            message=req["message"],
                            severity=req["severity"],
                            code=req["code"],
                        )
                    )
                    break  # Only report once

        return diagnostics

    def _validate_cross_group_conflicts(
        self, parsed_input: GAMESSInputFile, contrl: GAMESSGroup, contrl_kws: Dict[str, str]
    ) -> List[SemanticDiagnostic]:
        """Validate that conflicting groups are not present together."""
        diagnostics = []

        for rule in self.CROSS_GROUP_CONFLICTS:
            group_a = parsed_input.get_group(rule["group_a"])
            group_b = parsed_input.get_group(rule["group_b"])
            if group_a and group_b:
                # Additional condition check if present
                if "condition" in rule and not rule["condition"](contrl_kws):
                    continue
                diagnostics.append(
                    SemanticDiagnostic(
                        line=contrl.line_start,
                        message=rule["message"],
                        severity=rule["severity"],
                        code=rule["code"],
                    )
                )

        # DFT group present but DFTTYP not set in CONTRL
        dft_group = parsed_input.get_group("DFT")
        if dft_group and not contrl_kws.get("DFTTYP"):
            diagnostics.append(
                SemanticDiagnostic(
                    line=dft_group.line_start,
                    message="存在 $DFT 组但未设置 DFTTYP。请在 $CONTRL 中设置 DFTTYP 以启用 DFT 计算。",
                    severity="warning",
                    code="DFT_GROUP_NO_DFTTYP",
                )
            )

        # MP2 group present but MPLEVL not set to 2
        mp2_group = parsed_input.get_group("MP2")
        if mp2_group and contrl_kws.get("MPLEVL") != "2":
            diagnostics.append(
                SemanticDiagnostic(
                    line=mp2_group.line_start,
                    message="存在 $MP2 组但未设置 MPLEVL=2。请在 $CONTRL 中设置 MPLEVL=2 以启用 MP2 计算。",
                    severity="warning",
                    code="MP2_GROUP_NO_MPLEVL",
                )
            )

        return diagnostics

    def _validate_runtyp_method(
        self, contrl: GAMESSGroup, contrl_kws: Dict[str, str]
    ) -> List[SemanticDiagnostic]:
        """Validate that RUNTYP is compatible with selected method."""
        diagnostics = []

        runtyp = contrl_kws.get("RUNTYP", "ENERGY")

        for rule in self.RUNTYP_METHOD_CONSTRAINTS:
            if runtyp != rule["runtyp"]:
                continue
            for kw_name, kw_value in rule["forbidden_kws"].items():
                actual = contrl_kws.get(kw_name)
                if actual is None:
                    continue
                if kw_value is True:
                    # Any value triggers the conflict
                    diagnostics.append(
                        SemanticDiagnostic(
                            line=contrl.line_start,
                            message=rule["message"],
                            severity=rule["severity"],
                            code=rule["code"],
                        )
                    )
                elif actual == kw_value:
                    diagnostics.append(
                        SemanticDiagnostic(
                            line=contrl.line_start,
                            message=rule["message"],
                            severity=rule["severity"],
                            code=rule["code"],
                        )
                    )

        return diagnostics

    def _element_to_z(self, symbol: str) -> int:
        """Convert element symbol to atomic number."""
        return ELEMENT_ATOMIC_NUMBERS.get(symbol.capitalize(), 0)


def validate_semantics(parsed_input: GAMESSInputFile) -> List[SemanticDiagnostic]:
    """Convenience function to validate semantics."""
    validator = SemanticValidator()
    return validator.validate(parsed_input)
