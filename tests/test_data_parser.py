"""Tests for GAMESS data parser."""

import pytest
from gamess_lsp.data_parser import DataGroupParser, Atom, DataGroupInfo


class TestDataGroupParser:
    """Test cases for the $DATA group parser."""
    
    def test_parse_simple_data_group(self):
        parser = DataGroupParser()
        lines = [
            "$DATA",
            "Water molecule",
            "Cnv 2",
            "",
            "O  8.0   0.000000   0.000000   0.117790",
            "H  1.0   0.000000   0.755453  -0.471161",
            "H  1.0   0.000000  -0.755453  -0.471161",
            "$END"
        ]
        
        result = parser.parse_data_group(lines, 1, 8)
        
        assert result is not None
        assert result.title == "Water molecule"
        assert result.symmetry == "Cnv"
        assert len(result.atoms) == 3
        assert result.atoms[0].symbol == "O"
        assert result.atoms[0].atomic_number == 8.0
        assert result.atoms[0].x == 0.0
        assert result.atoms[0].y == 0.0
        assert result.atoms[0].z == 0.117790
    
    def test_parse_data_group_no_atomic_numbers(self):
        parser = DataGroupParser()
        lines = [
            "$DATA",
            "Water",
            "C1",
            "O   0.000000   0.000000   0.117790",
            "H   0.000000   0.755453  -0.471161",
            "H   0.000000  -0.755453  -0.471161",
            "$END"
        ]
        
        result = parser.parse_data_group(lines, 1, 7)
        
        assert result is not None
        assert len(result.atoms) == 3
        assert result.atoms[0].symbol == "O"
        assert result.atoms[0].atomic_number == 8.0  # Inferred from symbol
    
    def test_parse_data_group_empty(self):
        parser = DataGroupParser()
        lines = ["$DATA", "$END"]
        
        result = parser.parse_data_group(lines, 1, 2)
        
        assert result is None
        assert len(parser.errors) > 0
    
    def test_parse_invalid_atom_line(self):
        parser = DataGroupParser()
        lines = [
            "$DATA",
            "Test",
            "C1",
            "INVALID LINE",
            "$END"
        ]
        
        result = parser.parse_data_group(lines, 1, 5)
        
        assert result is not None
        assert len(result.atoms) == 0
        assert len(parser.errors) > 0
    
    def test_validate_atoms_valid(self):
        parser = DataGroupParser()
        atoms = [
            Atom("O", 8.0, 0.0, 0.0, 0.0, 4),
            Atom("H", 1.0, 0.757, 0.586, 0.0, 5),
            Atom("H", 1.0, -0.757, 0.586, 0.0, 6),
        ]
        
        errors = parser.validate_atoms(atoms)
        
        assert len(errors) == 0
    
    def test_validate_atoms_wrong_atomic_number(self):
        parser = DataGroupParser()
        atoms = [
            Atom("O", 6.0, 0.0, 0.0, 0.0, 4),  # Wrong atomic number for Oxygen
        ]
        
        errors = parser.validate_atoms(atoms)
        
        assert len(errors) == 1
        assert "mismatch" in errors[0][0].lower()
    
    def test_validate_atoms_large_coordinates(self):
        parser = DataGroupParser()
        atoms = [
            Atom("O", 8.0, 10000.0, 0.0, 0.0, 4),  # Unusually large coordinate
        ]
        
        errors = parser.validate_atoms(atoms)
        
        assert len(errors) == 1
        assert "large" in errors[0][0].lower()
    
    def test_get_molecular_formula(self):
        parser = DataGroupParser()
        atoms = [
            Atom("O", 8.0, 0.0, 0.0, 0.0, 4),
            Atom("H", 1.0, 0.757, 0.586, 0.0, 5),
            Atom("H", 1.0, -0.757, 0.586, 0.0, 6),
        ]
        
        formula = parser.get_molecular_formula(atoms)
        
        assert formula == "H2O"
    
    def test_get_molecular_formula_complex(self):
        parser = DataGroupParser()
        atoms = [
            Atom("C", 6.0, 0.0, 0.0, 0.0, 1),
            Atom("C", 6.0, 1.0, 0.0, 0.0, 2),
            Atom("H", 1.0, 0.5, 1.0, 0.0, 3),
            Atom("H", 1.0, 0.5, -1.0, 0.0, 4),
            Atom("O", 8.0, 2.0, 0.0, 0.0, 5),
        ]
        
        formula = parser.get_molecular_formula(atoms)
        
        assert formula == "C2H2O"
    
    def test_calculate_center_of_mass(self):
        parser = DataGroupParser()
        atoms = [
            Atom("O", 8.0, 0.0, 0.0, 0.0, 1),
            Atom("H", 1.0, 1.0, 0.0, 0.0, 2),
            Atom("H", 1.0, -1.0, 0.0, 0.0, 3),
        ]
        
        com = parser.calculate_center_of_mass(atoms)
        
        # Center of mass should be closer to oxygen (heavier)
        assert abs(com[0]) < 0.5
        assert com[1] == 0.0
        assert com[2] == 0.0


class TestSymmetryValidation:
    """Test symmetry group validation."""
    
    def test_valid_symmetry_groups(self):
        parser = DataGroupParser()
        valid_groups = ['C1', 'CS', 'CI', 'CNV', 'CNH', 'DN', 'T', 'TD', 'OH']
        
        for group in valid_groups:
            lines = ["$DATA", "Test", f"{group} 2", "O 8.0 0 0 0", "$END"]
            result = parser.parse_data_group(lines, 1, 5)
            assert result is not None, f"Failed for {group}"
    
    def test_invalid_symmetry_group(self):
        parser = DataGroupParser()
        lines = [
            "$DATA",
            "Test",
            "INVALID 2",
            "O 8.0 0 0 0",
            "$END"
        ]
        
        result = parser.parse_data_group(lines, 1, 5)
        
        assert result is not None
        assert len(parser.errors) > 0
        assert any("symmetry" in e[0].lower() for e in parser.errors)
