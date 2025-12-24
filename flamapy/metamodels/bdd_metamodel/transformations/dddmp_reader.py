import tempfile
import pathlib

from flamapy.core.transformations import TextToModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class DDDMPReader(TextToModel):
    @staticmethod
    def get_source_extension() -> str:
        return "dddmp"

    def __init__(self, path: str) -> None:
        self.path: str = path

    def transform(self) -> BDDModel:
        vars = get_vars_from_dddmp(self.path)
        path = dddmp_v3_to_v2(self.path)
        bdd_model = BDDModel.load_bdd(path, vars)
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

        # Add '.varnames' field
        index, line = next(
            (index, line) for index, line in enumerate(lines) if ".varnames" in line
        )
        lines.pop(index)

    with tempfile.NamedTemporaryFile(mode="w",
                                     suffix='.dddmp',
                                     encoding="utf8",
                                     delete=False) as temp_file:
        temp_file.writelines(lines)
        temp_file_path = temp_file.name
        return temp_file_path


def get_vars_from_dddmp(filepath: str) -> list[str]:
    """Extract variable names from a DDDMP file."""
    with open(filepath, "r", encoding="utf8") as file:
        lines = file.readlines()
        var_line = next((line for line in lines if ".orderedvarnames" in line), None)
        if var_line is not None:
            vars = var_line.split()[1:]
            return vars
    return []
