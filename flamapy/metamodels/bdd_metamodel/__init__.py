import os
from importlib.util import find_spec

from flamapy.core.manifest import PluginManifest, OperationCapability
from flamapy.core.models.language_level import LanguageLevel, MajorLevel


def _installed(module: str) -> bool:
    try:
        return find_spec(module) is not None
    except (ImportError, ValueError):
        return False


# Costs are from the 2.8 calibration run (FlamaExperimentExecutor calibration/costs.json,
# 2026-07-09). Compiling the BDD is the wall, so the feature limits depend on how the BDD is
# built (benchmarks/README.md, 2026-11-02): the native builder (flamapy-cudd) compiled real
# models of ~1200 features in seconds, the dd builder with CUDD up to ~500 features, and the
# pure-Python dd engine up to ~300 (earlier versions ran out of memory at 200). Enumerating
# configurations is limited by their number, whatever the builder.
_NATIVE = (_installed("flamapy_cudd")
           and os.environ.get("FLAMAPY_BDD_BUILDER", "auto").strip().lower() != "python")
if _NATIVE:
    _MAX_FEATURES = 1200
elif _installed("dd.cudd"):
    _MAX_FEATURES = 500
else:
    _MAX_FEATURES = 300

MANIFEST = PluginManifest(
    name='bdd',
    extension='bdd',
    supported_level=LanguageLevel(MajorLevel.BOOLEAN, set()),
    operations={
        'satisfiable': OperationCapability(max_features=_MAX_FEATURES, cost=80),
        'configurations_number': OperationCapability(max_features=_MAX_FEATURES, cost=60),
        'configurations': OperationCapability(max_features=150),
        'core_features': OperationCapability(max_features=_MAX_FEATURES, cost=120),
        'dead_features': OperationCapability(max_features=_MAX_FEATURES, cost=120),
    },
)
