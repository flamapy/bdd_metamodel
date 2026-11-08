from flamapy.core.manifest import OperationCapability, PluginManifest
from flamapy.core.models.language_level import LanguageLevel, MajorLevel, MinorLevel

# Costs are estimated milliseconds from the 2026-11-06 calibration with the pure-Python dd
# engine (what 2.9 ships): betty synthetic models at 1% and 30% constraint density plus
# JHipster and busybox, worst case of the two densities, never decreasing. Compiling the BDD is
# the wall, and it is erratic: 0.2 s for both 200-feature models, 0.4 s for the sparse
# 500-feature model but more than 5 minutes for the dense one, 1.7 s / 32 s at 1,000, and
# busybox (1,108 features) did not compile in 10 minutes. The journal benchmark with the same
# engine (300 s cap, real UVLHub models) compiled 29 of 41 models of 501-1,000 features and 2
# of 120 beyond, hence the 1,000-feature ceiling. Once compiled, every query is cheap (counting
# 29 ms, core/dead 140 ms, false-optional 300 ms at 1,000 features). The experimental native
# builder (flamapy-cudd, not released) is opt-in and not reflected here.
_MAX_FEATURES = 1000

MANIFEST = PluginManifest(
    name='bdd',
    calibration='2026-11-06',
    extension='bdd',
    supported_level=LanguageLevel(MajorLevel.BOOLEAN, {MinorLevel.GROUP_CARDINALITY}),
    # Every operation needs the compiled BDD, so the ceiling is plugin-wide.
    max_features=_MAX_FEATURES,
    transformation_cost_curve=((50, 11), (100, 23), (200, 200), (1000, 300000)),
    operations={
        'satisfiable': OperationCapability(cost=1),
        'satisfiable_configuration': OperationCapability(cost=1),
        'configurations_number': OperationCapability(
            cost_curve=((100, 1), (200, 4), (500, 9), (1000, 29))),
        # Two counts: all the products and those that include the configuration.
        'commonality': OperationCapability(
            cost_curve=((100, 2), (200, 8), (500, 18), (1000, 58))),
        'core_features': OperationCapability(
            cost_curve=((100, 1), (200, 20), (500, 33), (1000, 130))),
        'dead_features': OperationCapability(
            cost_curve=((100, 1), (200, 20), (500, 30), (1000, 140))),
        'false_optional_features': OperationCapability(
            cost_curve=((50, 2), (100, 3), (200, 42), (500, 72), (1000, 300))),
        # Uniform random sampling over the compiled BDD.
        'sampling': OperationCapability(
            cost_curve=((50, 2), (100, 3), (200, 29), (500, 57), (1000, 200))),
        # Listing is bounded by the number of configurations, not by the BDD: about 3 us and
        # 1 KB per configuration (measured 2026-11-08 on 16 UVLHub models of 1e3-1.5e6
        # configurations), so a million already takes ~1 GB. Using the exact counts of the SoSyM
        # benchmark (rq2_bdd_final), the share of UVLHub models with at most a million
        # configurations is 100% up to 30 features, 76% at 31-50, 36% at 51-75 and under 25%
        # beyond; with the same ~70% rule as the compilation ceiling, the limit is 50 features.
        'configurations': OperationCapability(max_features=50),
    },
)
