"""Combined functions expected to be of most common use."""

import os
import shutil
import warnings

from .utils import file_find_replace, load_template_paths
from .secret import create_secret, delete_secret, MyData
from .deployment import create_deployment, delete_deployment

try:
    MyDataInstance = MyData()
except Exception:
    warnings.warn(
        "Could not import namespace or user strings, functions imported from this module may not operate as expected "
        "until you set manually with 'kubecustom.MyData.add_data()' or interactively with `python -c 'from kubecustom "
        "import MyData; obj=MyData(); obj.add_interactively()'`"
    )


def create_secret_deployment(
    path,
    tag,
    cpus,
    memory,
    user=None,
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
        user (str, optional): Initials of user, added to secret and deployment names for use as a 'keep_key' in other
        functions. For example, 'my-organization-my-initials'. Defaults to :func:`kubecustom.secret.MyData.get_user`
        replicas (int, optional): Number of replicas (i.e., pods) to create. Defaults to 2.
        excluded_nodes (list, optional): List of node names to exclude. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.

    Raises:
        ValueError: Check that target directory for jobs exists
    """

    user = MyDataInstance.get_user() if user is None else user
    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    if not os.path.isdir(path):
        raise ValueError(f"Directory could not be found: {path}")

    filename_deployment = os.path.join(path, "deployment.yaml")
    filename_manager = os.path.join(path, "manager.yaml")
    template_deployment, template_manager = load_template_paths()

    shutil.copyfile(template_deployment, filename_deployment)
    shutil.copyfile(template_manager, filename_manager)

    find_replace = {
        "USER": MyDataInstance.get_user(),
        "TAG": tag,
        "CPUS": cpus,
        "MEMORY": memory,
        "REPLICAS": replicas,
        "CONTAINERNAME": MyDataInstance.get_container_name(),
        "CONTAINERIMAGE": MyDataInstance.get_container_image(),
    }
    file_find_replace(filename_deployment, find_replace)

    find_replace = {
        "USERNAME": MyDataInstance.get_username(),
        "PASSWORD": MyDataInstance.get_password(),
        "CLUSTER": MyDataInstance.get_cluster(),
        "CPUS": cpus,
        "MEMORY": memory,
        "TAG": tag,
    }
    file_find_replace(filename_manager, find_replace)

    deployment_name = f"{user}-{tag}"
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
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace
    delete_secret(deployment_name, namespace=namespace, verbose=verbose)
    delete_deployment(deployment_name, namespace=namespace, verbose=verbose)
