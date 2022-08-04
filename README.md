# BDD plugin for flamapy
- [BDD plugin for flamapy](#bdd-plugin-for-flamapy)
  - [Description](#description)
  - [Requirements and Installation](#requirements-and-installation)
  - [Functionality and usage](#functionality-and-usage)
    - [Load a feature model and create the BDD](#load-a-feature-model-and-create-the-bdd)
    - [Save the BDD in a file](#save-the-bdd-in-a-file)
    - [Analysis operations](#analysis-operations)
  - [Contributing to the BDD plugin](#contributing-to-the-bdd-plugin)


## Description
This plugin supports Binary Decision Diagrams (BDDs) representations for feature models.

The plugin is based on [flamapy](https://github.com/flamapy/core) and thus, it follows the same architecture:

<p align="center">
  <img width="750" src="doc/bdd_plugin.png">
</p>

The BDD plugin relies on the [dd](https://github.com/tulip-control/dd) library to manipulate BDDs.
The complete documentation of such library is available [here](https://github.com/tulip-control/dd/blob/main/doc.md).

The following is an example of feature model and its BDD using complemented arcs.

<p align="center">
  <img width="750" src="doc/fm_example.png">
</p>

<p align="center">
  <img width="750" src="doc/bdd_example.svg">
</p>

## Requirements and Installation
- Python 3.9+
- This plugin depends on the [flamapy core](https://github.com/flamapy/core) and on the [Feature Model plugin](https://github.com/flamapy/fm_metamodel).

```
pip install flamapy flamapy-fm flamapy-bdd
```

We have tested the plugin on Linux, but Windows is also supported.


## Functionality and usage
The executable script [test_bdd_metamodel.py](https://github.com/flamapy/bdd_metamodel/blob/master/tests/test_bdd_metamodel.py) serves as an entry point to show the plugin in action.

The following functionality is provided:


### Load a feature model and create the BDD
```python
from flamapy.metamodels.fm_metamodel.transformations.featureide_reader import FeatureIDEReader
from flamapy.metamodels.bdd_metamodel.transformations.fm_to_bdd import FmToBDD

# Load the feature model from FeatureIDE
feature_model = FeatureIDEReader('input_fms/featureide_models/pizzas.xml').transform()
# Create the BDD from the feature model
bdd_model = FmToBDD(feature_model).transform()
```


### Save the BDD in a file
```python
from flamapy.metamodels.bdd_metamodel.transformations.bdd_writer import BDDWriter, BDDDumpFormat
# Save the BDD as an image in PNG
BDDWriter(path='my_bdd.png',
          source_model=bdd_model,
          roots=[bdd_model.root],
          output_format=BDDDumpFormat.PNG).transform()
```
Formats supported: DDDMP_V3 ('dddmp'), DDDMP_V2 ('dddmp2'), PDF ('pdf'), PNG ('png'), SVG ('svg').


### Analysis operations

- Products number

    Return the number of products (configurations):
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import BDDProductsNumber
    nof_products = BDDProductsNumber().execute(bdd_model).get_result()
    print(f'#Products: {nof_products}')
    ```
    or alternatively:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import products_number
    nof_products = products_number(bdd_model)
    print(f'#Products: {nof_products}')
    ```

- Products

    Return the list of products (configurations):
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import BDDProducts
    list_products = BDDProducts().execute(bdd_model).get_result()
    for i, prod in enumerate(list_products):
        print(f'Product {i}: {[feat for feat in prod.elements if prod.elements[feat]]}')
    ```
    or alternatively:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import products
    nof_products = products(bdd_model)
    for i, prod in enumerate(list_products):
        print(f'Product {i}: {[feat for feat in prod.elements if prod.elements[feat]]}')
    ```

- Sampling

    Return a sample of the given size of uniform random products (configurations) with or without replacement:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import BDDSampling
    list_sample = BDDSampling(size=5, with_replacement=False).execute(bdd_model).get_result()
    for i, prod in enumerate(list_sample):
        print(f'Product {i}: {[feat for feat in prod.elements if prod.elements[feat]]}')
    ```
    or alternatively:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import sample
    list_sample = sample(bdd_model, size=5, with_replacement=False)
    for i, prod in enumerate(list_sample):
        print(f'Product {i}: {[feat for feat in prod.elements if prod.elements[feat]]}')
    ```

- Product Distribution

    Return the number of products having a given number of features:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import BDDProductDistributionBF
    dist = BDDProductDistributionBF().execute(bdd_model).get_result()
    print(f'Product Distribution: {dist}')
    ```
    or alternatively:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import product_distribution
    dist = product_distribution(bdd_model)
    print(f'Product Distribution: {dist}')
    ```

- Feature Inclusion Probability

    Return the probability for a feature to be included in a valid product:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import BDDFeatureInclusionProbabilityBF
    prob = BDDFeatureInclusionProbabilityBF().execute(bdd_model).get_result()
    for feat in prob.keys():
        print(f'{feat}: {prob[feat]}')
    ```
    or alternatively:
    ```python
    from flamapy.metamodels.bdd_metamodel.operations import feature_inclusion_probability
    prob = feature_inclusion_probability(bdd_model)
    for feat in prob.keys():
        print(f'{feat}: {prob[feat]}')
    ```

All analysis operations support also a partial configuration as an additional argument, so the operation will return the result taking into account the given partial configuration. For example:

```python
from flamapy.core.models import Configuration
# Create a partial configuration
elements = {'Pizza': True, 'Big': True}
partial_config = Configuration(elements)
# Calculate the number of products from the partial configuration
nof_products = BDDProductsNumber(partial_config).execute(bdd_model).get_result()
print(f'#Products: {nof_products}')
```
or alternatively:
```python
nof_products = products(bdd_model, partial_config)
print(f'#Products: {nof_products}')
```


## Contributing to the BDD plugin
To contribute in the development of this plugin:

1. Fork the repository into your GitHub account.
2. Clone the repository: `git@github.com:<<username>>/bdd_metamodel.git`
3. Create a virtual environment: `python -m venv env`
4. Activate the virtual environment: `source env/bin/activate`
5. Install the plugin dependencies: `pip install flamapy flamapy-fm`
6. Install the BDD plugin from the source code: `pip install -e bdd_metamodel`

Please try to follow the standards code quality to contribute to this plugin before creating a Pull Request:

- To analyze your Python code and output information about errors, potential problems, convention violations and complexity, pass the prospector with:

    `make lint`

- To analyze the static type checker for Python and find bugs, pass the Mypy:

    `make mypy`

