import os
from typing import Optional
from enum import Enum

from dd.autoref import Function

from flamapy.core.transformations import ModelToText

from flamapy.metamodels.bdd_metamodel.models.bdd_model import BDDModel


class BDDDumpFormat(Enum):
    """Possible output format for representing a BDD."""
    DDDMP_V3 = 'dddmp'
    DDDMP_V2 = 'dddmp2'
    PDF = 'pdf'
    PNG = 'png'
    SVG = 'svg'


class BDDWriter(ModelToText):
    """Create the dump file representing the argument BDD.

    The format can be:
        - dddmp v3: `'.dddmp'` (default)
        - dddmp v2: `'.dddmp2'`
        - PDF: `'.pdf'`
        - PNG: `'.png'`
        - SVG: `'.svg'`
    """

    @staticmethod
    def get_destination_extension() -> str:
        return BDDDumpFormat.DDDMP_V3.value

    def __init__(self, path: str, source_model: BDDModel, roots: Optional[list[Function]] = None, 
                 output_format: BDDDumpFormat = BDDDumpFormat.DDDMP_V3) -> None:
        self._path = path
        self._source_model = source_model
        self._output_format = output_format
        self._roots = roots

    def set_format(self, output_format: BDDDumpFormat) -> None:
        self._output_format = output_format

    def set_roots(self, roots: list[Function]) -> None:
        self._roots = roots

    def transform(self) -> str:
        self._source_model.bdd.dump(filename=self._path, roots=self._roots)
        if self._output_format == BDDDumpFormat.DDDMP_V3:
            # Convert to dddmp format version 3.0 (adding the '.varnames' field)
            result = dddmp_v2_to_v3(self._path)
        elif self._output_format == BDDDumpFormat.DDDMP_V2:
            with open(self._path, 'r', encoding='utf-8') as file:
                result = os.linesep.join(file.readlines())
        else:
            result = ''
        return result


def dddmp_v2_to_v3(filepath: str) -> str:
    """Convert the file with the BDD dump in format dddmp version 2 to version 3.

    The difference between versions 2.0 and 3.0 is the addition of the '.varnames' field.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # Change version from 2.0 to 3.0
        i, line = next((i, l) for i, l in enumerate(lines) if '.ver DDDMP-2.0' in l)
        lines[i] = line.replace('2.0', '3.0')

        # Add '.varnames' field
        i, line = next((i, l) for i, l in enumerate(lines) if '.orderedvarnames' in l)
        lines.insert(i - 1, line.replace('.orderedvarnames', '.varnames'))

    with open(filepath, 'w', encoding='utf-8') as file:
        file.writelines(lines)
    return os.linesep.join(lines)
