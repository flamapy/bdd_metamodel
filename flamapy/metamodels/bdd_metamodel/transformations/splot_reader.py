import re 
from pathlib import Path

from flamapy.core.transformations import TextToModel
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class SPLOTReader(TextToModel):

    @staticmethod
    def get_source_extension() -> str:
        return 'sxfm'

    def __init__(self, path: str) -> None:
        self._path = path

    def transform(self) -> BDDModel:
        bdd_model = BDDModel()
        build_bdd(self._path, bdd_model)
        return bdd_model


def build_bdd(model_file: str, bdd_model: BDDModel) -> None:
    """Builds a BDD for a feature model specified with the SPLOT format 
    (visit http://www.splot-research.org/).

    Return a dddmp file containing the BDD encoding of the model (dddmp is the format that the
    BDD library CUDD uses; check https://github.com/vscosta/cudd).
    The dddmp file is generated in the same folder where model_file is located.
    """
    # Check model_file
    splot_extension = SPLOTReader.get_source_extension()
    model_file = bdd_model.check_file_existence(model_file, splot_extension)
    re_expression = '(.*)[.]' + splot_extension
    match = re.search(re_expression, model_file)
    if match is not None:
        file_name = match.group(1)

    # Run binary splot2logic
    print("Preprocessing " + model_file + " to get its BDD...")
    bdd_model.run("splot2logic", "-use-XOR", model_file)
    # Check that splot2logic was successful
    bdd_model.check_file_existence(file_name, "var")
    bdd_model.check_file_existence(file_name, "exp")
    try:
        bdd_model.check_file_existence(file_name, "var")
        bdd_model.check_file_existence(file_name, "exp")
    except Exception:
        message = 'BDD synthesis failed: the files "' + file_name + '.var" and "' + \
                  file_name + '.exp" couldn\'t be generated.'
        raise Exception(message) from Exception

    # Run binary logic2bdd's execution
    print("Synthesizing the BDD (this may take a while)...")
    bdd_model.run("logic2bdd",
                  "-line-length", "50",
                  "-min-nodes", "100000",
                  "-constraint-reorder", "minspan",
                  "-base", file_name,
                  file_name + ".var",
                  file_name + ".exp")
    # Check that logic2bdd's execution was successful
    try:
        bdd_model.check_file_existence(file_name, "dddmp")
    except Exception:
        message = 'BDD synthesis failed: the file "' + file_name + '.dddmp couldn\'t be generated.'
        raise Exception(message) from Exception

    # Remove auxiliary generated files
    auxiliary_files = [".data", ".exp", ".reorder", ".tree", ".var"]
    for ext in auxiliary_files: 
        Path(file_name + ext).unlink()
    bdd_model.set_bdd_file(file_name)
