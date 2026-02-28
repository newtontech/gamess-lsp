"""Tests for GAMESS groups data."""

import pytest
from gamess_lsp.groups import (
    GAMESS_GROUPS,
    get_all_group_names,
    get_group_documentation,
    get_group_parameters,
    get_parameter_documentation,
)


class TestGroupsData:
    """Test cases for groups data."""
    
    def test_required_groups_exist(self):
        """Test that essential groups exist."""
        assert "CONTRL" in GAMESS_GROUPS
        assert "DATA" in GAMESS_GROUPS
    
    def test_contrl_parameters(self):
        """Test that CONTRL has expected parameters."""
        contrl = get_group_documentation("CONTRL")
        assert contrl is not None
        assert contrl.required
        
        assert "SCFTYP" in contrl.parameters
        assert "RUNTYP" in contrl.parameters
        assert "MAXIT" in contrl.parameters
        assert "MULT" in contrl.parameters
        assert "ICHARG" in contrl.parameters
    
    def test_scftyp_valid_values(self):
        """Test that SCFTYP has valid values."""
        scftyp = get_parameter_documentation("CONTRL", "SCFTYP")
        assert scftyp is not None
        assert "RHF" in scftyp.valid_values
        assert "UHF" in scftyp.valid_values
        assert "ROHF" in scftyp.valid_values
    
    def test_runtyp_valid_values(self):
        """Test that RUNTYP has valid values."""
        runtyp = get_parameter_documentation("CONTRL", "RUNTYP")
        assert runtyp is not None
        assert "ENERGY" in runtyp.valid_values
        assert "OPTIMIZE" in runtyp.valid_values
        assert "HESSIAN" in runtyp.valid_values
    
    def test_basis_parameters(self):
        """Test that BASIS has expected parameters."""
        basis = get_group_documentation("BASIS")
        assert basis is not None
        
        assert "GBASIS" in basis.parameters
        assert "NGAUSS" in basis.parameters
        assert "NDFUNC" in basis.parameters
    
    def test_get_all_group_names(self):
        """Test getting all group names."""
        names = get_all_group_names()
        assert "CONTRL" in names
        assert "BASIS" in names
        assert "DATA" in names
        assert "SYSTEM" in names
    
    def test_get_group_parameters(self):
        """Test getting group parameters."""
        params = get_group_parameters("CONTRL")
        assert "SCFTYP" in params
        assert "RUNTYP" in params
    
    def test_case_insensitive(self):
        """Test that group names are case insensitive."""
        assert get_group_documentation("contrl") is not None
        assert get_group_documentation("Contrl") is not None
        assert get_parameter_documentation("contrl", "scftyp") is not None
        assert get_parameter_documentation("CONTRL", "SCFTYP") is not None


class TestParameterDocumentation:
    """Test parameter documentation."""
    
    def test_parameter_has_description(self):
        """Test that parameters have descriptions."""
        param = get_parameter_documentation("CONTRL", "SCFTYP")
        assert param.description
        assert len(param.description) > 0
    
    def test_parameter_has_type(self):
        """Test that parameters have types."""
        param = get_parameter_documentation("CONTRL", "MAXIT")
        assert param.type == "integer"
    
    def test_parameter_default_values(self):
        """Test that some parameters have defaults."""
        scftyp = get_parameter_documentation("CONTRL", "SCFTYP")
        assert scftyp.default == "RHF"
        
        maxit = get_parameter_documentation("CONTRL", "MAXIT")
        assert maxit.default == "30"
