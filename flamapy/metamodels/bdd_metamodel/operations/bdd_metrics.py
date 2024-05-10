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
        self._features: dict[int, str] = {}
        self._common_features: list[Any] = []
        self._dead_features: list[Any] = []

    def get_result(self) -> list[dict[str, Any]]:
        return self.result

    def calculate_metamodel_metrics(self, model: VariabilityModel) -> list[dict[str, Any]]:
        self.model = cast(BDDModel, model)

        #Do some basic calculations to speedup the rest

        # Get all methods that are marked with the metric_method decorator
        metric_methods = [getattr(self, method_name) for method_name in dir(self)
                          if callable(getattr(self, method_name)) and 
                          hasattr(getattr(self, method_name), '_is_metric_method')]
        if self.filter is not None:
            metric_methods = [method for method in metric_methods 
                              if method.__name__ in self.filter]

        return [method() for method in metric_methods]

    @metric_method
    def valid(self) -> dict[str, Any]:
        """A feature model is valid if it represents at least one configuration."""
        if self.model is None:
            raise FlamaException('Model not initialized.')
        name = "Valid (not void)"
        _valid = bdd_operations.BDDValid().execute(self.model).get_result()
        result = self.construct_result(name=name, doc=self.valid.__doc__, result=_valid)
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
        _configurations = bdd_operations.BDDProducts().execute(self.model).get_result()
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
        _configurations = bdd_operations.BDDProductsNumber().execute(self.model).get_result()
        result = self.construct_result(name=name,
                                       doc=self.configurations.__doc__,
                                       result=_configurations,
                                       size=None)
        return result
