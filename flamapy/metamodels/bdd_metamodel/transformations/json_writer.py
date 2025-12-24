import os
import tempfile
from typing import Optional

from flamapy.core.transformations import ModelToText
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class JSONWriter(ModelToText):

    @staticmethod
    def get_destination_extension() -> str:
        return "json"

    def __init__(self, path: str, source_model: BDDModel) -> None:
        self._path: Optional[str] = path
        self._source_model: BDDModel = source_model

    def transform(self) -> str:
        if self._path is None:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf8") as file:
                self._path = file.name
                result = write_to_file(self._source_model, self._path)
                self._path = None
        else:
            result = write_to_file(self._source_model, self._path)
        return result


def write_to_file(source_model: BDDModel, path: str) -> str:
    source_model.save_bdd(path, [source_model.root], JSONWriter.get_destination_extension())
    with open(path, "r", encoding="utf8") as file:
        result = os.linesep.join(file.readlines())
    return result
