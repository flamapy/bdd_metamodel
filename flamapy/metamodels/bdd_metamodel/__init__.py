from flamapy.core.manifest import PluginManifest, OperationCapability
from flamapy.core.models.language_level import LanguageLevel, MajorLevel

MANIFEST = PluginManifest(
    name='bdd',
    extension='bdd',
    supported_level=LanguageLevel(MajorLevel.BOOLEAN, set()),
    operations={
        # BDD compilation blows up beyond a few hundred features; the ceiling is a
        # placeholder to be refined from benchmark calibration data.
        'configurations_number': OperationCapability(max_features=300),
        'configurations': OperationCapability(max_features=300),
    },
)
