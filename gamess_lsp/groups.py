"""GAMESS $GROUP and parameter documentation."""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ParameterDoc:
    """Documentation for a parameter."""
    name: str
    description: str
    type: str
    default: Optional[str] = None
    valid_values: Optional[List[str]] = None


@dataclass
class GroupDoc:
    """Documentation for a $GROUP."""
    name: str
    description: str
    parameters: Dict[str, ParameterDoc]
    required: bool = False


# GAMESS $GROUP documentation
GAMESS_GROUPS: Dict[str, GroupDoc] = {
    "CONTRL": GroupDoc(
        name="CONTRL",
        description="Control options for the calculation",
        required=True,
        parameters={
            "SCFTYP": ParameterDoc(
                name="SCFTYP",
                description="Type of SCF calculation",
                type="string",
                default="RHF",
                valid_values=["RHF", "UHF", "ROHF", "GVB", "MCSCF"]
            ),
            "RUNTYP": ParameterDoc(
                name="RUNTYP",
                description="Type of calculation to perform",
                type="string",
                default="ENERGY",
                valid_values=[
                    "ENERGY", "OPTIMIZE", "SADPOINT", "IRC", "DRC", "HESSIAN",
                    "GRADIENT", "TRANSITN", "TRUDGE", "GLOBOP", "GRADEXTR",
                    "ADMP", "FMO", "SURFACE"
                ]
            ),
            "DFTTYP": ParameterDoc(
                name="DFTTYP",
                description="Density functional for DFT calculations",
                type="string",
                valid_values=[
                    "B3LYP", "PBE", "PBE0", "M06", "M06-L", "M06-2X", "M06-HF",
                    "BLYP", "BP86", "B97-D", "B97-D3", "CAM-B3LYP", "wB97X",
                    "wB97XD", "LC-wPBE", "MN12-L", "MN15", "MN15-L", "N12",
                    "N12-SX", "SOGGA11-X", "M11", "M11-L", "VSXC", "HSE06"
                ]
            ),
            "MPLEVL": ParameterDoc(
                name="MPLEVL",
                description="MP2 perturbation theory level",
                type="integer",
                default="0",
                valid_values=["0", "2"]
            ),
            "CITYP": ParameterDoc(
                name="CITYP",
                description="CI calculation type",
                type="string",
                valid_values=["CIS", "ALDET", "ORMAS", "GENCI", "FSOCI", "GUGA", "GVB"]
            ),
            "CCTYP": ParameterDoc(
                name="CCTYP",
                description="Coupled cluster calculation type",
                type="string",
                valid_values=["CCSD", "CCSD(T)", "CR-CC(2,3)", "CCSD(TQ)", "CR-EOM"]
            ),
            "EXETYP": ParameterDoc(
                name="EXETYP",
                description="Execution type",
                type="string",
                default="RUN",
                valid_values=["RUN", "CHECK", "DEBUG"]
            ),
            "MAXIT": ParameterDoc(
                name="MAXIT",
                description="Maximum number of SCF iterations",
                type="integer",
                default="30"
            ),
            "MULT": ParameterDoc(
                name="MULT",
                description="Spin multiplicity (2S+1)",
                type="integer",
                default="1"
            ),
            "ICHARG": ParameterDoc(
                name="ICHARG",
                description="Molecular charge",
                type="integer",
                default="0"
            ),
            "ISPHER": ParameterDoc(
                name="ISPHER",
                description="Use spherical harmonics",
                type="integer",
                default="1",
                valid_values=["0", "1", "-1"]
            ),
            "UNITS": ParameterDoc(
                name="UNITS",
                description="Units for geometry",
                type="string",
                default="ANGS",
                valid_values=["ANGS", "BOHR"]
            ),
            "COORD": ParameterDoc(
                name="COORD",
                description="Coordinate type",
                type="string",
                default="UNIQUE",
                valid_values=["UNIQUE", "CART", "ZMT", "ZMTMPC"]
            ),
            "ECP": ParameterDoc(
                name="ECP",
                description="Effective core potential",
                type="string",
                valid_values=["READ", "NONE"]
            ),
            "PP": ParameterDoc(
                name="PP",
                description="Pseudopotential",
                type="string",
                valid_values=["READ", "NONE"]
            ),
            "INTTYP": ParameterDoc(
                name="INTTYP",
                description="Integral program type",
                type="string",
                default="POPLE",
                valid_values=["POPLE", "HONDO", "NUPROP", "ROTBAS"]
            ),
        }
    ),
    
    "BASIS": GroupDoc(
        name="BASIS",
        description="Basis set specification",
        required=False,
        parameters={
            "GBASIS": ParameterDoc(
                name="GBASIS",
                description="Gaussian basis set type",
                type="string",
                default="N31",
                valid_values=[
                    "MINI", "MIDI", "STO", "N21", "N31", "N311", "D95", "D95V",
                    "CC-PVDZ", "CC-PVTZ", "CC-PVQZ", "CC-PV5Z", "CC-PV6Z",
                    "AUG-CC-PVDZ", "AUG-CC-PVTZ", "AUG-CC-PVQZ", "AUG-CC-PV5Z",
                    "SV", "DZV", "TZV", "MCMINI", "MCDZ", "MCTZ", "MCQZ",
                    "DGAUSS", "DHMS", "BC", "PDZ", "PTZ", "CCT", "CCQ", "CC5",
                    "CC6", "ACCT", "ACCQ", "ACC5", "ACC6", "PC0", "PC1", "PC2",
                    "PC3", "PC4", "APC0", "APC1", "APC2", "APC3", "APC4",
                    "SPK-DZP", "SPK-TZP", "SPK-QZP", "SPK-AUG-DZP", "SPK-AUG-TZP",
                    "SPK-AUG-QZP", "SAPPORO-DZP", "SAPPORO-TZP", "SAPPORO-QZP",
                    "SAPPORO-AUG-DZP", "SAPPORO-AUG-TZP", "SAPPORO-AUG-QZP"
                ]
            ),
            "NGAUSS": ParameterDoc(
                name="NGAUSS",
                description="Number of Gaussian primitives for Pople basis sets",
                type="integer",
                default="6"
            ),
            "NDFUNC": ParameterDoc(
                name="NDFUNC",
                description="Number of d functions to add",
                type="integer",
                default="0"
            ),
            "NPFUNC": ParameterDoc(
                name="NPFUNC",
                description="Number of p functions to add to H, He",
                type="integer",
                default="0"
            ),
            "NFFUNC": ParameterDoc(
                name="NFFUNC",
                description="Number of f functions to add",
                type="integer",
                default="0"
            ),
            "DIFFSP": ParameterDoc(
                name="DIFFSP",
                description="Add diffuse functions to heavy atoms",
                type="logical",
                default=".FALSE."
            ),
            "DIFFS": ParameterDoc(
                name="DIFFS",
                description="Add diffuse functions to H, He",
                type="logical",
                default=".FALSE."
            ),
            "EXTFILE": ParameterDoc(
                name="EXTFILE",
                description="External basis set file",
                type="string"
            ),
        }
    ),
    
    "SYSTEM": GroupDoc(
        name="SYSTEM",
        description="System resources and memory",
        required=False,
        parameters={
            "TIMLIM": ParameterDoc(
                name="TIMLIM",
                description="Time limit in minutes",
                type="integer",
                default="1000000"
            ),
            "MEMORY": ParameterDoc(
                name="MEMORY",
                description="Memory in megawords (MW)",
                type="integer",
                default="1000000"
            ),
            "MEMDDI": ParameterDoc(
                name="MEMDDI",
                description="Distributed Data Interface memory in MW",
                type="integer",
                default="0"
            ),
            "PARALL": ParameterDoc(
                name="PARALL",
                description="Parallel execution mode",
                type="logical",
                default=".TRUE."
            ),
        }
    ),
    
    "SCF": GroupDoc(
        name="SCF",
        description="SCF convergence options",
        required=False,
        parameters={
            "CONV": ParameterDoc(
                name="CONV",
                description="SCF convergence threshold",
                type="real",
                default="1.0E-05"
            ),
            "ETHRSH": ParameterDoc(
                name="ETHRSH",
                description="Energy threshold for DIIS extrapolation",
                type="real",
                default="1.0"
            ),
            "DIIS": ParameterDoc(
                name="DIIS",
                description="Use Pulay DIIS extrapolation",
                type="logical",
                default=".TRUE."
            ),
            "SOSCF": ParameterDoc(
                name="SOSCF",
                description="Use second-order SCF",
                type="logical",
                default=".FALSE."
            ),
            "DAMP": ParameterDoc(
                name="DAMP",
                description="Damping factor for SCF",
                type="real",
                default="0.0"
            ),
            "SHIFT": ParameterDoc(
                name="SHIFT",
                description="Level shifter for virtual orbitals",
                type="real",
                default="0.0"
            ),
            "RSTRCT": ParameterDoc(
                name="RSTRCT",
                description="Restrict open shell orbitals",
                type="logical",
                default=".FALSE."
            ),
            "DIRSCF": ParameterDoc(
                name="DIRSCF",
                description="Direct SCF (recompute integrals)",
                type="logical",
                default=".FALSE."
            ),
            "FDIFF": ParameterDoc(
                name="FDIFF",
                description="Use finite difference for Fock matrix",
                type="logical",
                default=".FALSE."
            ),
        }
    ),
    
    "DATA": GroupDoc(
        name="DATA",
        description="Molecular geometry and basis set data",
        required=True,
        parameters={
            # $DATA is special - contains geometry, not key=value pairs
        }
    ),
    
    "GUESS": GroupDoc(
        name="GUESS",
        description="Initial guess options",
        required=False,
        parameters={
            "GUESS": ParameterDoc(
                name="GUESS",
                description="Type of initial guess",
                type="string",
                default="HUCKEL",
                valid_values=[
                    "HUCKEL", "HCORE", "MOREAD", "MOSAVED", "SKIP", "CNDO",
                    "INDO", "PNDO", "SAD", "SHMO"
                ]
            ),
            "NORB": ParameterDoc(
                name="NORB",
                description="Number of orbitals to read with MOREAD",
                type="integer",
                default="0"
            ),
            "NAHO": ParameterDoc(
                name="NAHO",
                description="Natural atomic hybrid orbitals",
                type="logical",
                default=".FALSE."
            ),
            "MIX": ParameterDoc(
                name="MIX",
                description="Mix HOMO and LUMO (useful for UHF)",
                type="logical",
                default=".FALSE."
            ),
            "PRTMO": ParameterDoc(
                name="PRTMO",
                description="Print molecular orbitals",
                type="logical",
                default=".FALSE."
            ),
        }
    ),
    
    "STATPT": GroupDoc(
        name="STATPT",
        description="Geometry optimization options",
        required=False,
        parameters={
            "NSTEP": ParameterDoc(
                name="NSTEP",
                description="Maximum number of optimization steps",
                type="integer",
                default="100"
            ),
            "OPTTOL": ParameterDoc(
                name="OPTTOL",
                description="Optimization convergence tolerance",
                type="real",
                default="0.0001"
            ),
            "METHOD": ParameterDoc(
                name="METHOD",
                description="Optimization algorithm",
                type="string",
                default="SCHLEGEL",
                valid_values=["SCHLEGEL", "NR", "RFO", "QA", "GDIIS", "CONOPT"]
            ),
            "HESS": ParameterDoc(
                name="HESS",
                description="Hessian update method",
                type="string",
                default="GILL",
                valid_values=["GILL", "SCHLEGEL", "POWELL", "BFGS", "NUMERIC", "CALC", "READ"]
            ),
            "HSSEND": ParameterDoc(
                name="HSSEND",
                description="Compute Hessian at end of optimization",
                type="logical",
                default=".FALSE."
            ),
        }
    ),
}


def get_group_documentation(group_name: str) -> Optional[GroupDoc]:
    """Get documentation for a $GROUP."""
    return GAMESS_GROUPS.get(group_name.upper())


def get_parameter_documentation(group_name: str, param_name: str) -> Optional[ParameterDoc]:
    """Get documentation for a parameter within a $GROUP."""
    group = get_group_documentation(group_name)
    if group:
        return group.parameters.get(param_name.upper())
    return None


def get_all_group_names() -> List[str]:
    """Get all valid $GROUP names."""
    return list(GAMESS_GROUPS.keys())


def get_group_parameters(group_name: str) -> List[str]:
    """Get all parameter names for a $GROUP."""
    group = get_group_documentation(group_name)
    if group:
        return list(group.parameters.keys())
    return []
