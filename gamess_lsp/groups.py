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

    "DFT": GroupDoc(
        name="DFT",
        description="Density Functional Theory options",
        required=False,
        parameters={
            "METHOD": ParameterDoc(
                name="METHOD",
                description="DFT method/functionals",
                type="string",
                default="B3LYP",
                valid_values=[
                    "B3LYP", "B3LYP5", "B3LYPX", "PBE", "PBE0", "M06", "M06-L",
                    "M06-2X", "M06-HF", "BLYP", "BP86", "B97-D", "B97-D3",
                    "CAM-B3LYP", "wB97X", "wB97XD", "LC-wPBE", "MN12-L",
                    "MN15", "MN15-L", "N12", "N12-SX", "SOGGA11-X", "M11",
                    "M11-L", "VSXC", "HSE06", "SLATER", "SVWN", "VWN",
                    "OPTX", "OLYP", "O3LYP", "X3LYP", "B1B95", "BB1K",
                    "MPW1K", "MPW1PW", "PW91", "TPSS", "revTPSS", "TPSSh",
                    "SCAN", "RSCAN", "r2SCAN", "r++SCAN", "B97M-V", "B97M-rV",
                    "WB97M-V", "WB97X-V", "M08-SO", "M08-HX", "M11", "M11-L"
                ]
            ),
            "GRID": ParameterDoc(
                name="GRID",
                description="Numerical integration grid",
                type="string",
                default="SG1",
                valid_values=[
                    "SG1", "FINE", "ULTRAFINE", "COARSE", "MEDIUM", "XFINE"
                ]
            ),
            "NRAD": ParameterDoc(
                name="NRAD",
                description="Number of radial grid points",
                type="integer",
                default="96"
            ),
            "NTHE": ParameterDoc(
                name="NTHE",
                description="Number of theta grid points",
                type="integer",
                default="12"
            ),
            "NPHI": ParameterDoc(
                name="NPHI",
                description="Number of phi grid points",
                type="integer",
                default="24"
            ),
            "NRAD0": ParameterDoc(
                name="NRAD0",
                description="Number of radial points for inner atoms",
                type="integer",
                default="40"
            ),
            "NTHE0": ParameterDoc(
                name="NTHE0",
                description="Number of theta points for inner atoms",
                type="integer",
                default="8"
            ),
            "NPHI0": ParameterDoc(
                name="NPHI0",
                description="Number of phi points for inner atoms",
                type="integer",
                default="16"
            ),
            "DIRECT": ParameterDoc(
                name="DIRECT",
                description="Use direct DFT (recompute integrals)",
                type="logical",
                default=".TRUE."
            ),
            "IDIRECT": ParameterDoc(
                name="IDIRECT",
                description="In-core direct DFT algorithm",
                type="logical",
                default=".FALSE."
            ),
            "DIFF": ParameterDoc(
                name="DIFF",
                description="Numerical differentiation for XC functional",
                type="logical",
                default=".FALSE."
            ),
            "ENCOMP": ParameterDoc(
                name="ENCOMP",
                description="Energy computation mode",
                type="string",
                default="OFF",
                valid_values=["OFF", "ON", "ONLY"]
            ),
            "TDDFT": ParameterDoc(
                name="TDDFT",
                description="Run TDDFT calculation",
                type="logical",
                default=".FALSE."
            ),
            "NSTATE": ParameterDoc(
                name="NSTATE",
                description="Number of excited states for TDDFT",
                type="integer",
                default="1"
            ),
            "ISTATE": ParameterDoc(
                name="ISTATE",
                description="State of interest for TDDFT",
                type="integer",
                default="1"
            ),
        }
    ),
    
    # Additional GAMESS groups
    "CIS": GroupDoc(
        name="CIS",
        description="Configuration Interaction Singles options",
        required=False,
        parameters={
            "NSTATE": ParameterDoc(
                name="NSTATE",
                description="Number of excited states to compute",
                type="integer",
                default="1"
            ),
            "ISTATE": ParameterDoc(
                name="ISTATE",
                description="State of interest for properties",
                type="integer",
                default="1"
            ),
            "MULT": ParameterDoc(
                name="MULT",
                description="Spin multiplicity for excited states",
                type="integer",
                valid_values=["1", "3"]
            ),
            "DIAGZN": ParameterDoc(
                name="DIAGZN",
                description="Diagonalization method",
                type="string",
                default="DAVIDSON",
                valid_values=["DAVIDSON", "JACOBI", "FULL"]
            ),
            "NCORE": ParameterDoc(
                name="NCORE",
                description="Number of core orbitals to freeze",
                type="integer",
                default="0"
            ),
        }
    ),
    
    "FORCE": GroupDoc(
        name="FORCE",
        description="Force constant and Hessian calculation options",
        required=False,
        parameters={
            "METHOD": ParameterDoc(
                name="METHOD",
                description="Method for Hessian calculation",
                type="string",
                default="ANALYTIC",
                valid_values=["ANALYTIC", "NUMERIC", "SEMINUM"]
            ),
            "VIBANL": ParameterDoc(
                name="VIBANL",
                description="Perform vibrational analysis",
                type="logical",
                default=".TRUE."
            ),
            "TEMP": ParameterDoc(
                name="TEMP",
                description="Temperature for thermodynamic analysis (K)",
                type="real",
                default="298.15"
            ),
            "PRES": ParameterDoc(
                name="PRES",
                description="Pressure for thermodynamic analysis (atm)",
                type="real",
                default="1.0"
            ),
            "SCAL": ParameterDoc(
                name="SCAL",
                description="Scale factor for frequencies",
                type="real",
                default="1.0"
            ),
        }
    ),
    
    "HESS": GroupDoc(
        name="HESS",
        description="Hessian matrix options",
        required=False,
        parameters={
            "PRTIFC": ParameterDoc(
                name="PRTIFC",
                description="Print internal force constants",
                type="logical",
                default=".FALSE."
            ),
            "PRTFCM": ParameterDoc(
                name="PRTFCM",
                description="Print full Cartesian force constant matrix",
                type="logical",
                default=".FALSE."
            ),
            "HLONLY": ParameterDoc(
                name="HLONLY",
                description="High level only in Hessian calculation",
                type="logical",
                default=".FALSE."
            ),
        }
    ),
    
    "MP2": GroupDoc(
        name="MP2",
        description="MP2 perturbation theory options",
        required=False,
        parameters={
            "METHOD": ParameterDoc(
                name="METHOD",
                description="MP2 algorithm",
                type="string",
                default="SEMI",
                valid_values=["SEMI", "FULL", "LOCAL"]
            ),
            "INCORE": ParameterDoc(
                name="INCORE",
                description="Use in-core integrals",
                type="logical",
                default=".FALSE."
            ),
            "CUTHF": ParameterDoc(
                name="CUTHF",
                description="Threshold for integral screening",
                type="real",
                default="1.0E-09"
            ),
            "NBOS": ParameterDoc(
                name="NBOS",
                description="Number of occupied orbitals to freeze",
                type="integer",
                default="0"
            ),
            "NVIR": ParameterDoc(
                name="NVIR",
                description="Number of virtual orbitals to freeze",
                type="integer",
                default="0"
            ),
        }
    ),
    
    "CC": GroupDoc(
        name="CC",
        description="Coupled Cluster options",
        required=False,
        parameters={
            "CONV": ParameterDoc(
                name="CONV",
                description="Convergence criterion for CC amplitudes",
                type="real",
                default="1.0E-06"
            ),
            "MAXIT": ParameterDoc(
                name="MAXIT",
                description="Maximum number of CC iterations",
                type="integer",
                default="50"
            ),
            "NCORE": ParameterDoc(
                name="NCORE",
                description="Number of core orbitals to freeze",
                type="integer",
                default="0"
            ),
            "NACT": ParameterDoc(
                name="NACT",
                description="Number of active orbitals",
                type="integer",
                default="0"
            ),
        }
    ),
    
    "EOM": GroupDoc(
        name="EOM",
        description="Equation of Motion coupled cluster options",
        required=False,
        parameters={
            "NSTATE": ParameterDoc(
                name="NSTATE",
                description="Number of excited states",
                type="integer",
                default="1"
            ),
            "MULT": ParameterDoc(
                name="MULT",
                description="Spin multiplicity",
                type="integer",
                valid_values=["1", "3"]
            ),
            "IROOT": ParameterDoc(
                name="IROOT",
                description="Root number for state of interest",
                type="integer",
                default="1"
            ),
        }
    ),
    
    "PCM": GroupDoc(
        name="PCM",
        description="Polarizable Continuum Model solvation",
        required=False,
        parameters={
            "SMD": ParameterDoc(
                name="SMD",
                description="Use SMD solvation model",
                type="logical",
                default=".FALSE."
            ),
            "SOLVNT": ParameterDoc(
                name="SOLVNT",
                description="Solvent name",
                type="string",
                valid_values=["WATER", "ACETONITRILE", "METHANOL", "ETHANOL", "DMSO", "DMF", "THF", "DCM", "BENZENE", "TOLUENE", "CYCLOHEXANE", "HEPTANE", "ANILINE", "ETHER", "CHLOROFORM", "OCTANOL"]
            ),
            "ICAV": ParameterDoc(
                name="ICAV",
                description="Cavity type",
                type="integer",
                default="0"
            ),
            "IDISP": ParameterDoc(
                name="IDISP",
                description="Dispersion correction",
                type="integer",
                default="0"
            ),
        }
    ),
    
    "COSMO": GroupDoc(
        name="COSMO",
        description="Conductor-like Screening Model",
        required=False,
        parameters={
            "EPS": ParameterDoc(
                name="EPS",
                description="Dielectric constant",
                type="real",
                default="78.39"
            ),
            "RSOLV": ParameterDoc(
                name="RSOLV",
                description="Solvent radius (Angstroms)",
                type="real",
                default="1.30"
            ),
            "ICORR": ParameterDoc(
                name="ICORR",
                description="Correction for outlying charge",
                type="integer",
                default="1"
            ),
        }
    ),
    
    "VEC": GroupDoc(
        name="VEC",
        description="Vector (molecular orbital) manipulation",
        required=False,
        parameters={
            "MOMAX": ParameterDoc(
                name="MOMAX",
                description="Maximum number of MOs to print",
                type="integer",
                default="99999"
            ),
            "MOINT": ParameterDoc(
                name="MOINT",
                description="MOs to interchange",
                type="string"
            ),
        }
    ),
    
    "POP": GroupDoc(
        name="POP",
        description="Population analysis options",
        required=False,
        parameters={
            "MULIKEN": ParameterDoc(
                name="MULIKEN",
                description="Print Mulliken population analysis",
                type="logical",
                default=".TRUE."
            ),
            "LOWDIN": ParameterDoc(
                name="LOWDIN",
                description="Print Lowdin population analysis",
                type="logical",
                default=".FALSE."
            ),
            "BOND": ParameterDoc(
                name="BOND",
                description="Print bond order analysis",
                type="logical",
                default=".FALSE."
            ),
        }
    ),
    
    "ELMOM": GroupDoc(
        name="ELMOM",
        description="Electric moments calculation",
        required=False,
        parameters={
            "WHERE": ParameterDoc(
                name="WHERE",
                description="Where to compute moments",
                type="string",
                default="PDCENTER",
                valid_values=["PDCENTER", "ORIGIN", "POINT"]
            ),
            "IEMOM": ParameterDoc(
                name="IEMOM",
                description="Which moments to compute",
                type="string",
                default="111111",
            ),
        }
    ),
    
    "ELPOT": GroupDoc(
        name="ELPOT",
        description="Electrostatic potential calculation",
        required=False,
        parameters={
            "WHERE": ParameterDoc(
                name="WHERE",
                description="Where to compute potential",
                type="string",
                default="PDCENTER",
                valid_values=["PDCENTER", "ORIGIN", "POINT", "GRID"]
            ),
            "OUTPUT": ParameterDoc(
                name="OUTPUT",
                description="Output format",
                type="string",
                default="PUNCH",
                valid_values=["PUNCH", "6", "BOTH"]
            ),
        }
    ),
    
    "PDC": GroupDoc(
        name="PDC",
        description="Potential-derived charges",
        required=False,
        parameters={
            "NPTE": ParameterDoc(
                name="NPTE",
                description="Number of points per unit sphere",
                type="integer",
                default="12"
            ),
            "NPTP": ParameterDoc(
                name="NPTP",
                description="Number of radial points",
                type="integer",
                default="4"
            ),
            "RMAX": ParameterDoc(
                name="RMAX",
                description="Maximum radius for charges (Angstroms)",
                type="real",
                default="2.8"
            ),
        }
    ),
    
    "MOREAD": GroupDoc(
        name="MOREAD",
        description="Read MO coefficients from $VEC group",
        required=False,
        parameters={}
    ),
    
    "AUXBAS": GroupDoc(
        name="AUXBAS",
        description="Auxiliary basis set for RI methods",
        required=False,
        parameters={
            "AUX": ParameterDoc(
                name="AUX",
                description="Auxiliary basis set type",
                type="string",
                default="NONE",
                valid_values=["NONE", "RI", "RIFIT", "JFIT", "JKFIT", "C-FIT", "CC-FIT"]
            ),
            "NBFAUX": ParameterDoc(
                name="NBFAUX",
                description="Number of auxiliary basis functions",
                type="integer",
                default="0"
            ),
        }
    ),
    
    "INTGRL": GroupDoc(
        name="INTGRL",
        description="Integral control options",
        required=False,
        parameters={
            "CUTTOFF": ParameterDoc(
                name="CUTTOFF",
                description="Integral cutoff threshold",
                type="real",
                default="1.0E-10"
            ),
            "ICUT": ParameterDoc(
                name="ICUT",
                description="Integral cutoff control",
                type="integer",
                default="11"
            ),
            "ITOL": ParameterDoc(
                name="ITOL",
                description="Two-electron integral tolerance",
                type="integer",
                default="20"
            ),
        }
    ),
    
    "TRANS": GroupDoc(
        name="TRANS",
        description="Integral transformation options",
        required=False,
        parameters={
            "MP2TRAN": ParameterDoc(
                name="MP2TRAN",
                description="MP2 integral transformation method",
                type="string",
                default="AUTO",
                valid_values=["AUTO", "SEMI", "FULL", "INCORE"]
            ),
            "DIRTRF": ParameterDoc(
                name="DIRTRF",
                description="Direct integral transformation",
                type="logical",
                default=".TRUE."
            ),
        }
    ),
    
    "CISVEC": GroupDoc(
        name="CISVEC",
        description="CIS vector options",
        required=False,
        parameters={
            "IVEC": ParameterDoc(
                name="IVEC",
                description="Which CIS vector to print",
                type="integer",
                default="1"
            ),
            "IVEC1": ParameterDoc(
                name="IVEC1",
                description="First CIS vector to print",
                type="integer",
                default="1"
            ),
            "IVEC2": ParameterDoc(
                name="IVEC2",
                description="Last CIS vector to print",
                type="integer",
                default="5"
            ),
        }
    ),
    
    "DAMP": GroupDoc(
        name="DAMP",
        description="Damping options for SCF",
        required=False,
        parameters={
            "DAMP": ParameterDoc(
                name="DAMP",
                description="Damping factor",
                type="real",
                default="0.0"
            ),
            "IDAMP": ParameterDoc(
                name="IDAMP",
                description="Damping iteration control",
                type="integer",
                default="0"
            ),
            "DAMPMX": ParameterDoc(
                name="DAMPMX",
                description="Maximum damping factor",
                type="real",
                default="0.5"
            ),
        }
    ),
    
    "DIIS": GroupDoc(
        name="DIIS",
        description="DIIS convergence acceleration",
        required=False,
        parameters={
            "DIIS": ParameterDoc(
                name="DIIS",
                description="Use DIIS extrapolation",
                type="logical",
                default=".TRUE."
            ),
            "NDIIS": ParameterDoc(
                name="NDIIS",
                description="Number of DIIS vectors",
                type="integer",
                default="10"
            ),
            "DIISSV": ParameterDoc(
                name="DIISSV",
                description="DIIS convergence threshold",
                type="real",
                default="0.1"
            ),
        }
    ),
    
    "LOCAL": GroupDoc(
        name="LOCAL",
        description="Localized orbital options",
        required=False,
        parameters={
            "METHOD": ParameterDoc(
                name="METHOD",
                description="Localization method",
                type="string",
                default="POP",
                valid_values=["POP", "PM", "ER", "FB", "BOYS", "PIPEK-MEZEY"]
            ),
            "TOL": ParameterDoc(
                name="TOL",
                description="Convergence tolerance",
                type="real",
                default="1.0E-06"
            ),
            "MAXIT": ParameterDoc(
                name="MAXIT",
                description="Maximum iterations",
                type="integer",
                default="100"
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
