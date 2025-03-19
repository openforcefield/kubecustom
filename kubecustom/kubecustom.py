"""Combined functions expected to be of most common use."""

import os
import yaml
import shutil
from pkg_resources import resource_filename

from .utils import file_find_replace, load_template_paths
from .secret import create_secret, delete_secret, MyData
from .deployment import create_deployment, delete_deployment


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
    filename_manager = os.path.join(path, f"manager_{configuration_type}.yaml")
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
