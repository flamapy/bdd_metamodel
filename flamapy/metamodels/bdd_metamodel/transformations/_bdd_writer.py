from typing import Any

from flamapy.core.transformations import ModelToText
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class BDDWriter(ModelToText):

    def __init__(self, path: str, source_model: BDDModel) -> None:
        self.path: str = path
        self.source_model: BDDModel = source_model
        self._roots: bool = True

    def set_roots(self, roots: bool) -> None:
        self._roots = roots

    def transform(self) -> str:
        if not self._roots:
            try:
                self.source_model.bdd.dump(filename=self.path, 
                                           filetype=self.get_destination_extension())
            except Exception:
                roots = [self.source_model.root]
        else:
            roots = [self.source_model.root]
            self.source_model.bdd.dump(filename=self.path,
                                       roots=roots,
                                       filetype=self.get_destination_extension())
        return ''
