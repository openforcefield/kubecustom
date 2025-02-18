"""Create and delete secrets"""

import os
import base64
import warnings
import yaml

from InquirerPy import prompt
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

from pkg_resources import resource_filename

_init_filename = resource_filename("kubecustom", "template_files/config.yaml")

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
    _attributes = {
        "qca": {  # config type
            "username": "(str): Kubernetes username for secret. Defaults to None.",
            "password": "(str): Kubernetes password for secret. Defaults to None.",
            "user": (
                "(str): YOUR personal identifier for deployments and secrets, e.g., "
                "'my-organization-my-initials'. Defaults to None."
            ),
            "namespace": "(str): Your team namespace. Defaults to None.",
            "container_name": "(str): Name for type of deployed containers. Defaults to None.",
            "container_image": "(str): Link to container image, e.g., ghcr.io/...",
            "cluster_name": "(str): Name of kubernetes cluster",
        },
    }

    def __init__(self, config=None):
        """Initialize MyData object, with or without an existing configuration

        Args:
            config (str, optional): Name of configuration to choose. Defaults to None.

        Raises:
            ValueError: If configuration name is not found.
        """

        config_names = list(self._get_configurations().keys())
        if len(config_names) == 0:
            self._no_config(type="warning")

        if config is None:
            if len(config_names) > 0:
                print(
                    f"Using configuration, {config_names[0]}, of the options: {config_names}. Select an alternative with "
                    "`MyData.set_configuration`"
                )
                self.set_configuration(config_names[0])
            else:
                self.configuration = None
        else:
            self.set_configuration(config)

    def _get_configurations(self):
        """Get the configurations from the configuration file

        Returns:
            dict: Dictionary of configurations settings
        """

        with open(_init_filename, "r") as f:
            _contents_dict = yaml.safe_load(f)
        return _contents_dict

    def set_configuration(self, configuration):
        """Set the configuration from those stored in the configuration yaml

        Args:
            configuration (str): Configuration name representing a a set of settings

        Raises:
            ValueError: Configuration name cannot be found
            ValueError: Configuration does not have required set of parameters
        """

        configuration_dict = self._get_configurations()
        if configuration not in configuration_dict:
            raise ValueError(
                f"Configuration, {configuration}, cannot be found, choose one of the following:"
                f" {configuration_dict.keys()}"
            )

        if "configuration_type" not in configuration_dict[configuration]:
            raise ValueError(
                f"The configuration type is not defined for, {configuration}, set using "
                "`MyData.add_data`."
            )
        elif (
            configuration_dict[configuration]["configuration_type"]
            not in self._attributes
        ):
            raise ValueError(
                f"The configuration type, {configuration_dict[configuration]['configuration_type']}, is"
                f"not a supported configuration type. Must be: {self._attributes.keys()}"
            )

        if not all(
            x in configuration_dict[configuration]
            for x in self._attributes[
                configuration_dict[configuration]["configuration_type"]
            ].keys()
        ):
            raise ValueError(
                f"Configuration, {configuration}, must have the following values set {self._attributes.keys()}."
            )

        self.configuration = configuration
        for key, value in configuration_dict[configuration]:
            setattr(self, f"_{key}", value)

    def get_data(self, value):
        """Get the value in a configuration

        Args:
            value (str): Key in the configuration that must be set by the configuration type.

        Raises:
            ValueError: Configuration value was not found.

        Returns:
            *: Value from a configuration yaml file.
        """
        if self.configuration is None:
            self._no_config()

        configuration_dict = self._get_configurations()
        if value not in configuration_dict[self.configuration]:
            raise ValueError(
                f"The value for, {value}, is not defined for the configuration, {self.configuration}."
                f"Must be one of: {configuration_dict[self.configuration].keys()}"
            )

        return configuration_dict[self.configuration][value]

    def _no_config(self, type="error"):
        if type == "error":
            raise ValueError(
                "Configuration information cannot be found. Please set manually with `kubecustom.MyData.add_data()`"
                " or interactively with `python -c 'from kubecustom import MyData; obj=MyData(); "
                "obj.add_interactively()'`"
            )
        elif type == "warning":
            warnings.warn(
                "Configuration information cannot be found. Please set manually with `kubecustom.MyData.add_data()`"
                " or interactively with `python -c 'from kubecustom import MyData; obj=MyData(); "
                "obj.add_interactively()'`"
            )
        else:
            raise ValueError("Type = {type} is not valid.")

    def add_data(self, new_attributes=False, **kwargs):
        """Set configuration information manually, if it has already been initialized.

        Args:
            \*\*kwargs: Kwargs to add to the configuration, restricted to the type defined.

        """

        if self.configuration is None:
            self._no_config()

        configuration_dict = self._get_configurations()[self.configuration]
        configuration_type = configuration_dict["configuration_type"]
        for key, value in kwargs.items():
            if key in self._attributes[configuration_type]:
                setattr(self, f"_{key}", value)
            else:
                raise ValueError(
                    f"The configuration value, {key}, is not supported for the configuration type, "
                    f" {configuration_type}. Must be one of the following: {configuration_dict.keys()}"
                )

        missing_attr = []
        for key in self._attributes[configuration_type].keys():
            if not hasattr(self, f"_{key}"):
                missing_attr.append(key)

        if len(missing_attr) > 0:
            raise ValueError(
                f"Missing the attributes: {missing_attr}, for configuration, {self.configuration},"
                f" of type, {configuration_type}."
            )

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
        configuration_dict = self._get_configurations(self)
        configuration_type = configuration_dict[self.configuration][
            "configuration_type"
        ]
        for key in self._attributes[configuration_type].keys():
            configuration_dict[self.configuration][key] = getattr(self, key)
        with open(_init_filename, "w") as f:
            yaml.dump(configuration_dict, f)


# ___________________________________________________________________________________________________


MyDataInstance = MyData()


def create_secret(manager_yaml, secret_name, namespace=None, verbose=True):
    """Create a secret from a manager.yaml

    Args:
        manager_yaml (str): Filename and path to a manager.yaml file
        secret_name (str): Name of secret
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_data("namespace")`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.

    Raises:
        FileExistsError: Check that manager.yaml file exists
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

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
        :func:`kubecustom.secret.MyData.get_data("namespace")`.
        verbose (bool, optional): If False the output will not print to screen. Defaults to True.
    """

    namespace = MyDataInstance.get_data("namespace") if namespace is None else namespace

    config.load_kube_config()
    api_instance = client.CoreV1Api()

    try:
        api_instance.delete_namespaced_secret(name=secret_name, namespace=namespace)
        if verbose:
            print(f"Secret '{secret_name}' deleted from namespace '{namespace}'.")
    except ApiException as e:
        print(f"Error deleting secret: {e}")
