"""Create, delete, and extract information for deployments"""

import warnings
import numpy as np
import contextlib
import time
import traceback

from kubernetes import client, config, utils
from kubernetes.stream import portforward
from kubernetes.client.exceptions import ApiException
from websocket import WebSocketConnectionClosedException

from .utils import (
    load_yaml,
    convert_cpu_use,
    convert_memory_use,
    convert_keys_to_camel_case,
    MyData,
)
from .pod import (
    sort_pods_by_deployment,
    get_pods_resource_info,
    delete_pod,
    get_pod_list,
    wait_for_pod_state,
)
from .pvc import create_volume_mount

try:
    MyDataInstance = MyData()
except Exception:
    warnings.warn(
        "Could not import namespace, functions imported from this module may not operate as expected until "
        "you set manually with 'kubecustom.MyData.add_data()' or interactively with `python -c 'from "
        "kubecustom import MyData; obj=MyData(); obj.add_interactively()'`"
    )


def create_deployment(
    deployment_yaml, excluded_nodes=None, args_pvc=(), namespace=None, verbose=True
):
    """Create a deployment from yaml file

    Args:
        deployment_yaml (str): Filename and path to yaml file
        excluded_nodes (list, optional): List of node names to exclude. Defaults to None.
        args_pvc (tuple, optional): Arguments for :func:`kubecustom.pvc.create_volume_mount`
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    config.load_kube_config()  # Refresh credentials

    # Create deployment
    deployment = load_yaml(deployment_yaml)
    deployment["metadata"]["namespace"] = namespace

    if args_pvc:
        volume_mount = create_volume_mount(
            *args_pvc
        )  # function that takes name and path
        raise NotImplementedError(
            f"The ability to support PVCs is not yet implemented. {volume_mount}"
        )
    #        create_volume_mount is equivalent of _to_volume_mount_k8s
    #        missing: volume = ? need equivalent to _to_volume_k8s
    #        both of these need to go into the deployment yaml
    if excluded_nodes is not None:
        deployment = add_node_affinity(deployment, excluded_nodes)

    utils.create_from_dict(client.ApiClient(), deployment)
    if verbose:
        print(f"Deployment {deployment['metadata']['name']} created.")


def delete_deployment(deployment_name, namespace=None, verbose=True):
    """Delete a kubernetes deployment

    Args:
        deployment_name (str): Name of deployment
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    config.load_kube_config()
    client.AppsV1Api().delete_namespaced_deployment(
        name=deployment_name, namespace=namespace
    )
    if verbose:
        print(f"Deployment {deployment_name} deleted.")


def get_deployment(deployment_name, namespace=None):
    """Get deployment object from Kubernetes API

    Args:
        deployment_name (str): Name of the deployment of a number of replica pods
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.

    Returns:
        obj: ``kubernetes.client.models.v1_deployment.V1Deployment`` deployment object
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    config.load_kube_config()
    apps_v1_api = client.AppsV1Api()
    return apps_v1_api.read_namespaced_deployment(deployment_name, namespace)


@contextlib.contextmanager
def forward_port(
    deployment_name,
    port=None,
    timelag=5,
    namespace=None,
):
    """
    Forward a port from a Kubernetes deployment to the local machine.

    This assumes that the deployment has at least one pod.

    Args:
        deployment_name (str): Name of deployment
        port (int): Port to forward. Currently assumed that local and pod port are the same.
        timelag (int, optional): Amount of time to wait in seconds before checking that the part connection is
        established, Defaults to 5.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace
    port = MyDataInstance.get_port() if port is None else port
    local_port, pod_port = port, port

    config.load_kube_config()

    pods = get_pod_list(deployment_name=deployment_name, namespace=namespace)
    pod_name = pods[0].metadata.name.split("_")[0]
    print(f"Pod name: {pod_name}")

    # Wait for the pod to be running
    wait_for_pod_state(pod_name, namespace, status="Running")

    # Setup Port Forwarding
    path = f"/api/v1/namespaces/{namespace}/pods/{pod_name}/portforward"
    host = config.kube_config.Configuration().host

    # Initialize port forwarding
    port_mapping = {local_port: pod_port}
    time.sleep(timelag)
    try:
        # Establish port forwarding
        pf = portforward.forward(host, path, port_mapping)
        print(
            f"Port forwarding established: localhost:{local_port} -> {pod_name}:{pod_port}"
        )
        pf.start()
    except WebSocketConnectionClosedException as e:
        raise RuntimeError(
            f"Port forwarding connection failed: {str(e)}\n{traceback.format_exc()}"
        )
    except Exception as e:
        raise RuntimeError(f"Unexpected Error: {str(e)}\n{traceback.format_exc()}")
    finally:
        if "pf" in locals():
            pf.close()
            print("Port forwarding process closed.")


def get_deployments(namespace=None):
    """Get a list of active deployments in the namespace

    Args:
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.

    Returns:
        list: A list of kubernetes deployment objects ``kubernetes.client.models.v1_deployment.V1Deployment``
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    config.load_kube_config()
    apps_v1_api = client.AppsV1Api()
    return apps_v1_api.list_namespaced_deployment(namespace=namespace).items


def get_deployment_info(deployment, namespace=None):
    """Get information about a deployment including the requested CPU usage
    the memory per replica, the number of replicas being used, and the name of
    the secret used.

    Args:
        deployment (str/obj): Name of the deployment of a number of replicas pods or a deployment class
        `kubernetes.client.models.v1_deployment.V1Deployment`
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.

    Returns:
        dict: Dictionary containing deployment info containing:

        - "cpu": (float) The number of CPUs requested per replica
        - "memory": (float) The amount of memory requested GB
        - "replicas": (int) the number of replicas running
        - "secret_name": (str) the name of the secret used in this deployment
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    if isinstance(deployment, str):
        deployment = get_deployment(deployment, namespace=namespace)

    n_replicas = int(deployment.spec.replicas)
    cpus = convert_cpu_use(
        deployment.spec.template.spec.containers[0].resources.requests["cpu"],
        issue_warnings=False,
    )
    memory = convert_memory_use(
        deployment.spec.template.spec.containers[0].resources.requests["memory"],
    )
    secret = deployment.spec.template.spec.volumes[0].secret.secret_name

    return {
        "cpu": cpus,
        "memory": memory,
        "replicas": n_replicas,
        "secret_name": secret,
    }


def add_node_affinity(deployment, excluded_nodes):
    """Add node affinity rules to the deployment spec.

    Args:
        deployment (dict): Dictionary defining deployment (most likely from yaml file)
        excluded_nodes (list[str]): A list of node names to exclude

    Returns:
        dict: A revised deployment dictionary containing node exclusion affinity
    """

    if excluded_nodes:
        node_selector_terms = [
            client.V1NodeSelectorTerm(
                match_expressions=[
                    client.V1NodeSelectorRequirement(
                        key="kubernetes.io/hostname",
                        operator="NotIn",
                        values=list(excluded_nodes),
                    )
                ]
            )
        ]

        affinity = client.V1Affinity(
            node_affinity=client.V1NodeAffinity(
                required_during_scheduling_ignored_during_execution=client.V1NodeSelector(
                    node_selector_terms=node_selector_terms
                )
            )
        )

        # Add the affinity to the pod template spec
        deployment["spec"]["template"]["spec"]["affinity"]["nodeAffinity"] = (
            convert_keys_to_camel_case(affinity.to_dict())["nodeAffinity"]
        )

    return deployment


def utilization_per_deployment(keep_key="", namespace=None, verbose=True):
    """Return the utilization of resources per deployment

    Args:
        keep_key (str, optional): A string in the deployment name to signify that it should be kept. Defaults to "".
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.

    Returns:
        dict: Utilization metrics per deployment, where the keys are deployment names and the values are
        dictionaries with:

        - "replicas": (int) number of replicas in the deployment
        - "memory": (dict) utilization metrics for memory

            - "mean": (float) Mean utilization
            - "min": (float) Minimum utilization
            - "max": (float) Maximum utilization
            - "requested": (float) Amount of memory requested in GB per replica
            - "array": (numpy.ndarray) An array of utilization per pod (i.e., replica)

        - "cpu": (dict) utilization metrics for CPUs

            - "mean": (float) Mean utilization
            - "min": (float) Minimum utilization
            - "max": (float) Maximum utilization
            - "requested": (float) Number of CPUs requested per replica
            - "array": (numpy.ndarray) An array of utilization per pod (i.e., replica)

    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    deployments = get_deployments(namespace=namespace)
    deployment_info = {
        dep.metadata.name: get_deployment_info(dep, namespace=namespace)
        for dep in deployments
    }
    dep_pod_info = sort_pods_by_deployment(
        get_pods_resource_info(namespace=namespace),
        list(deployment_info.keys()),
        keep_key=keep_key,
    )
    output = {}
    if verbose:
        print(
            "Dep Name, Nreplicas, |  Avg Mem Ut%, Min Mem Ut%, Max Mem Ut%, Mem Req, |  Avg CPU Ut%, Min CPU Ut%, Max"
            " CPU Ut%, CPU Req"
        )
        print(
            "_____________________________________________________________________________"
        )
    for dep_name, pod_info in dep_pod_info.items():
        try:
            cpu_usage = (
                100
                * np.array([x["cpu"] for _, x in pod_info.items()])
                / deployment_info[dep_name]["cpu"]
            )
            memory_usage = (
                100
                * np.array([x["memory"] for _, x in pod_info.items()])
                / deployment_info[dep_name]["memory"]
            )
            output[dep_name] = {
                "replicas": deployment_info[dep_name]["replicas"],
                "memory": {
                    "mean": np.mean(memory_usage),
                    "min": np.min(memory_usage),
                    "max": np.max(memory_usage),
                    "requested": deployment_info[dep_name]["memory"],
                    "array": memory_usage,
                },
                "cpu": {
                    "mean": np.mean(cpu_usage),
                    "min": np.min(cpu_usage),
                    "max": np.max(cpu_usage),
                    "requested": deployment_info[dep_name]["cpu"],
                    "array": cpu_usage,
                },
            }
            if verbose:
                print(
                    (
                        f'{dep_name}\t{output[dep_name]["replicas"]}\t|\t'
                        f'{output[dep_name]["memory"]["mean"]:.1f}\t{output[dep_name]["memory"]["min"]:.1f}\t'
                        f'{output[dep_name]["memory"]["max"]:.1f}\t{output[dep_name]["memory"]["requested"]:.1f}\t|\t'
                        f'{output[dep_name]["cpu"]["mean"]:.1f}\t{output[dep_name]["cpu"]["min"]:.1f}\t'
                        f'{output[dep_name]["cpu"]["max"]:.1f}\t{output[dep_name]["cpu"]["requested"]}'
                    )
                )
        except Exception:
            warnings.warn(f"Could not calculate utilization for deployment: {dep_name}")

    if verbose:
        print("\n")
    return output


def scale_deployment(deployment_name, replicas, namespace=None, verbose=True):
    """Scale a deployment up or down, where if it is scaled down, the pods with lower CPU
    usage will be preferably deleted

    Args:
        deployment_name (str): String signifying the deployment name
        replicas (int): Number of replicas to change it to
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    config.load_kube_config()

    dep_info = get_deployment_info(deployment_name, namespace=namespace)
    if dep_info["replicas"] == replicas:
        print("The number of replicas will not change")
    elif dep_info["replicas"] > replicas:
        pod_dict = get_pods_resource_info(
            keep_key=deployment_name, warn_zero_use=False, namespace=namespace
        )
        pod_list = list(pod_dict.keys())
        pod_list.sort(
            key=lambda x: -np.inf if pod_dict[x]["cpu"] is None else pod_dict[x]["cpu"]
        )

        for i in range(dep_info["replicas"] - replicas):
            delete_pod(pod_list[i], namespace=namespace)

    try:
        # Apply the patch to update the deployment
        patch_body = {"spec": {"replicas": replicas}}
        client.AppsV1Api().patch_namespaced_deployment(
            name=deployment_name, namespace=namespace, body=patch_body
        )

        if verbose:
            print(f"Deployment '{deployment_name}' scaled to {replicas} replicas.")

    except ApiException as e:
        raise ApiException(f"Error scaling deployment: {e}")
