KubeCustom
==============================
[//]: # (Badges)
[![GitHub Actions Build Status](https://github.com/jaclark5/kubecustom/workflows/CI/badge.svg)](https://github.com/jaclark5/kubecustom/actions?query=workflow%3ACI)
[![Documentation Status](https://readthedocs.org/projects/kubecustom/badge/?version=latest)](https://kubecustom.readthedocs.io/en/latest/?badge=latest)
<!--
[![codecov](https://codecov.io/gh/jaclark5/kubecustom/branch/main/graph/badge.svg)](https://codecov.io/gh/jaclark5/kubecustom/branch/main)
-->

Kubernetes assessment  and combined control functions to handle multiple deployments.

## Installation

* Step 1: Download the main branch from our GitHub page as a zip file, or clone it to your working directory with:

    ``git clone https://github.com/jaclark5/kubecustom``

* Step 2 (Optional): If you are using conda and you want to create a new environment for this package you may install with:

    ``conda env create -f requirements.yaml``

* Step 3: Install package with:

    ``pip install kubecustom/.``

    or change directories and run

    ``pip install .``

    Adding the flag ``-e`` will allow you to make changes that will be functional without reinstallation.

* Step 4: Initialize pre-commits (for developers)

    ``pre-commit install``

### Copyright

Copyright (c) 2025, Jennifer A. Clark


#### Acknowledgements

Project based on the
[Computational Molecular Science Python Cookiecutter](https://github.com/molssi/cookiecutter-cms) version 1.10.
