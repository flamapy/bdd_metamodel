import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="flamapy-bdd",
    version="1.0.1",
    author="Flamapy",
    author_email="flamapy@us.es",
    description="bdd-plugin for the automated analysis of feature models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flamapy/bdd_metamodel",
    packages=setuptools.find_namespace_packages(include=['flamapy.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=[
        'flamapy~=1.0.1',
        'flamapy-fm~=1.0.1',
        'dd>=0.5.6'
        'graphviz~=0.20',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-mock',
            'prospector',
            'mypy',
            'coverage',
        ]
    },
    dependency_links=[
        'flamapy~=1.0.1',
    ]
)
