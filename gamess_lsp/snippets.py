"""GAMESS LSP Code Snippets."""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Snippet:
    """A code snippet."""
    prefix: str
    description: str
    body: List[str]


# GAMESS input file snippets
GAMESS_SNIPPETS: Dict[str, Snippet] = {
    "scf_calculation": Snippet(
        prefix="scf",
        description="Single Point SCF Calculation",
        body=[
            "$CONTRL SCFTYP=${1|RHF,UHF,ROHF,GVB,MCSCF|} RUNTYP=ENERGY $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$BASIS GBASIS=${2|N31,CC-PVDZ,CC-PVTZ,STO|} ${3:NGAUSS=6} $END",
            "$GUESS GUESS=${4|HUCKEL,HCORE|} $END",
            "$DATA",
            "${5:Title}",
            "C1",
            "${6:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
    
    "geometry_optimization": Snippet(
        prefix="opt",
        description="Geometry Optimization",
        body=[
            "$CONTRL SCFTYP=${1|RHF,UHF,ROHF|} RUNTYP=OPTIMIZE $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$BASIS GBASIS=${2|N31,CC-PVDZ,CC-PVTZ|} ${3:NGAUSS=6} $END",
            "$STATPT NSTEP=${4:100} OPTTOL=0.0001 $END",
            "$GUESS GUESS=HUCKEL $END",
            "$DATA",
            "${5:Title}",
            "C1",
            "${6:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
    
    "frequency_calculation": Snippet(
        prefix="freq",
        description="Frequency Calculation",
        body=[
            "$CONTRL SCFTYP=${1|RHF,UHF,ROHF|} RUNTYP=HESSIAN $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$BASIS GBASIS=${2|N31,CC-PVDZ,CC-PVTZ|} NGAUSS=6 $END",
            "$FORCE METHOD=ANALYTIC $END",
            "$DATA",
            "${3:Title}",
            "C1",
            "${4:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
    
    "opt_freq": Snippet(
        prefix="optfreq",
        description="Optimization + Frequency",
        body=[
            "$CONTRL SCFTYP=${1|RHF,UHF,ROHF|} RUNTYP=OPTIMIZE $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$BASIS GBASIS=${2|N31,CC-PVDZ,CC-PVTZ|} NGAUSS=6 $END",
            "$STATPT NSTEP=${3:100} OPTTOL=0.0001 HSSEND=.TRUE. $END",
            "$GUESS GUESS=HUCKEL $END",
            "$DATA",
            "${4:Title}",
            "C1",
            "${5:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
    
    "dft_calculation": Snippet(
        prefix="dft",
        description="DFT Calculation",
        body=[
            "$CONTRL SCFTYP=${1|RHF,UHF,ROHF|} RUNTYP=ENERGY DFTTYP=${2|B3LYP,PBE,PBE0,M06,M06-2X|} $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$DFT METHOD=${2} $END",
            "$BASIS GBASIS=${3|N31,CC-PVDZ,CC-PVTZ|} NGAUSS=6 $END",
            "$DATA",
            "${4:Title}",
            "C1",
            "${5:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
    
    "mp2_calculation": Snippet(
        prefix="mp2",
        description="MP2 Calculation",
        body=[
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY MPLEVL=2 $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$BASIS GBASIS=${1|CC-PVDZ,CC-PVTZ,CC-PVQZ|} $END",
            "$DATA",
            "${2:Title}",
            "C1",
            "${3:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
    
    "td_dft": Snippet(
        prefix="tddft",
        description="Time-Dependent DFT",
        body=[
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY DFTTYP=${1|B3LYP,PBE,PBE0|} TDDFT=.TRUE. $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$DFT TDDFT=.TRUE. NSTATE=${2:5} ISTATE=${3:1} $END",
            "$BASIS GBASIS=${4|CC-PVDZ,CC-PVTZ|} $END",
            "$DATA",
            "${5:Title}",
            "C1",
            "${6:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
    
    "data_group": Snippet(
        prefix="data",
        description="$DATA Group Template",
        body=[
            "$DATA",
            "${1:Title}",
            "${2|C1,CS,CI,C2,C2V,C2H,D2,D2H|}",
            "${3:Atom} ${4:6.0} ${5:0.0} ${6:0.0} ${7:0.0}",
            "$END"
        ]
    ),
    
    "control_group": Snippet(
        prefix="contrl",
        description="$CONTRL Group",
        body=[
            "$CONTRL",
            "   SCFTYP=${1|RHF,UHF,ROHF,GVB,MCSCF|}",
            "   RUNTYP=${2|ENERGY,OPTIMIZE,HESSIAN,GRADIENT|}",
            "   EXETYP=${3|RUN,CHECK|}",
            "   MAXIT=${4:50}",
            "   MULT=${5:1}",
            "   ICHARG=${6:0}",
            "$END"
        ]
    ),
    
    "basis_group": Snippet(
        prefix="basis",
        description="$BASIS Group",
        body=[
            "$BASIS",
            "   GBASIS=${1|N31,CC-PVDZ,CC-PVTZ,CC-PVQZ,STO|}",
            "   NGAUSS=${2|3,4,5,6|}",
            "   NDFUNC=${3:0}",
            "   NPFUNC=${4:0}",
            "$END"
        ]
    ),
    
    "scf_group": Snippet(
        prefix="scfgroup",
        description="$SCF Group",
        body=[
            "$SCF",
            "   CONV=${1:1.0E-05}",
            "   DIIS=${2|.TRUE.,.FALSE.|}",
            "   SOSCF=${3|.FALSE.,.TRUE.|}",
            "$END"
        ]
    ),
    
    "statpt_group": Snippet(
        prefix="statpt",
        description="$STATPT Group",
        body=[
            "$STATPT",
            "   NSTEP=${1:100}",
            "   OPTTOL=${2:0.0001}",
            "   METHOD=${3|SCHLEGEL,NR,RFO,QA|}",
            "   HSSEND=${4|.FALSE.,.TRUE.|}",
            "$END"
        ]
    ),
    
    "cis_calculation": Snippet(
        prefix="cis",
        description="CIS/TDHF Calculation",
        body=[
            "$CONTRL SCFTYP=${1|RHF,UHF|} RUNTYP=ENERGY CITYP=CIS $END",
            "$SYSTEM MEMORY=1000000 $END",
            "$CIS NSTATE=${2:5} ISTATE=${3:1} MULT=${4|1,3|} $END",
            "$BASIS GBASIS=${5|CC-PVDZ,CC-PVTZ|} $END",
            "$DATA",
            "${6:Title}",
            "C1",
            "${7:C} 6.0 0.0 0.0 0.0",
            "$END"
        ]
    ),
}


def get_snippet(name: str) -> Optional[Snippet]:
    """Get a snippet by name."""
    return GAMESS_SNIPPETS.get(name)


def get_all_snippets() -> List[Snippet]:
    """Get all available snippets."""
    return list(GAMESS_SNIPPETS.values())
