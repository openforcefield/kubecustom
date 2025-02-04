"""Combined functions expected to be of most common use."""

import os
import shutil
import warnings

from .utils import file_find_replace, load_template_paths
from .secret import create_secret, delete_secret, MyData
from .deployment import create_deployment, delete_deployment

try:
    MyDataInstance = MyData()
    _user = MyDataInstance.get_user()
    _namespace = MyDataInstance.get_namespace()
except Exception:
    _namespace = "default"
    _user = "default"
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
    user=_user,
    replicas=2,
    excluded_nodes=None,
    namespace=_namespace,
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
        functions.
        For example, 'my-organization-my-initials'. Defaults to :func:`kubecustom.secret.MyData.get_user`
        replicas (int, optional): Number of replicas (i.e., pods) to create. Defaults to 2.
        excluded_nodes (list, optional): List of node names to exclude. Defaults to None.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.

    Raises:
        ValueError: Check that target directory for jobs exists
    """

    if not os.path.isdir(path):
        raise ValueError(f"Directory could not be found: {path}")

    cwd = os.getcwd()
    os.chdir(path)

    filename_deployment = os.path.join((path, "deployment.yaml"))
    filename_manager = os.path.join((path, "manager.yaml"))
    template_deployment, template_manager = load_template_paths()

    shutil.copyfile(template_deployment, filename_deployment)
    shutil.copyfile(template_manager, filename_manager)

    find_replace = {
        "USER": user,
        "TAG": tag,
        "CPUs": cpus,
        "MEMORY": memory,
        "REPLICAS": replicas,
    }
    file_find_replace("deployment.yaml", find_replace)
    find_replace.update(
        {
            "USERNAME": MyDataInstance.get_username(),
            "PASSWORD": MyDataInstance.get_password(),
            "CONTAINERNAME": MyDataInstance.get_container_name(),
            "CONTAINERIMAGE": MyDataInstance.get_container_image(),
            "CLUSTER": MyDataInstance.get_cluster(),
        }
    )
    file_find_replace("manager.yaml", find_replace)

    deployment_name = f"{user}-{tag}"
    create_secret("manager.yaml", deployment_name, namespace=namespace, verbose=verbose)
    create_deployment(
        "deployment.yaml",
        excluded_nodes=excluded_nodes,
        namespace=namespace,
        verbose=verbose,
    )

    os.chdir(cwd)


def delete_secret_deployment(deployment_name, namespace=_namespace, verbose=True):
    """Delete a deployment and secret, assuming they have the same name

    Args:
        deployment_name (str): Name of deployment and secret
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    delete_secret(deployment_name, namespace=namespace, verbose=verbose)
    delete_deployment(deployment_name, namespace=namespace, verbose=verbose)
