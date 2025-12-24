import os
import tempfile
from typing import Optional

from flamapy.core.transformations import ModelToText
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class DDDMPWriter(ModelToText):

    @staticmethod
    def get_destination_extension() -> str:
        return "dddmp"

    def __init__(self, path: str, source_model: BDDModel) -> None:
        self._path: Optional[str] = path
        self._source_model: BDDModel = source_model

    def transform(self) -> str:
        if self._path is None:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf8") as file:
                self._source_model.save_bdd(file.name,
                                            [self._source_model.root],
                                            DDDMPWriter.get_destination_extension())
                result = dddmp_v2_to_v3(file.name)
        else:
            self._source_model.save_bdd(self._path,
                                        [self._source_model.root],
                                        DDDMPWriter.get_destination_extension())
            result = dddmp_v2_to_v3(self._path)
        return result


def dddmp_v2_to_v3(filepath: str) -> str:
    """Convert the file with the BDD dump in format dddmp version 2 to version 3.

    The difference between versions 2.0 and 3.0 is the addition of the '.varnames' field.
    """
    with open(filepath, "r", encoding="utf8") as file:
        lines = file.readlines()
        # Change version from 2.0 to 3.0
        index, line = next(
            (index, line) for index, line in enumerate(lines) if ".ver DDDMP-2.0" in line
        )
        lines[index] = line.replace("2.0", "3.0")

        # Add '.varnames' field
        index, line = next(
            (index, line) for index, line in enumerate(lines) if ".orderedvarnames" in line
        )
        lines.insert(index - 1, line.replace(".orderedvarnames", ".varnames"))

    with open(filepath, "w", encoding="utf8") as file:
        file.writelines(lines)
    return os.linesep.join(lines)
