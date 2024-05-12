from flamapy.metamodels.bdd_metamodel.transformations._bdd_writer import BDDWriter


class PickleWriter(BDDWriter):

    @staticmethod
    def get_destination_extension() -> str:
        return 'p'

    def transform(self) -> str:
        if self._roots is None:
            try:
                self.source_model.bdd.dump(filename=self.path)
            except Exception:
                self._roots = [self.source_model.root]
        self.source_model.bdd.dump(filename=self.path, roots=self._roots)
        return ''