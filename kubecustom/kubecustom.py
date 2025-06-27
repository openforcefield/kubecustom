"""Combined functions expected to be of most common use."""

import sched
import time
import warnings
import os
import yaml
import shutil
import pandas as pd
from pkg_resources import resource_filename

from .utils import file_find_replace, load_template_paths, repeat_task
from .secret import create_secret, delete_secret, MyData
from .deployment import create_deployment, delete_deployment, get_deployments
from .pod import get_pods_status_info


with open(resource_filename("kubecustom", "template_files/template_keys.yaml")) as f:
    _attributes = yaml.safe_load(f)

MyDataInstance = MyData()


def get_deployment_name(tag):
    """Get the deployment name using a provided tag, and values from an instance of ``MyData``.

    Args:
        tag (str): Tag used to identify tasks, if the github compute tag is "compute-pr000" this tag should be "pr000",
        however if the mw feature is present, it might be "pr000-300"
    """

    user = MyDataInstance.get_data("user")
    configuration_name = MyDataInstance.configuration
    return f"{user}-{configuration_name}-{tag}"


def create_secret_deployment(
    path,
    tag,
    cpus,
    memory,
    replicas=2,
    excluded_nodes=None,
    namespace=None,
    verbose=True,
):
    """Create a secret and deployment with specified resources using template yaml files

    Deployment names will be f"{user}-{tag}"

    Args:
        path (str): Path to which template development.yaml and manager.yaml files will be saves
        tag (str): Tag used to identify tasks, if the github compute tag is "compute-pr000" this tag should be "pr000",
        however if the mw feature is present, it might be "pr000-300"
        cpus (int): Number of CPUs to use per replica (i.e., pod)
        memory (int): Number of GB of memory to request per replica
        functions. For example, 'my-organization-my-initials'. Defaults to :func:`kubecustom.secret.MyData.get_data```("user")``
        replicas (int, optional): Number of replicas (i.e., pods) to create. Defaults to 2.
        excluded_nodes (list, optional): List of node names to exclude. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data```("namespace")``.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.

    Raises:
        ValueError: Check that target directory for jobs exists
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace
    configuration_type = MyDataInstance._configuration_type

    if not os.path.isdir(path):
        raise ValueError(f"Directory could not be found: {path}")

    filename_deployment = os.path.join(path, f"deployment_{configuration_type}.yaml")
    filename_manager = os.path.join(path, "manager.yaml")
    template_deployment, template_manager = load_template_paths(configuration_type)

    shutil.copyfile(template_deployment, filename_deployment)
    shutil.copyfile(template_manager, filename_manager)

    deployment_name = get_deployment_name(tag)

    find_replace = {
        y[0]: MyDataInstance.get_data(x)
        for x, y in _attributes[configuration_type].items()
    }
    find_replace.update(
        {
            "DEPLOYMENTNAME": deployment_name,
            "TAG": tag,
            "CPUS": cpus,
            "MEMORY": memory,
            "REPLICAS": replicas,
        }
    )
    file_find_replace(filename_deployment, find_replace)
    file_find_replace(filename_manager, find_replace)

    create_secret(
        filename_manager, deployment_name, namespace=namespace, verbose=verbose
    )
    create_deployment(
        filename_deployment,
        excluded_nodes=excluded_nodes,
        namespace=namespace,
        verbose=verbose,
    )


def delete_secret_deployment(deployment_name, namespace=None, verbose=True):
    """Delete a deployment and secret, assuming they have the same name

    Args:
        deployment_name (str): Name of deployment and secret
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data```("namespace")``.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace
    delete_secret(deployment_name, namespace=namespace, verbose=verbose)
    delete_deployment(deployment_name, namespace=namespace, verbose=verbose)


def update_pods_status_info(filename="pod_log.csv", keep_key="", namespace=None):
    """Update file with status and IP address information for pods, optionally filtered by deployment.

    Args:
        filename (str, optional): Filename to store pod information. Defaults to "pod_log.csv",
        keep_key (str, optional): A string in the deployment name to signify that it should be kept. Defaults to "".
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data```("namespace")``.
    """
    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    deployments = get_deployments(namespace=namespace)
    deployment_names = [
        dep.metadata.name for dep in deployments if keep_key in dep.metadata.name
    ]

    fname_complete = ".".join(filename.split(".")[:-1]) + "_complete.csv"
    fields_new = [
        "pod_name",
        "uid",
        "creation_timestamp",
        "owner_references[0]['name']",
        "node_name",
        "service_account",
        "scheduler_name",
        "host_ip",
        "pod_ip",
        "start_time",
    ]
    fields_update = [
        "deletion_timestamp",
        "phase",
        "restart_count",
        "state",
        "qos_class",
        "status",
        "message",
        "reason",
    ]
    if not os.path.isfile(fname_complete):
        open(fname_complete, "w").write(f"{', '.join(fields_new + fields_update)}\n")
    if not os.path.isfile(filename):
        open(filename, "w").write(f"{', '.join(fields_new + fields_update)}\n")

    for dep_name in deployment_names:
        pods_info = get_pods_status_info(deployment_name=dep_name, namespace=namespace)
        pod_names = set(pods_info.keys())
        df = pd.read_csv(filename, skipinitialspace=True)
        df_pod_names = set(df["pod_name"])

        # Pods in df but not in pod_names (to be removed and archived)
        removed_pods = df_pod_names - pod_names
        removed_rows = df[df["pod_name"].isin(removed_pods)]
        df = df[~df["pod_name"].isin(removed_pods)]
        if not removed_rows.empty:
            removed_rows.to_csv(fname_complete, mode="a", header=False, index=False)

        # Pods in both df and pod_names (update fields_update)
        shared_pods = df_pod_names & pod_names
        for pod_name in shared_pods:
            idx = df.index[df["pod_name"] == pod_name][0]
            for field in fields_update:
                if field == "deletion_timestamp":
                    if pods_info[pod_name][field] is not None:
                        df.at[idx, field] = pods_info[pod_name][field].strftime(
                            "%Y-%m-%d %H:%M:%S %Z"
                        )
                    else:
                        df.at[idx, field] = None
                else:
                    df.at[idx, field] = pods_info[pod_name][field]

        # Pods in pod_names but not in df (add new rows)
        new_pods = pod_names - df_pod_names
        for pod_name in new_pods:
            pod_info = pods_info[pod_name]
            row = {
                field: pod_info.get(field, "") for field in fields_new + fields_update
            }
            row["owner_references[0]['name']"] = pod_info["owner_references"][0]["name"]
            row["creation_timestamp"] = pod_info["creation_timestamp"].strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
            new_row_df = pd.DataFrame([row])
            if (
                not new_row_df.empty
                and new_row_df.notnull().any().any()
                and len(new_row_df) >= 1
            ):
                if not df.empty and df.notnull().any().any() and len(df) >= 1:
                    df = pd.concat([new_row_df, df], ignore_index=True)
                else:
                    df = new_row_df

        df.to_csv(filename, index=False)


def monitor_pods(filename, keep_key="", timelag=20, namespace=None, silence=False):
    """Monitor pod information and store in a file

    Args:
        filename (str): Filename to store pod information
        timelag (int, optional): Time lag in seconds before updating. Defaults to 20.
        keep_key (str, optional): A string in the deployment name to signify that it should be kept. Defaults to "".
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data```("namespace")``.
        silence (bool, optional): Whether to silence warnings. Defaults to False.
    """
    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace
    if silence:
        warnings.filterwarnings("ignore")

    kwargs = {
        "filename": filename,
        "keep_key": keep_key,
        "namespace": namespace,
    }

    update_pods_status_info(**kwargs)
    my_scheduler = sched.scheduler(time.time, time.sleep)
    my_scheduler.enter(
        timelag,
        1,
        repeat_task,
        (my_scheduler, update_pods_status_info, kwargs, timelag),
    )
    my_scheduler.run()
