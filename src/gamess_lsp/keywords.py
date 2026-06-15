"""GAMESS keywords database.

See also: wiki/synthesis/GAMESS_Input_Syntax.md
"""

GAMESS_GROUPS = {
    "CONTRL": """$CONTRL group - Main control options for GAMESS calculation.
This group controls the calculation type, theory level, and run options.""",
    "SYSTEM": """$SYSTEM group - System-specific options.
Memory allocation, timing, and parallelization settings.""",
    "BASIS": """$BASIS group - Basis set specification.
Controls the basis set used for the calculation.""",
    "SCF": """$SCF group - SCF (Hartree-Fock) calculation options.
Controls convergence criteria and SCF algorithm.""",
    "DFT": """$DFT group - Density Functional Theory options.
Exchange-correlation functional and grid settings.""",
    "MP2": """$MP2 group - Møller-Plesset perturbation theory.
MP2 energy and gradient calculation options.""",
    "CC": """$CC group - Coupled Cluster theory options.
CCSD, CCSD(T) and other coupled cluster methods.""",
    "CIS": """$CIS group - Configuration Interaction Singles.
CIS/TDHF excited state calculations.""",
    "TDDFT": """$TDDFT group - Time-Dependent DFT options.
TDDFT excited state calculations.""",
    "STATPT": """$STATPT group - Geometry optimization options.
Controls geometry convergence criteria and algorithm.""",
    "FORCE": """$FORCE group - Force constant calculation.
Vibrational frequency and thermodynamic properties.""",
    "HESSIAN": """$HESSIAN group - Hessian matrix options.
Analytic or numerical second derivatives.""",
    "VIB": """$VIB group - Vibrational analysis options.
Mode following and anharmonic corrections.""",
    "IRC": """$IRC group - Intrinsic Reaction Coordinate.
Reaction path following calculations.""",
    "DRC": """$DRC group - Dynamic Reaction Coordinate.
Classical trajectory on potential energy surface.""",
    "GUESS": """$GUESS group - Initial guess options.
Huckel, core, or restart guess for SCF.""",
    "VEC": """$VEC group - Molecular orbitals.
User-provided MO coefficients.""",
    "DATA": """$DATA group - Molecular structure.
Geometry and symmetry specification.""",
    "LIBRARY": """$LIBRARY group - Basis set library.
External basis set library specification.""",
    "ECP": """$ECP group - Effective Core Potentials.
Pseudopotential specification.""",
    "PCM": """$PCM group - Polarizable Continuum Model.
Solvation effects with PCM.""",
    "COSM": """$COSM group - COSMO solvation model.
Conductor-like screening model.""",
    "EFRAG": """$EFRAG group - Effective Fragment Potential.
EFP fragments and positions.""",
    "FFIELD": """$FFIELD group - Force Field options.
Molecular mechanics parameters.""",
    "SURFACE": """$SURFACE group - Potential energy surface scan.
Coordinate scanning options.""",
    "TRUDGE": """$TRUDGE group - Trudge optimization.
Simplex optimization method.""",
    "MCSCF": """$MCSCF group - Multiconfigurational SCF.
CASSCF and RASSCF calculations.""",
    "CI": """$CI group - Configuration Interaction.
Full CI or selected CI calculations.""",
    "DRT": """$DRT group - Determinant Reference Table.
CI active space specification.""",
}

GAMESS_KEYWORDS = {
    "CONTRL": {
        "RUNTYP": {
            "doc": """Type of calculation to perform.
Values: ENERGY, GRADIENT, HESSIAN, OPTIMIZE, SADPOINT, IRC, DRC,
        SURFACE, GLOBOP, OPTFMO, MEX, NAINTERP, NACOUPL, TRANSITN.
Default: ENERGY""",
            "values": [
                "ENERGY",
                "GRADIENT",
                "HESSIAN",
                "OPTIMIZE",
                "SADPOINT",
                "IRC",
                "DRC",
                "SURFACE",
                "GLOBOP",
            ],
        },
        "SCFTYP": {
            "doc": """Type of SCF wavefunction.
Values: RHF, UHF, ROHF, MCSCF, NONE.
Default: RHF""",
            "values": ["RHF", "UHF", "ROHF", "MCSCF", "NONE"],
        },
        "DFTTYP": {
            "doc": """DFT exchange-correlation functional.
Values: BLYP, B3LYP, PBE, PBE0, M06, M06L, etc.""",
            "values": [
                "BLYP",
                "B3LYP",
                "PBE",
                "PBE0",
                "M06",
                "M06L",
                "M062X",
                "M06HF",
                "B97D",
                "B97D3",
                "TPSS",
                "TPSSH",
            ],
        },
        "MPLEVL": {
            "doc": """Møller-Plesset perturbation theory level.
Values: 0 (no MP), 2 (MP2).
Default: 0""",
            "values": ["0", "2"],
        },
        "CCTYP": {
            "doc": """Coupled Cluster theory level.
Values: CCSD, CCSD(T), CR-CC(2,3), LR-CCSD(T), etc.
Default: none""",
            "values": ["CCSD", "CCSD(T)", "CR-CC(2,3)", "LR-CCSD(T)"],
        },
        "CITYP": {
            "doc": """CI calculation type.
Values: CIS, CISD, ALDET, ORMAS, FSOCI, GENCI.
Default: none""",
            "values": ["CIS", "CISD", "ALDET", "ORMAS", "FSOCI", "GENCI"],
        },
        "MULT": {
            "doc": """Spin multiplicity (2S+1).
Default: 1 (singlet)""",
            "values": ["1", "2", "3", "4", "5", "6"],
        },
        "ICHARG": {
            "doc": """Molecular charge.
Default: 0 (neutral)""",
            "values": [],
        },
        "MAXIT": {
            "doc": """Maximum SCF iterations.
Default: 30""",
            "values": [],
        },
        "COORD": {
            "doc": """Coordinate system.
Values: UNIQUE, HINT, CART, FRAGONLY.
Default: UNIQUE""",
            "values": ["UNIQUE", "HINT", "CART", "FRAGONLY"],
        },
        "UNITS": {
            "doc": """Units for geometry.
Values: ANGS (Angstroms), BOHR.
Default: ANGS""",
            "values": ["ANGS", "BOHR"],
        },
        "ISPHER": {
            "doc": """Spherical harmonic basis functions.
Values: -1 (all Cartesian), 0 (as input), 1 (all spherical).
Default: 0""",
            "values": ["-1", "0", "1"],
        },
        "NOSYM": {
            "doc": """Disable symmetry.
Values: .TRUE. (no symmetry), .FALSE. (use symmetry).
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "EXETYP": {
            "doc": """Execution type.
Values: RUN (normal run), CHECK (input check only).
Default: RUN""",
            "values": ["RUN", "CHECK"],
        },
        "INTTYP": {
            "doc": """Integral evaluation type.
Values: POPLE, HONDO, ERIC, ARI.
Default: POPLE""",
            "values": ["POPLE", "HONDO", "ERIC", "ARI"],
        },
    },
    "SYSTEM": {
        "MWORDS": {
            "doc": """Memory in million words (8 bytes each).
Default: 1""",
            "values": [],
        },
        "MEMDDI": {
            "doc": """Memory for distributed data (in words).
Default: 0""",
            "values": [],
        },
        "TIMLIM": {
            "doc": """Time limit in minutes.
Default: 10000""",
            "values": [],
        },
    },
    "BASIS": {
        "GBASIS": {
            "doc": """Gaussian basis set name.
Values: MINI, MIDI, STO, N21, N31, N311, D95, D95V, CC-PVDZ, CC-PVTZ,
        CC-PVQZ, CC-PV5Z, CC-PV6Z, AUG-CC-PVDZ, etc.""",
            "values": [
                "MINI",
                "MIDI",
                "STO",
                "N21",
                "N31",
                "N311",
                "D95",
                "D95V",
                "CC-PVDZ",
                "CC-PVTZ",
                "CC-PVQZ",
                "CC-PV5Z",
                "AUG-CC-PVDZ",
            ],
        },
        "NGAUSS": {
            "doc": """Number of Gaussian primitives (for Pople basis sets).
Values: 2, 3, 4, 5, 6""",
            "values": ["2", "3", "4", "5", "6"],
        },
        "NDFUNC": {
            "doc": """Number of d functions on heavy atoms.
Default: 0""",
            "values": [],
        },
        "NFFUNC": {
            "doc": """Number of f functions on heavy atoms.
Default: 0""",
            "values": [],
        },
        "DIFFSP": {
            "doc": """Add diffuse functions on heavy atoms.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "DIFFS": {
            "doc": """Add diffuse functions on hydrogens.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
    },
    "SCF": {
        "DIRSCF": {
            "doc": """Direct SCF (recompute integrals).
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "DIIS": {
            "doc": """Use DIIS convergence acceleration.
Values: .TRUE., .FALSE.
Default: .TRUE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "SOSCF": {
            "doc": """Use SOSCF (second-order SCF).
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "CONV": {
            "doc": """SCF convergence criterion (energy change).
Default: 1.0E-05""",
            "values": [],
        },
        "ETHRSH": {
            "doc": """Energy threshold for integral screening.
Default: 0.5""",
            "values": [],
        },
    },
    "DFT": {
        "METHOD": {
            "doc": """DFT grid method.
Values: GRID, GRIDFREE.
Default: GRID""",
            "values": ["GRID", "GRIDFREE"],
        },
        "NRAD": {
            "doc": """Number of radial grid points.
Default: 96""",
            "values": [],
        },
        "NLEB": {
            "doc": """Number of Lebedev angular points.
Values: 302, 434, 590, 770, 974, 1202, 1454, 1730, 2030, 2354, 2702, 3074, 3470, 3890.
Default: 302""",
            "values": [
                "302",
                "434",
                "590",
                "770",
                "974",
                "1202",
                "1454",
                "1730",
                "2030",
                "2354",
                "2702",
                "3074",
                "3470",
                "3890",
            ],
        },
        "DFTTHR": {
            "doc": """DFT grid pruning threshold.
Default: 1.0E-11""",
            "values": [],
        },
    },
    "STATPT": {
        "METHOD": {
            "doc": """Optimization method.
Values: RFO (Rational Function Optimization), QA (Quadratic Approximation),
        GDIIS, CONOPT, SCHLEGEL, EF.
Default: RFO""",
            "values": ["RFO", "QA", "GDIIS", "CONOPT", "SCHLEGEL", "EF"],
        },
        "OPTTOL": {
            "doc": """Geometry convergence tolerance (max gradient).
Default: 0.0001""",
            "values": [],
        },
        "NSTEP": {
            "doc": """Maximum number of optimization steps.
Default: 50""",
            "values": [],
        },
        "HESS": {
            "doc": """Hessian for optimization.
Values: READ, CALC, GUESS.
Default: GUESS""",
            "values": ["READ", "CALC", "GUESS"],
        },
        "HSSEND": {
            "doc": """Calculate Hessian at optimized geometry.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "IFOLOW": {
            "doc": """Follow Hessian mode (for saddle points).
Default: 0""",
            "values": [],
        },
    },
    "FORCE": {
        "METHOD": {
            "doc": """Method for force constants.
Values: SEMIANALYTIC, ANALYTIC, FULLYNUMERIC, FULLNUM.
Default: ANALYTIC""",
            "values": ["SEMIANALYTIC", "ANALYTIC", "FULLYNUMERIC", "FULLNUM"],
        },
        "VIBANL": {
            "doc": """Perform vibrational analysis.
Values: .TRUE., .FALSE.
Default: .TRUE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "PURIFY": {
            "doc": """Purify rotations/translations from vibrations.
Values: .TRUE., .FALSE.
Default: .TRUE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "TEMP": {
            "doc": """Temperature for thermochemistry (K).
Default: 298.15""",
            "values": [],
        },
        "PRES": {
            "doc": """Pressure for thermochemistry (atm).
Default: 1.0""",
            "values": [],
        },
        "PROJCT": {
            "doc": """Project out rotations/translations.
Values: .TRUE., .FALSE.
Default: .TRUE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
    },
}

# Additional GAMESS groups for comprehensive support
ADDITIONAL_GROUPS = {
    "RELWFN": """$RELWFN group - Relativistic wavefunction options.
DKH, ZORA, and other relativistic corrections.""",
    "TAMC": """$TAMC group - Transition state and minimum energy path.
Transition state search options.""",
    "MOROKM": """$MOROKM group - Morokuma energy decomposition.
Interaction energy decomposition analysis.""",
    "EQUIL": """$EQUIL group - Equilibrium geometry search.
Equilibrium structure optimization.""",
    "DECOMP": """$DECOMP group - Energy decomposition analysis.
Decomposition of interaction energies.""",
    "MOLCAS": """$MOLCAS group - MOLCAS interface options.
Interface to MOLCAS program.""",
    "CIM": """$CIM group - Cluster-in-molecule method.
Local correlation methods.""",
    "LOCAL": """$LOCAL group - Localized orbital options.
Orbital localization methods.""",
    "PMO": """$PMO group - Pipek-Mezey localization.
Orbital localization criteria.""",
    "GEM": """$GEM group - Gaussian electrostatic model.
GEM fragment calculations.""",
    "ELMOM": """$ELMOM group - Electric multipole moments.
Multipole moment calculations.""",
    "AIMPAC": """$AIMPAC group - AIM analysis options.
Atoms in molecules analysis.""",
    "FRIEND": """$FRIEND group - Interface to other programs.
External program interfaces.""",
    "NBO": """$NBO group - Natural Bond Orbital analysis.
NBO analysis options.""",
    "MAKVEC": """$MAKVEC group - Vector generation options.
Molecular orbital vector generation.""",
    "RAMAN": """$RAMAN group - Raman spectroscopy options.
Raman intensity calculations.""",
    "INPUT": """$INPUT group - Input file options.
Input processing controls.""",
    "PUNCH": """$PUNCH group - Punch file options.
Output file generation.""",
    "BENCH": """$BENCH group - Benchmarking options.
Performance benchmarking controls.""",
    "PARALLEL": """$PARALLEL group - Parallel execution options.
Distributed computing settings.""",
    "ACCURACY": """$ACCURACY group - Accuracy control options.
Numerical precision settings.""",
}

# Update GAMESS_GROUPS with additional groups
GAMESS_GROUPS.update(ADDITIONAL_GROUPS)

# Additional keywords for existing groups
ADDITIONAL_KEYWORDS = {
    "CONTRL": {
        "TDDFT": {
            "doc": """Enable TDDFT calculation.
Values: NONE, EXCITE (excited states).
Default: NONE""",
            "values": ["NONE", "EXCITE"],
        },
        "EFP": {
            "doc": """Enable Effective Fragment Potential.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "FRAGNAME": {
            "doc": """Fragment name for EFP calculations.
Specifies the fragment library name.""",
            "values": [],
        },
        "PROPS": {
            "doc": """Property calculation flag.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
    },
    "SYSTEM": {
        "PARALL": {
            "doc": """Parallel execution flag.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "KDIAG": {
            "doc": """Number of parallel tasks for diagnostics.
Default: 0""",
            "values": [],
        },
    },
    "BASIS": {
        "EXTFIL": {
            "doc": """Read basis from external file.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "BASNAM": {
            "doc": """Basis set file name.
External basis set library name.""",
            "values": [],
        },
    },
    "SCF": {
        "FSTATE": {
            "doc": """Target SCF state for MCSCF.
State number for optimization.""",
            "values": [],
        },
        "NWORD": {
            "doc": """Memory for SCF in words.
Default: 0 (auto)""",
            "values": [],
        },
    },
    "DFT": {
        "AUTHOR": {
            "doc": """DFT functional author specification.
Values: BECKE, PBE, B3LYP, etc.""",
            "values": ["BECKE", "PBE", "B3LYP", "M06", "M06L"],
        },
        "LAMBDA": {
            "doc": """Range-separation parameter.
For long-range corrected functionals.""",
            "values": [],
        },
    },
    "STATPT": {
        "STPT": {
            "doc": """Starting point for optimization.
Values: .TRUE. (restart), .FALSE. (fresh).
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "TRMAX": {
            "doc": """Maximum trust radius.
Default: 0.2""",
            "values": [],
        },
        "TRMIN": {
            "doc": """Minimum trust radius.
Default: 0.0""",
            "values": [],
        },
    },
    "FORCE": {
        "SIDE": {
            "doc": """Projection side for vibrations.
Values: +1, -1.""",
            "values": ["+1", "-1"],
        },
        "SCLFAC": {
            "doc": """Scaling factor for frequencies.
Default: 1.0""",
            "values": [],
        },
        "ANHALG": {
            "doc": """Anharmonic analysis algorithm.
Values: 0, 1, 2.""",
            "values": ["0", "1", "2"],
        },
    },
    "MP2": {
        "MP2PRP": {
            "doc": """MP2 property calculation.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "NACORE": {
            "doc": """Number of core orbitals to freeze.
Default: 0""",
            "values": [],
        },
    },
    "CC": {
        "NCORE": {
            "doc": """Number of core orbitals to freeze.
Default: 0""",
            "values": [],
        },
        "MAXCC": {
            "doc": """Maximum CC iterations.
Default: 50""",
            "values": [],
        },
        "CCCONV": {
            "doc": """CC convergence criterion.
Default: 1.0E-06""",
            "values": [],
        },
    },
}

# Update GAMESS_KEYWORDS with additional keywords
for group, keywords in ADDITIONAL_KEYWORDS.items():
    if group in GAMESS_KEYWORDS:
        GAMESS_KEYWORDS[group].update(keywords)
    else:
        GAMESS_KEYWORDS[group] = keywords

# Additional keywords for commonly used groups missing definitions
MORE_KEYWORDS = {
    "GUESS": {
        "GUESS": {
            "doc": """Type of initial guess.
Values: HUCKEL, CORE, MOREAD, SKIP, DENSITY, HCORE, NORNDM, DAMP, etc.
Default: HUCKEL""",
            "values": ["HUCKEL", "CORE", "MOREAD", "SKIP", "DENSITY", "HCORE", "NORNDM", "DAMP"],
        },
        "NORB": {
            "doc": """Number of orbitals to read for MOREAD guess.
Default: 0 (all)""",
            "values": [],
        },
        "PRTMO": {
            "doc": """Print MOs in initial guess.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "MIX": {
            "doc": """Mix HOMO and LUMO for broken symmetry.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
    },
    "CIS": {
        "NSTATE": {
            "doc": """Number of excited states to compute.
Default: 1""",
            "values": [],
        },
        "IROOT": {
            "doc": """State of interest for properties.
Default: 1""",
            "values": [],
        },
        "MULT": {
            "doc": """Multiplicity of excited states.
Default: same as ground state""",
            "values": ["1", "3", "SINGLET", "TRIPLET"],
        },
        "DIAG": {
            "doc": """Diagonalization method.
Values: FULL, DAVIDSON.
Default: DAVIDSON""",
            "values": ["FULL", "DAVIDSON"],
        },
    },
    "TDDFT": {
        "NSTATE": {
            "doc": """Number of excited states to compute.
Default: 1""",
            "values": [],
        },
        "IROOT": {
            "doc": """State of interest for properties.
Default: 1""",
            "values": [],
        },
        "MULT": {
            "doc": """Multiplicity of excited states.
Default: same as ground state""",
            "values": ["1", "3", "SINGLET", "TRIPLET"],
        },
        "MAXVEC": {
            "doc": """Maximum number of expansion vectors.
Default: 100""",
            "values": [],
        },
        "CVG": {
            "doc": """Convergence criterion for excitation energies.
Default: 1.0E-05""",
            "values": [],
        },
    },
    "HESSIAN": {
        "METHOD": {
            "doc": """Method for computing Hessian.
Values: ANALYTIC, SEMIANALYTIC, FULLYANALYTIC, NUMERIC.
Default: ANALYTIC""",
            "values": ["ANALYTIC", "SEMIANALYTIC", "FULLYANALYTIC", "NUMERIC"],
        },
        "PRTIFC": {
            "doc": """Print internal force constants.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "VIBANL": {
            "doc": """Perform vibrational analysis.
Values: .TRUE., .FALSE.
Default: .TRUE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
    },
    "IRC": {
        "METHOD": {
            "doc": """IRC following method.
Values: RFO, TRUST, EULER, LQA.
Default: RFO""",
            "values": ["RFO", "TRUST", "EULER", "LQA"],
        },
        "FORWRD": {
            "doc": """Follow IRC forward from saddle point.
Values: .TRUE., .FALSE.
Default: .TRUE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "NPOINT": {
            "doc": """Number of IRC points to compute.
Default: 100""",
            "values": [],
        },
        "STRIDE": {
            "doc": """IRC step size (in amu^(1/2) * Bohr).
Default: 0.1""",
            "values": [],
        },
    },
    "ECP": {
        "ECP": {
            "doc": """Effective Core Potential type.
Values: READ, SBKJC, HW, LANL2DZ.
Default: READ""",
            "values": ["READ", "SBKJC", "HW", "LANL2D2", "LANL2DZ"],
        },
        "PTRAD": {
            "doc": """Print ECP radial potentials.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
    },
    "PCM": {
        "SOLVNT": {
            "doc": """Solvent name.
Values: WATER, CH2CL2, THF, ACETONE, ETC.
Default: WATER""",
            "values": [
                "WATER",
                "CH2CL2",
                "THF",
                "ACETONE",
                "DMSO",
                "DMF",
                "ACETONITRILE",
                "METHANOL",
                "ETHANOL",
            ],
        },
        "ICAV": {
            "doc": """Cavity type.
Values: 0 (GePol), 1 (UFF), 2 (Pierotti).
Default: 0""",
            "values": ["0", "1", "2"],
        },
        "EPS": {
            "doc": """Dielectric constant (overrides solvent).
Default: from solvent""",
            "values": [],
        },
        "RSOLV": {
            "doc": """Probe radius (Angstroms).
Default: 1.0 (water)""",
            "values": [],
        },
    },
    "COSM": {
        "EPS": {
            "doc": """Dielectric constant.
Default: infinity (conductor)""",
            "values": [],
        },
        "RSOLV": {
            "doc": """Probe radius (Angstroms).
Default: 1.3""",
            "values": [],
        },
        "DISPT": {
            "doc": """Dispersion correction type.
Values: 0 (none), 1 (DFT-D3).
Default: 0""",
            "values": ["0", "1"],
        },
    },
    "MCSCF": {
        "CISTEP": {
            "doc": """CI step method.
Values: FULLNR, ALDET, ORMAS, GENCI, FSOCI.
Default: FULLNR""",
            "values": ["FULLNR", "ALDET", "ORMAS", "GENCI", "FSOCI"],
        },
        "MAXIT": {
            "doc": """Maximum MCSCF iterations.
Default: 100""",
            "values": [],
        },
        "ACURCY": {
            "doc": """MCSCF convergence criterion.
Default: 1.0E-05""",
            "values": [],
        },
        "FULLNR": {
            "doc": """Use full NR method (for small active spaces).
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
    },
    "VIB": {
        "SCLFAC": {
            "doc": """Scale factor for frequencies.
Default: 1.0""",
            "values": [],
        },
        "MODES": {
            "doc": """Modes to print/analyze.
Default: ALL""",
            "values": ["ALL"],
        },
    },
    "DRC": {
        "TINIT": {
            "doc": """Initial temperature (K).
Default: 298.15""",
            "values": [],
        },
        "NSTEP": {
            "doc": """Maximum number of DRC steps.
Default: 1000""",
            "values": [],
        },
        "DELTAT": {
            "doc": """Time step (femtoseconds).
Default: 0.5""",
            "values": [],
        },
    },
    "SURFACE": {
        "NVIB": {
            "doc": """Number of vibrational modes.
Required for surface scan.""",
            "values": [],
        },
        "NSURF": {
            "doc": """Number of surface points.
Default: 10""",
            "values": [],
        },
        "IVEC": {
            "doc": """Vibrational mode to follow.
Default: 1""",
            "values": [],
        },
    },
    "NBO": {
        "NBO": {
            "doc": """NBO analysis level.
Values: NONE, DENSITY, POPULATION, FULL.
Default: NONE""",
            "values": ["NONE", "DENSITY", "POPULATION", "FULL"],
        },
        "NPA": {
            "doc": """Natural Population Analysis.
Values: .TRUE., .FALSE.
Default: .FALSE.""",
            "values": [".TRUE.", ".FALSE.", "1", "0"],
        },
        "NBOKEY": {
            "doc": """NBO keylist commands.
See NBO manual for options.""",
            "values": [],
        },
    },
    "SMD": {
        "SOLVNT": {
            "doc": """Solvent name for SMD.
Values: WATER, ETHANOL, HEXANE, BENZENE, ETC.
Default: WATER""",
            "values": [
                "WATER",
                "ETHANOL",
                "HEXANE",
                "BENZENE",
                "TOLUENE",
                "CH2CL2",
                "THF",
                "ACETONE",
            ],
        },
        "ICAV": {
            "doc": """Cavity type.
Values: 0 (SMD), 1 (custom).
Default: 0""",
            "values": ["0", "1"],
        },
    },
    "CI": {
        "CITYP": {
            "doc": """CI calculation type.
Values: CIS, CISD, ALDET, ORMAS, FSOCI, GENCI.
Default: CIS""",
            "values": ["CIS", "CISD", "ALDET", "ORMAS", "FSOCI", "GENCI"],
        },
        "NFZC": {
            "doc": """Number of frozen core orbitals.
Default: 0""",
            "values": [],
        },
        "NDOC": {
            "doc": """Number of doubly occupied orbitals in active space.
Required for ALDET/ORMAS.""",
            "values": [],
        },
        "NALP": {
            "doc": """Number of active orbitals (ALDET/ORMAS).
Required for ALDET/ORMAS.""",
            "values": [],
        },
    },
}

# Update with the new keywords
for group, keywords in MORE_KEYWORDS.items():
    if group in GAMESS_KEYWORDS:
        GAMESS_KEYWORDS[group].update(keywords)
    else:
        GAMESS_KEYWORDS[group] = keywords
