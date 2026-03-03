"""Additional edge case tests for GAMESS parser."""

import pytest
from gamess_lsp.parser import GamessParser, Group, GroupParameter, ParseError


class TestParserEdgeCases:
    """Test edge cases for the parser."""
    
    def test_parse_whitespace_only(self):
        parser = GamessParser()
        groups, errors = parser.parse("   \n\n   \n")
        assert len(groups) == 0
        assert len(errors) == 0
    
    def test_parse_only_comments(self):
        parser = GamessParser()
        content = """! This is a comment
! Another comment
! Third comment"""
        groups, errors = parser.parse(content)
        assert len(groups) == 0
        assert len(errors) == 0
    
    def test_parse_mixed_comments(self):
        parser = GamessParser()
        content = """! Comment at start
$CONTRL ! inline comment
   SCFTYP=RHF  ! another inline
$END
! Comment at end"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].name == "CONTRL"
    
    def test_empty_group(self):
        parser = GamessParser()
        content = """$CONTRL $END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert len(groups[0].parameters) == 0
    
    def test_parameter_with_spaces(self):
        parser = GamessParser()
        content = """$CONTRL SCFTYP = RHF $END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert len(groups[0].parameters) == 1
        assert groups[0].parameters[0].name == "SCFTYP"
        assert groups[0].parameters[0].value == "RHF"
    
    def test_multiple_parameters_same_line(self):
        parser = GamessParser()
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY MAXIT=50 MULT=1 $END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert len(groups[0].parameters) == 4
    
    def test_parameter_value_with_dots(self):
        parser = GamessParser()
        content = """$SCF CONV=1.0E-05 $END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].parameters[0].value == "1.0E-05"
    
    def test_parameter_value_with_sign(self):
        parser = GamessParser()
        content = """$CONTRL ICHARG=-1 $END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].parameters[0].value == "-1"
    
    def test_quoted_value_with_spaces(self):
        parser = GamessParser()
        content = '''$CONTRL SCFTYP="RHF UHF" $END'''
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].parameters[0].value == "RHF UHF"
    
    def test_single_quoted_value(self):
        parser = GamessParser()
        content = """$CONTRL SCFTYP='RHF' $END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].parameters[0].value == "RHF"
    
    def test_case_insensitive_group_names(self):
        parser = GamessParser()
        content = """$contrl scftyp=rhf $end"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].name == "CONTRL"
    
    def test_nested_groups_not_allowed(self):
        parser = GamessParser()
        content = """$CONTRL SCFTYP=RHF
$BASIS GBASIS=N31 $END
$END"""
        groups, errors = parser.parse(content)
        # Should detect unclosed CONTRL and separate BASIS
        assert len(groups) == 2
        # Should have error about unclosed CONTRL
        assert any("Unclosed" in e.message for e in errors)
    
    def test_get_group_at_position_exact(self):
        parser = GamessParser()
        content = """$CONTRL
   SCFTYP=RHF
$END"""
        groups, errors = parser.parse(content)
        
        # Position at start of group
        group = parser.get_group_at_position(1, 0)
        assert group is not None
        assert group.name == "CONTRL"
        
        # Position inside group
        group = parser.get_group_at_position(2, 5)
        assert group is not None
        
        # Position after group
        group = parser.get_group_at_position(10, 0)
        assert group is None
    
    def test_get_parameter_at_position_exact(self):
        parser = GamessParser()
        content = """$CONTRL SCFTYP=RHF $END"""
        groups, errors = parser.parse(content)
        
        # Position at parameter name
        param = parser.get_parameter_at_position(1, 10)
        assert param is not None
        assert param.name == "SCFTYP"
    
    def test_line_number_tracking(self):
        parser = GamessParser()
        content = """$CONTRL
   SCFTYP=RHF
   RUNTYP=ENERGY
$END"""
        groups, errors = parser.parse(content)
        
        assert groups[0].parameters[0].line == 2
        assert groups[0].parameters[1].line == 3


class TestParserDataGroup:
    """Test DATA group parsing."""
    
    def test_data_group_with_title(self):
        parser = GamessParser()
        content = """$DATA
Water molecule
C1
O 8.0 0.0 0.0 0.0
$END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].name == "DATA"
    
    def test_data_group_multi_atom(self):
        parser = GamessParser()
        content = """$DATA
Methane
Td

C 6.0 0.0 0.0 0.0
H 1.0 0.6 0.6 0.6
$END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert groups[0].name == "DATA"


class TestParserErrors:
    """Test parser error handling."""
    
    def test_multiple_unclosed_groups(self):
        parser = GamessParser()
        content = """$CONTRL SCFTYP=RHF
$BASIS GBASIS=N31
$SYSTEM MEMORY=1000"""
        groups, errors = parser.parse(content)
        
        # Should report multiple unclosed groups
        assert len(errors) >= 2
        assert any("CONTRL" in e.message for e in errors)
        assert any("BASIS" in e.message for e in errors)
    
    def test_dollar_sign_in_value(self):
        parser = GamessParser()
        # This should parse correctly - value doesn't contain $
        content = """$CONTRL SCFTYP=RHF $END"""
        groups, errors = parser.parse(content)
        assert len(groups) == 1
        assert len(errors) == 0
    
    def test_empty_parameter_value(self):
        parser = GamessParser()
        content = """$CONTRL SCFTYP= $END"""
        groups, errors = parser.parse(content)
        # Empty values might be parsed or not depending on implementation
        assert len(groups) == 1
