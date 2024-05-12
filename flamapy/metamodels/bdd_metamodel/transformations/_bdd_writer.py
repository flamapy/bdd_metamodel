from typing import Any

from flamapy.core.transformations import ModelToText
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class BDDWriter(ModelToText):

    def __init__(self, path: str, source_model: BDDModel) -> None:
        self.path = path
        self.source_model = source_model
        self._roots = None

    def set_roots(self, roots: Any) -> None:
        self._roots = roots

    def transform(self) -> str:
        if self._roots is None:
            try:
                self.source_model.bdd.dump(filename=self.path, 
                                           filetype=self.get_destination_extension())
            except Exception:
                self._roots = [self.source_model.root]
        self.source_model.bdd.dump(filename=self.path, 
                                   roots=self._roots, 
                                   filetype=self.get_destination_extension())
        return ''
