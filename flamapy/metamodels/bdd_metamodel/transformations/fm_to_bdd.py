import importlib
import logging
import os
from types import ModuleType
from typing import Any, Optional, cast

from flamapy.core.models import VariabilityModel
from flamapy.core.transformations import CacheableModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import FMSecureFeaturesNames
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel.models.bdd_model import DD_BACKEND
from flamapy.metamodels.bdd_metamodel.models.utils import PLModel
from flamapy.metamodels.bdd_metamodel.models.utils.ordering import (
    CLAUSE_ORDERS,
    VARIABLE_ORDERS,
    clause_order,
    variable_order,
)


# Only CUDD can write DDDMP, so cached artifacts use DDDMP with the 'cudd' dd engine and dd's
# JSON format with the pure-Python 'autoref' engine (see DD_BACKEND).
__all__ = ["DD_BACKEND", "FmToBDD", "attach_feature_mapping"]

logger = logging.getLogger(__name__)

BUILDERS = ("auto", "native", "python")
BUILD_MODES = ("incremental", "monolithic")
DEFAULT_BUILD = "incremental"
DEFAULT_VAR_ORDER = "tree"
DEFAULT_CLAUSE_ORDER = "minspan"


def _native_module() -> Optional[ModuleType]:
    """flamapy_cudd (Logic2BDD on CUDD, `pip install flamapy-bdd[fast]`), if installed."""
    try:
        return importlib.import_module("flamapy_cudd")
    except ImportError:
        return None


def _env_choice(name: str, default: str, choices: tuple[str, ...]) -> str:
    value = os.environ.get(name, default).strip().lower()
    if value not in choices:
        raise ValueError(f"{name}={value!r} is not valid. Use one of {choices}.")
    return value


def _env_reorder() -> Optional[bool]:
    value = os.environ.get("FLAMAPY_BDD_REORDER", "auto").strip().lower()
    if value in ("auto", ""):
        return None
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"FLAMAPY_BDD_REORDER={value!r} is not valid. Use auto, 1 or 0.")


class FmToBDD(CacheableModelToModel):
    """Transforms a Feature Model into a BDD Model.

    With the optional native package flamapy-cudd installed (`pip install flamapy-bdd[fast]`)
    the BDD is built by Logic2BDD on CUDD (`builder="native"`; `"auto"`, the default, uses it
    whenever it is installed) and loaded into the dd engine in use; it handles much larger
    models. Otherwise (`builder="python"`) it is built with dd as follows.

    By default the BDD is built clause by clause (`build="incremental"`): the variables are
    declared in feature-tree order (`var_order`), the clauses are conjoined following a
    schedule (`clause_order`), and with dd built against CUDD the variables are reordered
    dynamically while building (`reorder`). `build="monolithic"` parses the whole formula at
    once, as earlier versions did. Each option can also be set with the environment variables
    FLAMAPY_BDD_BUILDER, FLAMAPY_BDD_BUILD, FLAMAPY_BDD_VAR_ORDER, FLAMAPY_BDD_CLAUSE_ORDER and
    FLAMAPY_BDD_REORDER (auto, 1 or 0); explicit arguments take precedence. See
    `models/utils/ordering.py`. `var_order` is also the initial order of the native builder.

    BDD compilation is the expensive step, so the transformation is cacheable: the compiled
    BDD round-trips through DDDMP (dd built with CUDD) or dd's JSON format (the pure-Python
    engine), opt-in via FLAMAPY_CACHE=1, and only the cheap feature-name mapping is
    recomputed on a cache load.
    """

    artifact_suffix = "dddmp" if DD_BACKEND == "cudd" else "json"
    # 2: feature-name mapping fixed for names that sanitize alike (FMSecureFeaturesNames);
    # artifacts compiled before that may hold merged variables and must not be reused.
    # 3: the build options (variable order, clause schedule, reordering) are part of the key.
    artifact_format_version = 3

    @staticmethod
    def get_source_extension() -> str:
        return "fm"

    @staticmethod
    def get_destination_extension() -> str:
        return "bdd"

    def __init__(self,  # noqa: PLR0913  (build options, keyword-only)
                 source_model: FeatureModel,
                 *,
                 build: Optional[str] = None,
                 var_order: Optional[str] = None,
                 clause_order: Optional[str] = None,  # pylint: disable=redefined-outer-name
                 reorder: Optional[bool] = None,
                 builder: Optional[str] = None) -> None:
        self.source_model = source_model
        self.destination_model: Optional[BDDModel] = None
        builder = builder or _env_choice("FLAMAPY_BDD_BUILDER", "auto", BUILDERS)
        if builder not in BUILDERS:
            raise ValueError(f"Unknown builder '{builder}'. Use one of {BUILDERS}.")
        self._native = _native_module() if builder in ("auto", "native") else None
        if builder == "native" and self._native is None:
            raise ValueError("builder='native' needs the flamapy-cudd package "
                             "(pip install flamapy-bdd[fast]).")
        self._fallback = builder == "auto"
        self.builder = "native" if self._native is not None else "python"
        self.build = build or _env_choice("FLAMAPY_BDD_BUILD", DEFAULT_BUILD, BUILD_MODES)
        self.var_order = var_order or _env_choice("FLAMAPY_BDD_VAR_ORDER", DEFAULT_VAR_ORDER,
                                                  VARIABLE_ORDERS)
        self.clause_order = clause_order or _env_choice("FLAMAPY_BDD_CLAUSE_ORDER",
                                                        DEFAULT_CLAUSE_ORDER, CLAUSE_ORDERS)
        if self.build not in BUILD_MODES:
            raise ValueError(f"Unknown build mode '{self.build}'. Use one of {BUILD_MODES}.")
        if reorder is None:
            reorder = _env_reorder()
        # Dynamic reordering is cheap in CUDD but slow in the pure-Python engine.
        self.reorder: bool = (DD_BACKEND == "cudd") if reorder is None else reorder

    def cache_options(self) -> dict[str, Any]:
        # Artifacts written by one dd engine are never loaded by the other, and the build
        # options change the variable order stored in the artifact.
        if self._native is not None:
            return {"dd_backend": DD_BACKEND, "builder": "native",
                    "native_version": getattr(self._native, "__version__", "unknown"),
                    "var_order": self.var_order}
        return {"dd_backend": DD_BACKEND, "builder": "python", "build": self.build,
                "var_order": self.var_order, "clause_order": self.clause_order,
                "reorder": self.reorder}

    def dump_artifact(self, model: VariabilityModel, path: str) -> None:
        bdd_model = cast(BDDModel, model)
        if DD_BACKEND != "cudd":
            bdd_model.save_bdd(path, [bdd_model.root], "json")
            return
        # Local import: the writer imports models, keep module import light.
        from flamapy.metamodels.bdd_metamodel.transformations.dddmp_writer import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel,cyclic-import
            DDDMPWriter,
        )
        DDDMPWriter(path, bdd_model).transform()

    def load_artifact(self, path: str, source_model: VariabilityModel) -> VariabilityModel:
        if DD_BACKEND != "cudd":
            model = BDDModel.load_bdd(path)
        else:
            from flamapy.metamodels.bdd_metamodel.transformations.dddmp_reader import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel,cyclic-import
                DDDMPReader,
            )
            model = DDDMPReader(path).transform()
        attach_feature_mapping(model, cast(FeatureModel, source_model))
        return model

    def transform(self) -> BDDModel:
        fm_secure_names_op = FMSecureFeaturesNames(self.source_model)
        secured_model = fm_secure_names_op.transform()

        pl_model = PLModel()
        formula = pl_model.build_from_feature_model(secured_model)
        model_order = [feature.name for feature in secured_model.get_features()]
        order = variable_order(pl_model.variables, pl_model.clauses, self.var_order,
                               model_order)
        self.destination_model = None
        if self._native is not None:
            try:
                self.destination_model = self._build_native(secured_model, order)
            except ValueError as error:  # Logic2BDDError is a ValueError
                if not self._fallback:
                    raise
                logger.warning("Native BDD build failed (%s); building with dd.", error)
                self.destination_model = None
        if self.destination_model is None:
            self.destination_model = self._build_python(pl_model, formula, order)
        _set_feature_mapping(self.destination_model, fm_secure_names_op, secured_model)
        self.source_model = secured_model
        return self.destination_model

    def _build_native(self, secured_model: FeatureModel, order: list[str]) -> BDDModel:
        # Local imports: only needed with the native builder.
        from flamapy.metamodels.bdd_metamodel.models.utils.logic2bdd_writer import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel
            feature_model_to_logic2bdd,
        )
        from flamapy.metamodels.bdd_metamodel.transformations.dddmp_reader import (  # noqa: PLC0415  pylint: disable=import-outside-toplevel,cyclic-import
            load_dddmp_text,
        )
        native = cast(ModuleType, self._native)
        l2b = feature_model_to_logic2bdd(secured_model, order)
        names = {var: name for name, var in l2b.names.items()}
        text = native.compile_bdd([names[var] for var in order], l2b.expressions)
        return load_dddmp_text(text, l2b.names)

    def _build_python(self, pl_model: PLModel, formula: str, order: list[str]) -> BDDModel:
        model = BDDModel()
        if self.build == "monolithic":
            model.build_bdd(formula, order)
        else:
            schedule = clause_order(pl_model.clauses, order, self.clause_order)
            model.build_bdd_incremental(
                (clause.formula for clause in schedule), order, reorder=self.reorder)
        return model


def attach_feature_mapping(model: BDDModel, source_model: FeatureModel) -> None:
    """Attach to `model` the feature <-> variable mapping of `source_model`.

    The variable names of a compiled BDD are the sanitized feature names
    (FMSecureFeaturesNames), so the mapping is recomputed from the feature model rather than
    trusted from a stored artifact.
    """
    fm_secure_names_op = FMSecureFeaturesNames(source_model)
    secured_model = fm_secure_names_op.transform()
    _set_feature_mapping(model, fm_secure_names_op, secured_model)


def _set_feature_mapping(model: BDDModel,
                         fm_secure_names_op: FMSecureFeaturesNames,
                         secured_model: FeatureModel) -> None:
    model.features_vars = fm_secure_names_op.mapping_names
    model.vars_features = {v: f for f, v in model.features_vars.items()}
    # Attach the (sanitized) feature model for operations that may need it.
    model.original_model = secured_model
