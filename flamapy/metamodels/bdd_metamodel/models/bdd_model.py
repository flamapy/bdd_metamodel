import os
import stat
import subprocess
import locale
from platform import system 
from pathlib import Path
from typing import Any

from flamapy.core.models import VariabilityModel


class BDDModel(VariabilityModel):
    """A Binary Decision Diagram (BDD) representation of the feature model.

    It relies on the bdd4va library (https://github.com/rheradio/bdd4va).
    """

    # Binary programs available
    SPLOT2LOGIC = 'splot2logic.sh'
    LOGIC2BDD = 'logic2bdd.sh'
    BDD_SAMPLER = 'BDDSampler.sh'
    PRODUCT_DISTRIBUTION = 'product_distribution.sh'
    FEATURE_PROBABILITIES = 'feature_probabilities.sh'
    COUNTER = 'counter.sh'

    @staticmethod
    def get_extension() -> str:
        return 'bdd'

    def __init__(self) -> None:
        """Initialize the BDD with the dddmp file.

        The BDD relies on a dddmp file that stores a feature model's BDD encoding (dddmp is the
        format that the BDD library CUDD uses; check https://github.com/vscosta/cudd)
        """
        self.bdd_file: str = None
        self._set_global_constants()

    def set_bdd_file(self, dddmp_file: str) -> None:
        self.bdd_file = dddmp_file

    def get_bdd_file(self) -> str:
        return self.bdd_file

    def __del__(self) -> None:
        if self.bdd_file is not None:
            Path(self.bdd_file + '.dddmp').unlink()

    def _set_global_constants(self) -> None:
        """Private auxiliary function that configures the following global constants.

            + SYSTEM, which stores the operating system running bdd4va: Linux or Windows.
            + BDD4VAR_DIR, which stores the path of the module bdd4va, 
            which is needed to locate the binaries.
        """
        # get SYSTEM
        self.system = system()
        # get BDD4VAR_DIR
        caller_dir = os.getcwd()
        os.chdir(Path(__file__).parent)
        if self.system == 'Windows':
            shell = subprocess.run(['wsl', 'pwd'], stdout=subprocess.PIPE, check=True)
        else:
            shell = subprocess.run(['pwd'], stdout=subprocess.PIPE, check=True)
        self.bdd4var_dir = shell.stdout.decode(str(locale.getdefaultlocale()[1])).strip()
        os.chdir(caller_dir)

    def run(self, binary: str, *args: Any) -> Any:
        """Private auxiliary function to run binary files in Linux and Windows."""
        #bin_file = os.path.join(self.bdd4var_dir, 'bin', binary)
        bin_dir = self.bdd4var_dir + '/bin'
        bin_file = bin_dir + '/' + binary
        # Set execution permission
        file_stats = os.stat(bin_file)
        os.chmod(bin_file, file_stats.st_mode | stat.S_IEXEC)
        if self.system == 'Windows':
            if not args:
                command = ['wsl', bin_file, bin_dir]
            else:
                command = ['wsl', bin_file, bin_dir] + list(args)
        else:
            if not args:
                command = [bin_file, bin_dir]
            else:
                command = [bin_file, bin_dir] + list(args)
        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    @staticmethod
    def check_file_existence(filename: str, extension: str = None) -> str:
        """Private auxiliary function that verifies if the input file exists."""
        if not os.path.isfile(filename) and extension is not None:
            filename = filename + '.' + extension
            if not os.path.isfile(filename):
                message = 'The file "' + filename + '" doesn\'t exist.'
                raise Exception(message)
        return filename
