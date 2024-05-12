from typing import Any, cast, Callable, Optional

from flamapy.core.models import VariabilityModel
from flamapy.core.exceptions import FlamaException
from flamapy.core.operations.metrics_operation import Metrics
from flamapy.metamodels.bdd_metamodel.models import BDDModel
from flamapy.metamodels.bdd_metamodel import operations as bdd_operations


def metric_method(func: Callable) -> Callable:
    """Decorator to mark a method as a metric method.
    It has the value of the measure, it can also have a size and a ratio.
    Example:
        property name: Abstract Features.
        description: The description of the property.
        value (optional): the list of abstract features.
        size (optional): the length of the list.
        ratio (optional): the percentage of abstract features with regards the total number
                            of features.
    """
    if not hasattr(func, '_is_metric_method'):
        setattr(func, '_is_metric_method', True)
    return func


class BDDMetrics(Metrics):

    def __init__(self) -> None:
        super().__init__()
        self.model: Optional[VariabilityModel] = None
        self.result: list[dict[str, Any]] = []
        self.model_type_extension = "bdd"
        self._features: list[Any] = []

    def get_result(self) -> list[dict[str, Any]]:
        return self.result

    def calculate_metamodel_metrics(self, model: VariabilityModel) -> list[dict[str, Any]]:
        self.model = cast(BDDModel, model)

        #Do some basic calculations to speedup the rest
        self._features = self.model.variables

        # Get all methods that are marked with the metric_method decorator
        metric_methods = [getattr(self, method_name) for method_name in dir(self)
                          if callable(getattr(self, method_name)) and 
                          hasattr(getattr(self, method_name), '_is_metric_method')]
        if self.filter is not None:
            metric_methods = [method for method in metric_methods 
                              if method.__name__ in self.filter]

        return [method() for method in metric_methods]

    @metric_method
    def satisfiable(self) -> dict[str, Any]:
        """A feature model is satisfiable if it represents at least one configuration."""
        if self.model is None:
            raise FlamaException('Model not initialized.')
        name = "satisfiable (valid) (not void)"
        _satisfiable = bdd_operations.BDDSatisfiable().execute(self.model).get_result()
        result = self.construct_result(name=name, doc=self.satisfiable.__doc__, result=_satisfiable)
        return result

    @metric_method
    def core_features(self) -> dict[str, Any]:
        """Features that are part of all the configurations (aka 'common features')."""
        name = "Core features"
        _core = bdd_operations.BDDCoreFeatures().execute(self.model).get_result()
        result = self.construct_result(name=name,
                                       doc=self.core_features.__doc__,
                                       result=_core,
                                       size=len(_core),
                                       ratio=self.get_ratio(_core, self._features, 2))
        return result

    @metric_method
    def dead_features(self) -> dict[str, Any]:
        """Features that cannot appear in any configuration."""
        if self.model is None:
            raise FlamaException('Model not initialized.')
        name = "Dead features"
        _dead_features = bdd_operations.BDDDeadFeatures().execute(self.model).get_result()
        result = self.construct_result(name=name,
                                       doc=self.dead_features.__doc__,
                                       result=_dead_features,
                                       size=len(_dead_features),
                                       ratio=self.get_ratio(_dead_features, self._features, 2))
        return result

    @metric_method
    def configurations(self) -> dict[str, Any]:
        """Configurations represented by the feature model."""
        if self.model is None:
            raise FlamaException('Model not initialized.')
        name = "Configurations"
        _configurations = bdd_operations.BDDConfigurations().execute(self.model).get_result()
        result = self.construct_result(name=name,
                                       doc=self.configurations.__doc__,
                                       result=_configurations,
                                       size=len(_configurations))
        return result

    @metric_method
    def number_of_configurations(self) -> dict[str, Any]:
        """Number of configurations represented by the feature model."""
        if self.model is None:
            raise FlamaException('Model not initialized.')
        name = "Configurations"
        _configurations = bdd_operations.BDDConfigurationsNumber().execute(self.model).get_result()
        result = self.construct_result(name=name,
                                       doc=self.number_of_configurations.__doc__,
                                       result=_configurations,
                                       size=None)
        return result

    @metric_method
    def product_distribution(self) -> dict[str, Any]:
        """Product distribution of the feature model."""
        if self.model is None:
            raise FlamaException('Model not initialized.')
        name = "Product distribution"
        _dist = bdd_operations.BDDProductDistribution().execute(self.model).get_result()
        result = self.construct_result(name=name,
                                       doc=self.product_distribution.__doc__,
                                       result=_dist,
                                       size=None)
        return result

    @metric_method
    def feature_inclusion_probabilities(self) -> dict[str, Any]:
        """Feature inclusion probabilities of the feature model."""
        if self.model is None:
            raise FlamaException('Model not initialized.')
        name = "Feature inclusion probabilities"
        _prob = bdd_operations.BDDFeatureInclusionProbability().execute(self.model).get_result()
        result = self.construct_result(name=name,
                                       doc=self.feature_inclusion_probabilities.__doc__,
                                       result=_prob,
                                       size=None)
        return result