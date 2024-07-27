import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

def read_requirements(file):
    with open(file, "r") as fh:
        return fh.read().splitlines()
    
# Read requirements from the requirements.txt file
requirements = read_requirements("requirements.txt")

# Read development requirements from the dev-requirements.txt file
dev_requirements = read_requirements("requirements-dev.txt")

setuptools.setup(
    name="flamapy-bdd",
    version="2.0.0.dev10",
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
    install_requires=requirements,
    extras_require={
        'dev':dev_requirements
    }
)