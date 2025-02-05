Basic Deployment Interaction
============================

Import Functions
----------------

.. code:: ipython3

    import os

    from kubecustom.kubecustom import (
        create_secret_deployment,
        delete_secret_deployment,
    )
    from kubecustom.deployment import (
        utilization_per_deployment,
        scale_deployment,
    )
    from kubecustom.pod import (
        get_pods_resource_info,
        print_pods_summary,
        get_active_tasks,
        delete_pods_by_status,
    )
    from kubecustom import MyData
    MyDataInstance = MyData()
    user = MyDataInstance.get_user()

Check Active Tasks in Pods
--------------------------

.. code:: ipython3

    path = "/some/path/to/target/directory/394_pyddx-600"
    tag, cpus, mem = "pyddx-600", 16, 32
    deployment_name = f"{user}-{tag}"

    #create_secret_deployment(path, tag, cpus, mem, replicas=1)
    #delete_secret_deployment(deployment_name)
    #scale_deployment(deployment_name, 10)
    #get_pods_resource_info(verbose=True, keep_key=tag);
    print_pods_summary(deployment_name=deployment_name)
    #get_active_tasks(get_pod_list(deployment_name=deployment_name));
    #delete_pods_by_status("ContainerCreating")


.. parsed-literal::

    Pod Name,				Restart Count,	Memory,	CPUs,	|	Current State,	Current Status,	|	Previous State,	Previous Status
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-462kx,	23,	0.1,	0.0	|	running,	Running,	|	terminated,	OOMKilled
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-9bgsm,	0,	12.8,	12.2	|	running,	Running,	|	None,	None
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-ddcmn,	4,	0.1,	0.0	|	running,	Running,	|	terminated,	OOMKilled
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-htssf,	0,	10.5,	11.6	|	running,	Running,	|	None,	None
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-kwlvx,	35,	0.1,	0.0	|	running,	Running,	|	terminated,	OOMKilled
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-nbk7d,	0,	14.4,	10.1	|	running,	Running,	|	None,	None
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-pcv67,	5,	0.1,	0.0	|	running,	Running,	|	terminated,	OOMKilled
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-q287c,	1,	10.8,	11.2	|	running,	Running,	|	terminated,	OOMKilled
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-wshwz,	7,	15.2,	11.9	|	running,	Running,	|	terminated,	OOMKilled
    openff-qca-qm-jac-pyddx-600-6cf5cf797c-wvj5q,	19,	14.0,	10.5	|	running,	Running,	|	terminated,	OOMKilled


.. parsed-literal::

    UserWarning: No CPU unit detected, assuming whole CPU.
      warnings.warn("No CPU unit detected, assuming whole CPU.")


Get Pod CPU and Memory Usage
----------------------------

.. code:: ipython3

    output = utilization_per_deployment(namespace="openforcefield", verbose=True,) # keep_key="pyddx")
    # When containers are "waiting" their resources aren't counted... this means this plot shows higher utilizaiton than grafana


.. parsed-literal::

    Dep Name, Nreplicas, |  Avg Mem Ut%, Min Mem Ut%, Max Mem Ut%, Mem Req, |  Avg CPU Ut%, Min CPU Ut%, Max CPU Ut%, CPU Req
    _____________________________________________________________________________
    openff-qca-qm-jac-pyddx-600	10	|	24.4	0.2	47.4	32.0	|	42.2	0.0	76.1	16.0
