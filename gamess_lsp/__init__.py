"""GAMESS Language Server Protocol implementation."""

__version__ = "0.1.0"

from .parser import GamessParser, Group, GroupParameter
from .groups import (
    GAMESS_GROUPS,
    GroupDoc,
    ParameterDoc,
    get_all_group_names,
    get_group_documentation,
    get_group_parameters,
    get_parameter_documentation,
)
from .data_parser import DataGroupParser, Atom, DataGroupInfo
from .diagnostics import GamessDiagnostics
from .server import GamessLanguageServer
from .document_symbols import DocumentSymbolProvider
from .folding import FoldingRangeProvider
from .snippets import (
    Snippet,
    GAMESS_SNIPPETS,
    get_snippet,
    get_all_snippets,
)

__all__ = [
    "__version__",
    "GamessParser",
    "Group",
    "GroupParameter",
    "GAMESS_GROUPS",
    "GroupDoc",
    "ParameterDoc",
    "get_all_group_names",
    "get_group_documentation",
    "get_group_parameters",
    "get_parameter_documentation",
    "DataGroupParser",
    "Atom",
    "DataGroupInfo",
    "GamessDiagnostics",
    "GamessLanguageServer",
    "DocumentSymbolProvider",
    "FoldingRangeProvider",
    "Snippet",
    "GAMESS_SNIPPETS",
    "get_snippet",
    "get_all_snippets",
]
