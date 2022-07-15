import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="famapy-bdd",
    version="1.0.0",
    author="José Miguel Horcas",
    author_email="jhorcas@us.es",
    description="bdd-plugin for the automated analysis of feature models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FaMaPy/bdd_metamodel",
    packages=setuptools.find_namespace_packages(include=['famapy.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=[
        'famapy~=1.0.0',
        'famapy-fm~=1.0.0',
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
        'famapy~=1.0.0',
    ]
)
