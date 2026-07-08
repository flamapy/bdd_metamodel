from flamapy.core.manifest import PluginManifest, OperationCapability
from flamapy.core.models.language_level import LanguageLevel, MajorLevel

# Costs/limits from the 2.8 calibration run (FlamaExperimentExecutor calibration/costs.json,
# 2026-07-09): BDD compilation itself is the wall — every operation was fine at 100
# features (counting 22ms, core/dead ~1.5s) and timed out at 200, so the ceiling applies
# plugin-wide, not just to counting.
MANIFEST = PluginManifest(
    name='bdd',
    extension='bdd',
    supported_level=LanguageLevel(MajorLevel.BOOLEAN, set()),
    operations={
        'satisfiable': OperationCapability(max_features=150, cost=80),
        'configurations_number': OperationCapability(max_features=150, cost=60),
        'configurations': OperationCapability(max_features=150),
        'core_features': OperationCapability(max_features=150, cost=120),
        'dead_features': OperationCapability(max_features=150, cost=120),
    },
)
