import tempfile
import pathlib
from typing import Any, Optional

from flamapy.core.exceptions import FlamaException
from flamapy.core.transformations import TextToModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.models.bdd_model import (
    DD_BACKEND,
    ensure_recursion_limit,
)


class DDDMPReader(TextToModel):
    """Read a BDD dumped in the text DDDMP format (CUDD's dddmp library).

    With dd built against CUDD the file is loaded by CUDD itself. With the pure-Python dd
    engine the file is parsed here and the BDD is rebuilt node by node, so DDDMP files (e.g.
    produced by CUDD-based tools such as Logic2BDD) can be read on every platform.
    Both DDDMP 2.0 and 3.0 (which adds a `.varnames` header line) are accepted.
    """

    @staticmethod
    def get_source_extension() -> str:
        return "dddmp"

    def __init__(self, path: str) -> None:
        self.path: str = path

    def transform(self) -> BDDModel:
        if DD_BACKEND != "cudd":
            return load_dddmp(self.path)
        vars = get_vars_from_dddmp(self.path)
        path = dddmp_v3_to_v2(self.path)
        try:
            bdd_model = BDDModel.load_bdd(path, vars)
        finally:
            if path != self.path:
                pathlib.Path(path).unlink()  # Remove temporary file
        return bdd_model


def dddmp_v3_to_v2(filepath: str) -> str:
    """Convert the file with the BDD dump in format dddmp version 3 to version 2
    (for compatibility).

    The difference between versions 2.0 and 3.0 is the addition of the '.varnames' field.
    """
    with open(filepath, "r", encoding="utf8") as file:
        lines = file.readlines()
    # Change version from 3.0 to 2.0
    index_line = next(
        ((index, line) for index, line in enumerate(lines) if ".ver DDDMP-3.0" in line), None
    )
    if index_line is None:
        return filepath  # No conversion needed
    index, line = index_line
    lines[index] = line.replace("3.0", "2.0")
    # Remove the '.varnames' field (DDDMP 3.0 only), if present
    lines = [line for line in lines if not line.startswith(".varnames")]

    with tempfile.NamedTemporaryFile(mode="w",
                                     suffix='.dddmp',
                                     encoding="utf8",
                                     delete=False) as temp_file:
        temp_file.writelines(lines)
        return temp_file.name


def get_vars_from_dddmp(filepath: str) -> list[str]:
    """Extract variable names from a DDDMP file."""
    with open(filepath, "r", encoding="utf8") as file:
        lines = file.readlines()
        var_line = next((line for line in lines if ".orderedvarnames" in line), None)
        if var_line is not None:
            vars = var_line.split()[1:]
            return vars
    return []


def _parse_header(lines: list[str]) -> tuple[dict[str, list[str]], int]:
    """Return the header fields ('.key' -> values) and the index of the first node line."""
    header: dict[str, list[str]] = {}
    for index, line in enumerate(lines):
        fields = line.split()
        if not fields:
            continue
        if fields[0] == ".nodes":
            return header, index + 1
        if fields[0].startswith("."):
            header[fields[0]] = fields[1:]
    raise FlamaException("Invalid DDDMP file: missing '.nodes' section.")


def _variable_levels(header: dict[str, list[str]]) -> list[str]:
    """All variable names, top level first."""
    if ".orderedvarnames" in header:
        return header[".orderedvarnames"]
    support = header.get(".suppvarnames")
    permids = header.get(".permids")
    if support is None or permids is None:
        raise FlamaException("Invalid DDDMP file: variable names are missing.")
    by_level = sorted(zip((int(p) for p in permids), support))
    return [name for _, name in by_level]


# Values of the DDDMP '.varinfo' header: what the 'info' field of a node line holds.
VARINFO_IDS = 0
VARINFO_PERMIDS = 1
VARINFO_NAMES = 3


def _info_to_name(header: dict[str, list[str]]) -> Optional[dict[str, str]]:
    """Map the 'info' field of the node lines to the file's variable names (None: the field
    is the name)."""
    varinfo = int(header.get(".varinfo", [str(VARINFO_NAMES)])[0])
    support = header.get(".suppvarnames", [])
    if varinfo == VARINFO_IDS:
        return dict(zip(header.get(".ids", []), support))
    if varinfo == VARINFO_PERMIDS:
        return dict(zip(header.get(".permids", []), support))
    if varinfo == VARINFO_NAMES:
        return None
    raise FlamaException(f"DDDMP files with '.varinfo {varinfo}' are not supported.")


def load_dddmp(filepath: str, names: Optional[dict[str, str]] = None) -> BDDModel:
    """Load a text DDDMP file into a new BDDModel, with any dd engine (see load_dddmp_text)."""
    with open(filepath, "r", encoding="utf8") as file:
        return load_dddmp_text(file.read(), names)


def load_dddmp_text(text: str, names: Optional[dict[str, str]] = None) -> BDDModel:
    """Load a BDD in text DDDMP format into a new BDDModel, with any dd engine.

    Node lines read `id info level then else`, children before parents; only `else` edges
    and roots can be complemented (negative ids). Variables are declared in the order of
    `.orderedvarnames` so that the BDD keeps the levels of the file. `names` renames the
    variables of the file (file name -> variable name).
    """
    lines = text.splitlines()
    header, first_node = _parse_header(lines)
    if header.get(".mode", ["A"])[0] != "A":
        raise FlamaException("Only text DDDMP files (.mode A) are supported.")
    file_variables = _variable_levels(header)
    rename = names or {}
    variables = [rename.get(var, var) for var in file_variables]
    info_names = _info_to_name(header)
    if info_names is None:
        info_names = {var: rename.get(var, var) for var in file_variables}
    else:
        info_names = {info: rename.get(var, var) for info, var in info_names.items()}

    bdd_model = BDDModel()
    bdd = bdd_model.bdd
    ensure_recursion_limit(len(variables))
    bdd.configure(reordering=False)
    for var in variables:
        bdd.declare(var)

    nodes: dict[int, Any] = {}
    for line in lines[first_node:]:
        fields = line.split()
        if not fields:
            continue
        if fields[0] == ".end":
            break
        node_id, info, then_id, else_id = int(fields[0]), fields[1], int(fields[3]), \
            int(fields[4])
        if info == "T":
            nodes[node_id] = bdd.true
            continue
        name = info_names[info]
        high = nodes[then_id]
        low = nodes[abs(else_id)]
        if else_id < 0:
            low = ~low
        nodes[node_id] = bdd.ite(bdd.var(name), high, low)

    root_ids = [int(root) for root in header.get(".rootids", [])]
    if not root_ids:
        raise FlamaException("Invalid DDDMP file: no root.")
    root = nodes[abs(root_ids[0])]
    bdd_model.root = ~root if root_ids[0] < 0 else root
    bdd_model.vars_order = sorted(variables, key=bdd.level_of_var)
    bdd_model.vars_features = {var: var for var in bdd_model.vars_order}
    bdd_model.features_vars = {var: var for var in bdd_model.vars_order}
    return bdd_model
