Using KubeCustom
================

Now that your credentials are ready to go (if not see the :ref:`Getting Started` page), you
can run the :func:`kubecustom.deployment.utilization_per_deployment` from the command line
with a refresh timer:

    ``python -m kubecustom -h``

or check out these examples of how to use in python scripting:

.. toctree::
    :maxdepth: 1
    :glob:

    examples/*

.. _supported_configuration_types:

Use a Different Configuration
------------------------------

Multiple configurations can be created from one of the following templates:

.. literalinclude:: ../kubecustom/template_files/template_keys.yaml
   :language: yaml
   :caption: Supported Configuration Types
