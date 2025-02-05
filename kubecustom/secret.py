"""Create and delete secrets"""

import os
import base64
import warnings

from InquirerPy import prompt
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from pkg_resources import resource_filename

_init_filename = resource_filename("kubecustom", "template_files/secret.txt")

questions = [
    {
        "type": "input",
        "message": "What is your USERNAME for submission with a kubernetes secret?",
        "name": "_username",
    },
    {
        "type": "input",
        "message": "What is your PASSWORD for submission with a kubernetes secret?",
        "name": "_password",
    },
    {
        "type": "input",
        "message": (
            "What string should represent your personal deployments/secrets (e.g., "
            "'my-organization-my-initials')?"
        ),
        "name": "_user",
    },
    {
        "type": "input",
        "message": "What is your kubernetes namespace?",
        "name": "_namespace",
    },
    {
        "type": "input",
        "message": "What would you like your kubernetes container name to be (e.g., 'my-org-pod')?",
        "name": "_container_name",
    },
    {
        "type": "input",
        "message": "What GitHub image should be used to make containers? (e.g., ghcr.io/...)",
        "name": "_container_image",
    },
    {
        "type": "input",
        "message": "What is the name of your kubernetes cluster?",
        "name": "_cluster",
    },
]


class MyData:
    # These are in the same order as lines in the secret.txt file
    _attributes = [
        "_username",
        "_password",
        "_user",
        "_namespace",
        "_container_name",
        "_container_image",
        "_cluster",
    ]

    def __init__(self):
        _file_contents = open(_init_filename, "r").readlines()
        for i, attr in enumerate(self._attributes):
            value = (
                None
                if _file_contents[i].split()[1] == "None"
                else _file_contents[i].split()[1]
            )
            setattr(self, attr, value)

    def add_data(
        self,
        username=None,
        password=None,
        user=None,
        namespace=None,
        container_name=None,
        container_image=None,
        cluster_name=None,
    ):
        """Set personal information manually. If None is passed, the attribute does not change.

        Args:
            username (str, optional): Kubernete username for secret. Defaults to None.
            password (str, optional): Kubernetes password for secret. Defaults to None.
            user (str, optional): YOUR personal identifier for deployments and secrets, e.g.,
            'my-organization-my-initials'. Defaults to None.
            namespace (str, optional): Your team namespace. Defaults to None.
            container_name (str, optional): Name for type of deployed containers. Defaults to None.
            container_image (str, optional): Link to container image, e.g., ghcr.io/...
            cluster_name (str, optional): Name of kubernetes cluster
        """

        if username is not None and username != self._username:
            self._username = username
        elif password is not None and password != self._password:
            self._password = password
        elif user is not None and user != self._user:
            self._user = user
        elif namespace is not None and namespace != self._namespace:
            self._namespace = namespace
        elif container_name is not None and container_name != self._container_name:
            self._container_name = container_name
        elif container_image is not None and container_image != self._container_image:
            self._container_image = container_image
        elif cluster_name is not None and cluster_name != self._cluster:
            self._cluster = cluster_name

        self._update_file()

    def add_interactively(self):
        """Spawn an interactive prompt to set personal information."""
        print(
            "Let's set your personal information locally. Hit 'enter' to skip and set to None."
        )
        result = prompt(questions)
        for key, value in result.items():
            setattr(self, key, value)

        self._update_file()

    def _update_file(self):
        _file_contents = open(_init_filename, "r").readlines()
        with open(_init_filename, "w") as f:
            for i, line in enumerate(_file_contents):
                line_array = line.split()
                attr = getattr(self, self._attributes[i])
                line_array = [line_array[0], str(attr if attr is not None else "None")]
                f.write(" ".join(line_array) + "\n")

    def get_username(self):
        """Get kubernetes username for secret."""
        if self._username is None:
            raise ImportError(
                "'username' missing. Personal kubernetes information must be initiated. Set manually with"
                " kubecustom.MyData.add_data() or interactively with `python -c 'from kubecustom import "
                "MyData; obj=MyData(); obj.add_interactively()'`"
            )
        return self._username

    def get_password(self):
        """Get kubernetes password for secret."""
        if self._password is None:
            raise ImportError(
                "'password' missing. Personal kubernetes information must be initiated. Set manually with"
                " kubecustom.MyData.add_data() or interactively with `python -c 'from kubecustom import "
                "MyData; obj=MyData(); obj.add_interactively()'`"
            )
        return self._password

    def get_user(self):
        """Get YOUR personal identifier for deployments and secrets, e.g., 'my-organization-my-initials'."""
        if self._user is None:
            raise ImportError(
                "'user' missing. Personal kubernetes information must be initiated. Set manually with"
                " kubecustom.MyData.add_data() or interactively with `python -c 'from kubecustom import "
                "MyData; obj=MyData(); obj.add_interactively()'`"
            )
        return self._user

    def get_namespace(self):
        """Get your team namespace"""
        if self._namespace is None:
            raise ImportError(
                "'namespace' missing. Personal kubernetes information must be initiated. Set manually with"
                " kubecustom.MyData.add_data() or interactively with `python -c 'from kubecustom import "
                "MyData; obj=MyData(); obj.add_interactively()'`"
            )
        return self._namespace

    def get_container_name(self):
        """Name for type of deployed containers"""
        if self._container_name is None:
            raise ImportError(
                "'container_name' missing. Personal kubernetes information must be initiated. Set manually with"
                " kubecustom.MyData.add_data() or interactively with `python -c 'from kubecustom import MyData; "
                "obj=MyData(); obj.add_interactively()'`"
            )
        return self._container_name

    def get_container_image(self):
        """Link to github image of container"""
        if self._container_image is None:
            raise ImportError(
                "'container_image' missing. Personal kubernetes information must be initiated. Set manually with"
                " kubecustom.MyData.add_data() or interactively with `python -c 'from kubecustom import MyData; "
                "obj=MyData(); obj.add_interactively()'`"
            )
        return self._container_image

    def get_cluster(self):
        """Name of kubernetes cluster"""
        if self._cluster is None:
            raise ImportError(
                "'cluster_name' missing. Personal kubernetes information must be initiated. Set manually with"
                " kubecustom.MyData.add_data() or interactively with `python -c 'from kubecustom import MyData; "
                "obj=MyData(); obj.add_interactively()'`"
            )
        return self._cluster


# ___________________________________________________________________________________________________

try:
    MyDataInstance = MyData()
except Exception:
    warnings.warn(
        "Could not import namespace, functions imported from this module may not operate as expected until "
        "you set manually with 'kubecustom.MyData.add_data()' or interactively with `python -c 'from "
        "kubecustom import MyData; obj=MyData(); obj.add_interactively()'`"
    )


def create_secret(manager_yaml, secret_name, namespace=None, verbose=True):
    """Create a secret from a manager.yaml

    Args:
        manager_yaml (str): Filename and path to a manager.yaml file
        secret_name (str): Name of secret
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.

    Raises:
        FileExistsError: Check that manager.yaml file exists
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    config.load_kube_config()  # Refresh credentials

    # Create secret
    if not os.path.exists(manager_yaml):
        raise FileExistsError(f"File '{manager_yaml}' not found.")

    with open(manager_yaml, "rb") as file:
        file_content = file.read()
        # Kubernetes expects base64 encoding in the 'data' field
        encoded_content = base64.b64encode(file_content).decode("utf-8")

    secret = client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name=secret_name, namespace=namespace),
        data={os.path.basename(manager_yaml): encoded_content},
    )

    try:
        client.CoreV1Api().create_namespaced_secret(namespace=namespace, body=secret)
        if verbose:
            print(f"Secret '{secret_name}' created in namespace '{namespace}'.")
    except ApiException as e:
        if verbose:
            print(f"Error creating secret: {e}")


def delete_secret(secret_name, namespace=None, verbose=True):
    """Delete a kubernetes secret

    Args:
        secret_name (str): Name of the secret
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace

    config.load_kube_config()
    api_instance = client.CoreV1Api()

    try:
        api_instance.delete_namespaced_secret(name=secret_name, namespace=namespace)
        if verbose:
            print(f"Secret '{secret_name}' deleted from namespace '{namespace}'.")
    except ApiException as e:
        print(f"Error deleting secret: {e}")
