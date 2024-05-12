import os
import tempfile

from flamapy.metamodels.bdd_metamodel.transformations._bdd_writer import BDDWriter


class DDDMPv2Writer(BDDWriter):

    @staticmethod
    def get_destination_extension() -> str:
        return 'dddmp'

    def transform(self) -> str:
        if self.path is None:
            self.path = tempfile.NamedTemporaryFile(mode='w', encoding='utf8') 
        result = super().transform()
        with open(self.path, 'r', encoding='utf8') as file:
            result = os.linesep.join(file.readlines())
        return result
