"""Tests for CLI module."""
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from gamess_lsp.cli import validate_file, parse_file, main


class TestValidateFile:
    """Tests for validate_file function."""
    
    def test_validate_nonexistent_file(self):
        """Test validating a file that doesn't exist."""
        result = validate_file("/nonexistent/file.inp")
        assert result == 1
    
    def test_validate_valid_file(self, tmp_path):
        """Test validating a valid GAMESS input file."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        result = validate_file(str(inp_file))
        assert result == 0
    
    def test_validate_with_errors(self, tmp_path):
        """Test validating a file with parse errors."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        result = validate_file(str(inp_file))
        # Missing $END for CONTRL is now an error
        assert result == 1
    
    def test_validate_json_output(self, tmp_path, capsys):
        """Test JSON output format."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        result = validate_file(str(inp_file), json_output=True)
        captured = capsys.readouterr()
        
        assert result == 0
        output = json.loads(captured.out)
        assert "valid" in output
        assert "groups_found" in output
        assert output["valid"] is True
    
    def test_validate_unknown_group(self, tmp_path, capsys):
        """Test validating a file with an unknown group."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$UNKNOWN
Test
$END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        result = validate_file(str(inp_file))
        captured = capsys.readouterr()
        
        # Unknown groups generate warnings, not errors
        assert result == 0
        assert "Groups found" in captured.out or "File:" in captured.out


class TestParseFile:
    """Tests for parse_file function."""
    
    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        result = parse_file("/nonexistent/file.inp")
        assert result == 1
    
    def test_parse_valid_file(self, tmp_path, capsys):
        """Test parsing a valid GAMESS input file."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        result = parse_file(str(inp_file))
        captured = capsys.readouterr()
        
        assert result == 0
        assert "CONTRL" in captured.out
        assert "DATA" in captured.out
        assert "SCFTYP = RHF" in captured.out
    
    def test_parse_json_output(self, tmp_path, capsys):
        """Test JSON output format."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        result = parse_file(str(inp_file), json_output=True)
        captured = capsys.readouterr()
        
        assert result == 0
        output = json.loads(captured.out)
        assert "groups" in output
        assert len(output["groups"]) >= 2
    
    def test_parse_empty_file(self, tmp_path, capsys):
        """Test parsing an empty file."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("")
        
        result = parse_file(str(inp_file))
        captured = capsys.readouterr()
        
        assert result == 0
        assert "Groups: 0" in captured.out


class TestMain:
    """Tests for main function."""
    
    @patch.object(sys, 'argv', ['gamess-lsp'])
    def test_main_no_args(self, capsys):
        """Test main with no arguments."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    
    @patch.object(sys, 'argv', ['gamess-lsp', '--version'])
    def test_main_version(self, capsys):
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "gamess-lsp" in captured.out
    
    def test_main_validate_command(self, tmp_path):
        """Test validate command through main."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        with patch.object(sys, 'argv', ['gamess-lsp', 'validate', str(inp_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_main_validate_json_command(self, tmp_path):
        """Test validate --json command."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        with patch.object(sys, 'argv', ['gamess-lsp', 'validate', '--json', str(inp_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_main_parse_command(self, tmp_path):
        """Test parse command through main."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        with patch.object(sys, 'argv', ['gamess-lsp', 'parse', str(inp_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_main_parse_json_command(self, tmp_path):
        """Test parse --json command."""
        inp_file = tmp_path / "test.inp"
        inp_file.write_text("""$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
H 1.0 0.0 0.0 0.0
$END
""")
        
        with patch.object(sys, 'argv', ['gamess-lsp', 'parse', '--json', str(inp_file)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    @patch.object(sys, 'argv', ['gamess-lsp', 'validate', '/nonexistent/file.inp'])
    def test_main_validate_nonexistent(self):
        """Test validate with non-existent file."""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
