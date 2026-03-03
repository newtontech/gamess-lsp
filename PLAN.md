# GAMESS LSP Development Plan

## Overview

This plan outlines the development of a Language Server Protocol (LSP) implementation for GAMESS (US) quantum chemistry input files.

## Input File Format

### GAMESS .inp File Structure
GAMESS input files use a card-based format with $GROUP sections:

```
$CONTRL SCFTYP=RHF RUNTYP=ENERGY MAXIT=50 MULT=1 $END
$SYSTEM MEMORY=4000000 TIMLIM=525600 $END
$BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
$SCF CONV=1.0E-06 DIIS=.TRUE. $END
$DATA
Water molecule - RHF/6-31G(d)
Cnv 2

O  8.0   0.000000   0.000000   0.117790
H  1.0   0.000000   0.755453  -0.471161
H  1.0   0.000000  -0.755453  -0.471161
$END
$GUESS GUESS=HUCKEL $END
```

### Key Components
- **$GROUP**: Groups start with `$NAME` and end with `$END`
- **Parameters**: `KEY=VALUE` pairs within groups
- **Comments**: Lines starting with `!`
- **$DATA Group**: Special group containing molecular geometry data
- **Coordinates**: Atom symbol, atomic number, x, y, z coordinates

## Implementation Phases

### Phase 1: Parser Core ✅
- [x] Basic $GROUP parsing
- [x] Parameter extraction (KEY=VALUE)
- [x] Multi-line group support
- [x] Comment handling
- [x] Error detection (unclosed groups, unknown groups)
- [x] Position-based queries

### Phase 2: $GROUP Documentation ✅
- [x] $CONTRL - Control options (SCFTYP, RUNTYP, MAXIT, MULT, etc.)
- [x] $BASIS - Basis set specification (GBASIS, NGAUSS, NDFUNC, etc.)
- [x] $SYSTEM - System resources (MEMORY, TIMLIM, PARALL)
- [x] $SCF - SCF convergence options (CONV, DIIS, SOSCF, etc.)
- [x] $DATA - Molecular geometry data
- [x] $GUESS - Initial guess options
- [x] $STATPT - Geometry optimization options

### Phase 3: LSP Features - In Progress

#### ✅ Completion
- [x] Group name completion (typing `$`)
- [x] Parameter completion within groups
- [x] Value completion for parameters with valid values

#### ✅ Hover
- [x] Group documentation on hover
- [x] Parameter documentation on hover

#### 🔄 Diagnostics (Current Focus)
- [ ] Unknown group validation
- [ ] Required parameter validation
- [ ] Parameter type validation (integer, real, logical, string)
- [ ] Valid value validation
- [ ] Missing $END detection

### Phase 4: Enhanced Features - Planned
- [ ] $DFT group support
- [ ] Coordinate data parsing (atom positions, charge)
- [ ] Code snippets for common inputs
- [ ] Symbol provider for outline view
- [ ] Folding support for $GROUP sections

### Phase 5: Testing & Documentation
- [x] Parser unit tests
- [x] Groups data tests
- [ ] Diagnostics tests
- [ ] LSP integration tests
- [ ] README documentation
- [ ] CONTRIBUTING guidelines

## Technical Details

### Parser Design
```python
class GamessParser:
    def parse(self, content: str) -> Tuple[List[Group], List[ParseError]]
    def get_group_at_position(self, line: int, column: int) -> Optional[Group]
    def get_parameter_at_position(self, line: int, column: int) -> Optional[GroupParameter]
```

### LSP Server
- **Framework**: pygls
- **Features**: Completion, Hover, Diagnostics
- **Protocol**: stdio (standard LSP communication)

### Parameter Types
- `string`: Text values (e.g., SCFTYP=RHF)
- `integer`: Integer values (e.g., MAXIT=50)
- `real`: Floating point values (e.g., CONV=1.0E-06)
- `logical`: Boolean values (e.g., DIIS=.TRUE.)

## Major $GROUPs

### $CONTRL (Required)
- SCFTYP: RHF, UHF, ROHF, GVB, MCSCF
- RUNTYP: ENERGY, OPTIMIZE, HESSIAN, etc.
- MAXIT: Maximum SCF iterations
- MULT: Spin multiplicity
- ICHARG: Molecular charge

### $BASIS
- GBASIS: N31, CC-PVDZ, STO, etc.
- NGAUSS: Number of Gaussian primitives
- NDFUNC/NPFUNC/NFFUNC: Polarization functions
- DIFFSP/DIFFS: Diffuse functions

### $SYSTEM
- MEMORY: Memory in megawords
- TIMLIM: Time limit in minutes
- PARALL: Parallel execution

### $SCF
- CONV: SCF convergence threshold
- DIIS: DIIS extrapolation
- SOSCF: Second-order SCF

### $DATA (Required)
- Title line
- Symmetry group
- Atom data: Symbol, atomic number, x, y, z

## Diagnostics

### Validation Rules
1. **Group Validation**: Check if $GROUP name is valid
2. **Parameter Validation**: Check if parameter exists in group
3. **Type Validation**: Validate parameter value type
4. **Value Validation**: Check if value is in valid set
5. **Required Validation**: Check if required groups are present

### Error Severity
- **Error**: Invalid syntax, missing required elements
- **Warning**: Unknown groups, deprecated parameters
- **Information**: Style suggestions

## Resources
- [GAMESS Documentation](https://www.msg.chem.iastate.edu/gamess/documentation.html)
- [GAMESS Input Manual](https://www.msg.chem.iastate.edu/gamess/GAMESS_Manual/input.doc.html)
- Language Server Protocol Specification

## Timeline
- Week 1: Parser Core ✅
- Week 2: LSP Features (Completion, Hover) ✅
- Week 3: Diagnostics 🔄 (Current)
- Week 4: Enhanced Features & Testing

---
*Plan Created: 2026-03-01*
*Last Updated: 2026-03-01*
