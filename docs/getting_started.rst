.. _Getting Started:

Getting Started
===============

Installation
-------------

* Step 1: Download the main branch from our GitHub page as a zip file, or clone it to your working directory with:

    ``git clone https://github.com/openforcefield/kubecustom``

* Step 2 (Optional): If you are using conda and you want to create a new environment for this package you may install with:

    ``conda env create -f requirements.yaml``

* Step 3: Install package with:

    ``pip install kubecustom/.``

    or change directories and run

    ``pip install .``

    Adding the flag ``-e`` will allow you to make changes that will be functional without reinstallation.

* Step 4: Initialize pre-commits (for developers)

    ``pre-commit install``

Setting Up Your Credentials
---------------------------

Just like the set up of `kubectl` you'll need your `.kube/config` file in place.

Kubecustom seeks to simplify your interaction with Kubernetes by using the python API
alternative to `kubectl`. Part of that process involves saving your information that is expected
to be repetitively used. This includes the names of the environment variables holding your server
username and password for secret files (the credentials themselves are never stored), your
container names, container images, cluster name, user identifier string, and team namespace.
See :class:`kubecustom.secret.MyData` for more information. In the process of installing
`kubecustom`, a yaml file that will contain this information is created. `kubecustom` will not
operate normally until you've populated the file. The ``username`` and ``password`` entries must be the
names of environment variables, never the credentials themselves; ``kubecustom`` reads the values from
your environment when they are needed and raises an error if the variable is not set. For example, add the
following to your shell profile:

``export NRP_USER=myusername NRP_PASSWORD=mypassword``

The file can be populated in two ways:

Using python scripting...
::

>    from kubecustom import MyData
>    MyDataInstance = MyData()
>    MyDataInstance.add_data(
>        configuration_name="my-config",
>        username="NRP_USER_ENV",
>        password="NRP_PASSWORD_ENV",
>        user="my-org-my-initials",
>        namespace="myorgnamespace",
>        container_name="my-org-pod",
>        container_image="ghcr.io/...",
>        cluster_name="our_kubernetes_cluster",
>    )

Alternatively you may achieve this interactively in the commandline:

``python -c 'from kubecustom import MyData; obj=MyData(); obj.add_interactively()'``
