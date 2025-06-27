"""Create, delete, and extract information for pods"""

import warnings
from collections import defaultdict, Counter

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException


from .utils import convert_cpu_use, convert_memory_use, MyData

try:
    MyDataInstance = MyData()
except Exception:
    warnings.warn(
        "Could not import namespace or container_name, functions imported from this module may not operate as expected"
        " until you set manually with 'kubecustom.MyData.add_data()' or interactively with `python -c 'from kubecustom"
        " import MyData; obj=MyData(); obj.add_interactively()'`"
    )


def delete_pod(pod_name, namespace=None, verbose=False):
    """Delete a Kubernetes pod

    Args:
        pod_name (str): Name identifying pod
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    core_v1_api = client.CoreV1Api()

    try:
        core_v1_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
        if verbose:
            print(f"Pod '{pod_name}' deleted from namespace '{namespace}'.")

    except ApiException as e:
        if e.status == 404:
            ApiException(f"Pod '{pod_name}' not found in namespace '{namespace}'.")
        else:
            ApiException(f"Error deleting pod: {e}")


def get_pod_list(deployment_name=None, namespace=None):
    """Get a list of Kubernetes pod objects, optionally filtered by deployment.

    Args:
        deployment_name (_type_, optional): Name of deployment to restrict pod list. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.

    Returns:
        list: List of Kubernetes pod objects ``kubernetes.client.models.v1_pod.V1Pod``
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    config.load_kube_config()
    pods = client.CoreV1Api().list_namespaced_pod(namespace=namespace)
    if deployment_name is not None:
        pods = [
            pod
            for pod in pods.items
            if pod.metadata.owner_references is not None
            and all(
                owner.kind == "ReplicaSet"
                and "-".join(owner.name.split("-")[:-1]) == deployment_name
                for owner in pod.metadata.owner_references
            )
        ]
    else:
        pods = list(pods.items)

    return pods


def pod_state(pod, previous=False):
    """Get pod status and associated information

    Status will return None if there is no status information for the states: running, waiting, or terminated.

    Args:
        pod (obj): Kubernetes pod class instance of ``kubernetes.client.models.v1_pod.V1Pod``
        previous (bool, optional): Obtain previous pod state. Defaults to False.

    Returns:
        state (str): State of the current pod, either running, waiting, or terminated
        status (str): Reason for the current state
        status_info (dict): Additional information about the pod status changed from
        ``kubernetes.client.models.v1_container_state_waiting.V1ContainerStateWaiting`` to a dictionary
    """

    try:
        if not previous:
            status = pod.status.container_statuses[0].state
        else:
            status = pod.status.container_statuses[0].last_state
    except Exception:
        return None, None, None

    if status.running is not None:
        state = "running"
        status_info = status.running.to_dict()
        status = "Running"
    elif status.terminated is not None:
        state = "terminated"
        status_info = status.terminated.to_dict()
        status = status_info["reason"]
    elif status.waiting is not None:
        state = "waiting"
        status_info = status.waiting.to_dict()
        status = status_info["reason"]
    else:
        state, status, status_info = None, None, None

    return state, status, status_info


def sort_pods_by_deployment(pods, deployment_names, keep_key=""):
    """Sort pods into deployments.

    Args:
        pods (dict): Keys are pod_names and values can be anything
        deployment_names (list): deployment names expected to overlap with a number of pod_names
        keep_key (str, optional): A string in the deployment name to signify that it should be kept. Defaults to "".

    Returns:
        dict: A dictionary with deployments as keys and values are the same structure as the input dictionary.
    """

    if not isinstance(pods, dict):
        raise ValueError("Expected a dictionary where the keys are pod names")

    # Sort deployment names longest to shortest
    # to ensure that a shorter name will not overlap with a longer name
    deployment_names.sort(key=lambda x: -len(x))
    pods_sorted = defaultdict(dict)
    for dep_name in deployment_names:
        if keep_key not in dep_name:
            continue
        pods_sorted[dep_name] = {
            pod_name: value
            for pod_name, value in pods.items()
            if "-".join(pod_name.split("-")[:-2]) == dep_name
        }

    return pods_sorted


def delete_pods_by_status(status, deployment_name=None, namespace=None, verbose=False):
    """Delete pods by their status

    Args:
        status (str): Status of pod, as seen in ``kubectl get pods``
        deployment_name (_type_, optional): Name of deployment to restrict pod list. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.
        verbose (bool, optional): Print pod names as they are deleted. Defaults to True.
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    status_current = get_pods_status_info(
        namespace=namespace, deployment_name=deployment_name
    )
    for pod_name, current in status_current.items():
        current_status = (
            "none" if current["status"] is None else current["status"].lower()
        )
        if current_status == status.lower():
            delete_pod(pod_name, namespace=namespace, verbose=verbose)


def delete_pods_by_state(state, deployment_name=None, namespace=None, verbose=False):
    """Delete pods by their status

    Args:
        state (str): State of pod, as seen in ``kubectl get pods``
        deployment_name (_type_, optional): Name of deployment to restrict pod list. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.
        verbose (bool, optional): Print pod names as they are deleted. Defaults to True.
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    status_current = get_pods_status_info(
        namespace=namespace, deployment_name=deployment_name
    )
    for pod_name, current in status_current.items():
        current_status = (
            "none" if current["state"] is None else current["state"].lower()
        )
        if current_status == state.lower():
            delete_pod(pod_name, namespace=namespace, verbose=verbose)


def get_pods_status_info(previous=False, deployment_name=None, namespace=None):
    """Get status and IP address information for pods, optionally filtered by deployment.

    Args:
        previous (bool, optional): Obtain previous pod state. Defaults to False.
        deployment_name (str, optional): Name of deployment to restrict pod list. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.

    Returns:
        dict: Per pod information, where each key is a pod name and each value is a dictionary with:

         - "pod_name" (str): Name of the pod
         - "namespace" (str): Namespace that the pod is in
         - "labels" (dict[str]): Dictionary of labels associated with the pod
         - "annotations" (dict[str]): Dictionary of annotations on the pod containing some ids and IPs
         - "creation_timestamp" (datetime): Timestamp when the pod was created
         - "deletion_timestamp" (datetime or None): Timestamp when the pod was deleted, or None if not deleted
         - "uid" (str): Unique identifier for the pod
         - "owner_references" (list[dict]): List of owner reference dictionaries for the pod
         - "node_name" (str): Name of the node the pod is scheduled on
         - "service_account" (str): Name of the service account used by the pod
         - "priority" (int or None): Priority value of the pod
         - "scheduler_name" (str): Name of the scheduler used for the pod
         - "containers" (list[str]): List of container names in the pod
         - "init_containers" (list[str]): List of init container names in the pod
         - "volumes" (list[str]): List of volume names attached to the pod
         - "host_ip" (str): IP address of the host node
         - "pod_ip" (str): IP address assigned to the pod
         - "phase" (str): Current phase of the pod (e.g., Running, Pending)
         - "restart_count" (int or None): Number of times the main container has restarted
         - "state" (str or None): State of the pod ("running", "waiting", "terminated", or None)
         - "status" (str or None): Status reason for the current state
         - "status_info" (dict or None): Additional information about the pod status
         - "start_time" (datetime or None): Time when the pod started
         - "container_statuses" (list[dict]): List of container status dictionaries
         - "init_container_statuses" (list[dict]): List of init container status dictionaries
         - "conditions" (list[dict]): List of condition dictionaries for the pod
         - "qos_class" (str or None): Quality of Service class assigned to the pod
         - "message" (str or None): Message about the pod's status, if any
         - "reason" (str or None): Reason for the pod's current condition, if any

    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    pods = get_pod_list(deployment_name=deployment_name, namespace=namespace)
    if not pods:
        raise ValueError(
            f"There are no pods in namespace {namespace}, deployment_name {deployment_name}"
        )

    pod_info = {}
    for pod in pods:
        state, status, status_info = pod_state(pod, previous=previous)
        try:
            restart_count = pod.status.container_statuses[0]["restart_count"]
        except Exception:
            restart_count = None

        pod_info[pod.metadata.name] = {
            "pod_name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "labels": pod.metadata.labels,
            "annotations": pod.metadata.annotations,
            "creation_timestamp": pod.metadata.creation_timestamp,
            "deletion_timestamp": pod.metadata.deletion_timestamp,
            "uid": pod.metadata.uid,
            "owner_references": [
                owner.to_dict() for owner in (pod.metadata.owner_references or [])
            ],
            "node_name": pod.spec.node_name,
            "service_account": pod.spec.service_account_name,
            "priority": pod.spec.priority,
            "scheduler_name": pod.spec.scheduler_name,
            "containers": [container.name for container in pod.spec.containers],
            "init_containers": [
                container.name for container in (pod.spec.init_containers or [])
            ],
            "volumes": [volume.name for volume in (pod.spec.volumes or [])],
            "host_ip": pod.status.host_ip,
            "pod_ip": pod.status.pod_ip,
            "phase": pod.status.phase,
            "restart_count": restart_count,
            "state": state,
            "status": status,
            "status_info": status_info,
            "start_time": pod.status.start_time,
            "container_statuses": [
                cs.to_dict() for cs in (pod.status.container_statuses or [])
            ],
            "init_container_statuses": [
                cs.to_dict() for cs in (pod.status.init_container_statuses or [])
            ],
            "conditions": [cond.to_dict() for cond in (pod.status.conditions or [])],
            "qos_class": getattr(pod.status, "qos_class", None),
            "message": getattr(pod.status, "message", None),
            "reason": getattr(pod.status, "reason", None),
        }

    return pod_info


def get_pods_resource_info(
    keep_key="",
    warn_zero_use=True,
    verbose=False,
    namespace=None,
    container_name=None,
):
    """Output pods CPU and memory usage (GB) along with labels.

    Args:
        keep_key (str, optional): A short string that must be in a pod name to report values
        warn_zero_use (bool, optional): Toggle warnings on/off for nodes that are not actively using resources.
        Defaults to True.
        verbose (bool, optional): Print pods information as it's being generated, including the CPU and memory use
        before and after unit conversions. Defaults to False.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.
        container_name (str, optional): Kubernetes container name used in your deployments. Defaults to
        :func:`kubecustom.secret.MyData.get_data("container_name")`.

    Returns:
        dict: Dictionary containing pod info where the keys are pod names, and the values are dictionaries containing:

        - "cpu": (float) CPU usage in number of whole CPUs
        - "memory": (float) Memory usage in GB
        - "labels": (dict) {label_type: label_value}
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace
    container_name = (
        MyDataInstance.get_data("container_name")
        if container_name is None
        else container_name
    )

    config.load_kube_config()
    api = client.CustomObjectsApi()

    group, version = "metrics.k8s.io", "v1beta1"
    resource = "pods"

    pod_list = [pod.metadata.name for pod in get_pod_list(namespace=namespace)]
    pod_metrics = api.list_namespaced_custom_object(group, version, namespace, resource)

    # Process and display the metrics
    output = defaultdict(dict)
    for pod in pod_metrics["items"]:
        pod_name = pod["metadata"]["name"]
        pod_list.remove(pod_name)
        if keep_key not in pod_name:
            continue
        containers = pod["containers"]
        for container in containers:
            if container["name"] != container_name:
                continue
            cpu_usage = convert_cpu_use(container["usage"]["cpu"])
            memory_usage = convert_memory_use(container["usage"]["memory"])
            if warn_zero_use and cpu_usage == str(0) and memory_usage == str(0):
                warnings.warn(f"Pod {pod_name} is using zero resources")
            if verbose:
                print(
                    f"Pod: {pod_name}, Container: {container_name}, CPU: {container['usage']['cpu']} {cpu_usage},\t"
                    f"Memory: {container['usage']['memory']} {memory_usage}GB,\tLabels: {pod['metadata']['labels']}"
                )

            output[pod_name] = {
                "cpu": cpu_usage,
                "memory": memory_usage,
                "labels": pod["metadata"]["labels"],
            }

    for pod_name in pod_list:
        if verbose:
            print(
                "Pod: {pod_name}, Container: None, CPU: None None,\tMemory: None None,\tLabels: None"
            )

        output[pod_name] = {
            "cpu": None,
            "memory": None,
            "labels": None,
        }

    return output


def get_active_tasks(pod_list, verbose=True, namespace=None):
    """Retrieve the number of active tasks from a list of pod objects

    Args:
        pod_list (list): List of kubernetes pod objects
        verbose (bool, optional): Print pod names and number of active tasks. Defaults to True.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.

    Returns:
        pod_tasks (dict): Dictionary of pod names and the number of active tasks each pod has
        stats (dict): Dictionary of the number of tasks a pod could have, and the number of pods
        in that state.
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace
    output = defaultdict(int)
    stats = Counter()
    for pod in pod_list:
        pod_name = pod.metadata.name
        try:
            log = (
                client.CoreV1Api()
                .read_namespaced_pod_log(
                    namespace=namespace,
                    name=pod_name,
                )
                .split("\n")
            )

            for line in reversed(log):
                if "active tasks" in line:
                    line_array = line.split()
                    tasks = int(line_array[-7])
                    output[pod_name] = tasks
                    break

            if pod_name not in output:
                output[pod_name] = "None Yet"

        except Exception:
            output[pod_name] = None

        stats[output[pod_name]] += 1
        if verbose:
            print(f"    Pod: {pod_name}, Number of Tasks {output[pod_name]}")

    if verbose:
        print("Count of Number of Tasks")
        for task, count in stats.items():
            print(f"    {task}: {count}")
        print(
            f"Out of {len(pod_list)} pods. Note that some pods labeled as 'Not Yet' may not contribute to this count."
        )

    return output, stats


def print_pods_summary(deployment_name=None, namespace=None):
    """Print a summary of pod status

    Args:
        deployment_name (_type_, optional): Name of deployment to restrict pod list. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    status_current = get_pods_status_info(
        deployment_name=deployment_name, namespace=namespace
    )
    status_previous = get_pods_status_info(
        deployment_name=deployment_name, namespace=namespace, previous=True
    )
    keep_key = deployment_name if deployment_name is not None else ""
    pod_resources = get_pods_resource_info(
        keep_key=keep_key, warn_zero_use=False, namespace=namespace
    )

    print(
        "Pod Name,\t\t\t\tRestart Count,\tMemory,\tCPUs,\t|\tCurrent State,\tCurrent Status,\t|\tPrevious State,\t"
        "Previous Status"
    )
    for pod_name, current in status_current.items():
        if pod_resources[pod_name]:
            if pod_resources[pod_name]["memory"] is not None:
                print_str = (
                    f'{pod_name},\t{current["restart_count"]},\t{pod_resources[pod_name]["memory"]:.1f},\t'
                    f'{pod_resources[pod_name]["cpu"]:.1f}'
                )
            else:
                print_str = f'{pod_name},\t{current["restart_count"]},\tNone,\tNone'
        else:
            print_str = f'{pod_name},\t{current["restart_count"]},\tNone,\tNone'
        print(
            print_str
            + (
                f'\t|\t{current["state"]},\t{current["status"]},\t'
                f'|\t{status_previous[pod_name]["state"]},\t{status_previous[pod_name]["status"]}'
            )
        )
