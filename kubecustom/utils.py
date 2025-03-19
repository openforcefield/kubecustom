"""Utilities for unit and case conversions and file manipulation"""

import os
import yaml
import warnings
import argparse

from .secret import MyData

MyDataInstance = MyData()
try:
    _namespace = MyDataInstance.get_data("namespace")
except Exception:
    _namespace = "default"
    warnings.warn(
        "Could not import namespace, functions imported from this module may not operate as expected until "
        "you set manually with 'kubecustom.MyData.add_data()' or interactively with `python -c 'from "
        "kubecustom import MyData; obj=MyData(); obj.add_interactively()'`"
    )


def convert_cpu_use(cpu_usage, issue_warnings=True):
    """Take a string indicating CPU usage and output a float of
    whole number of CPUs used.

    Args:
        cpu_usage (str): CPU usage and unit
        issue_warnings (bool, optional): Choose whether to warn if there is not unit detected. Defaults to True.

    Raises:
        ValueError: Detected unit is not supported

    Returns:
        float: CPU usage in number of whole CPUs
    """
    unit_conversion = {"m": 1 / 1000}

    cpu_usage.replace(" ", "")
    ind = [i for i, x in enumerate(cpu_usage) if not x.isdigit()]
    ind = ind[0] if len(ind) > 0 else len(cpu_usage)
    cpu_float, cpu_unit = float(cpu_usage[:ind]), cpu_usage[ind:]

    if cpu_unit in unit_conversion:
        cpu_float *= unit_conversion[cpu_unit]
    elif len(cpu_unit) == 0:
        if issue_warnings:
            warnings.warn("No CPU unit detected, assuming whole CPU.")
    else:
        raise ValueError(
            f"The CPU unit, {cpu_unit}, is not one of the supported units: {unit_conversion.keys()}. Consider "
            "contributing a conversion factor."
        )

    return cpu_float


def convert_memory_use(mem_usage):
    """Take a string indicating Memory usage and output a float of
    usage in GB. Note that if there is not unit, the float is assumed
    to be in bytes.

    Args:
        mem_usage (str): Memory usage and unit

    Returns:
        float: Memory in GB
    """
    unit_conversion = {
        "Ei": 1073741824,
        "Pi": 1125899.91,
        "Ti": 1099.511627776,
        "Gi": 1.073741824,
        "Mi": 0.001048576,
        "Ki": 1.024e-6,
        "bi": 1.25e-10,
        "E": 1e9,
        "P": 1e6,
        "T": 1000,
        "G": 1,
        "M": 0.001,
        "k": 1e-6,
        "b": 1e-9,
        "": 1e-9,
        "m": 9.3132257461548e-13,
    }
    mem_usage.replace(" ", "")
    ind = [i for i, x in enumerate(mem_usage) if not x.isdigit()]
    ind = ind[0] if len(ind) > 0 else len(mem_usage)
    mem_float, mem_unit = float(mem_usage[:ind]), mem_usage[ind:]

    if mem_unit in unit_conversion:
        mem_float *= unit_conversion[mem_unit]
    else:
        raise ValueError(
            f"The Memory unit, {mem_unit}, is not one of the supported units: {unit_conversion.keys()}. Consider "
            "contributing a conversion factor."
        )

    return mem_float


def file_find_replace(filename, replace_dict):
    """Find keywords and replace with new_words

    Args:
        filename (str): Filename and path to find and replace contents
        replace_dict (dict): A dictionary whose keys are strings to find
        in a file and the values are the strings to replace it with.
    """

    # Read in the file
    with open(filename, "r") as file:
        filedata = file.read()

    # Replace the target string
    for old_word, new_word in replace_dict.items():
        filedata = filedata.replace(str(old_word), str(new_word))

    # Write the file out again
    with open(filename, "w") as file:
        file.write(filedata)


def load_yaml(file_path):
    """Load a deployment YAML file and return the deployment object.

    Args:
        file_path (str): Filename and path to yaml file

    Raises:
        FileExistsError: Will raise error if the filename provided does not exist

    Returns:
        dict: Dictionary created from yaml file
    """
    if not os.path.exists(file_path):
        raise FileExistsError(f"File '{file_path}' not found.")

    with open(file_path, "r") as f:
        dictionary = yaml.safe_load(f)
    return dictionary


def load_template_paths():
    """Return the paths to template deployment.yaml files and manager.yaml files

    Returns:
        deployment_yaml (str): Path to template deployment.yaml file
        manager_yaml (str): Path to template manager.yaml file
    """
    module_path = os.path.dirname(__file__)
    deployment_path = os.path.join(module_path, "template_files", "deployment.yaml")
    manager_path = os.path.join(module_path, "template_files", "manager.yaml")
    return deployment_path, manager_path


def to_camel_case(snake_str):
    """Convert snake_case to camelCase

    Args:
        snake_str (str): String in snake case

    Returns:
        str: String in camel case
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def convert_keys_to_camel_case(obj):
    """Recursively convert dictionary keys to camelCase

    Args:
        obj (list/dict): A list where the contents or a dictionary where the keys need to be converted from snake case"
        " to camel case

    Returns:
        list/dict: A list or dictionary with appropriate conversions from snake case to camel case
    """
    if isinstance(obj, list):
        return [convert_keys_to_camel_case(i) for i in obj]
    elif isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_key = to_camel_case(k)
            new_dict[new_key] = convert_keys_to_camel_case(v)
        return new_dict
    else:
        return obj


def get_parser():
    """Process line arguments"""

    # Define parser functions and arguments
    parser = argparse.ArgumentParser(
        description=(
            "KubeCustom: Kubernetes assessment  and combined control functions to handle multiple deployments."
            " Running the module as a command line function applies the `kubecustom.utilization_per_deployment()`"
            " function. The following arguments are associated with that function.\n"
            "\nReturn the utilization of resources per deployment every `timelag` seconds."
        )
    )
    parser.add_argument(
        "-k",
        "--keep_key",
        dest="keep_key",
        default="",
        help=(
            "A string in the deployment name to signify that it should be kept, such as a deployment name or your "
            "kubecustom.MyData.get_data('user') string. Defaults to ''."
        ),
    )
    parser.add_argument(
        "-n",
        "--namespace",
        dest="namespace",
        default=_namespace,
        help=(
            "Kubernetes descriptor to indicate a set of team resources. Defaults to "
            "`kubecustom.MyData.get_data('namespace')`"
        ),
    )
    parser.add_argument(
        "-t",
        "--timelag",
        dest="timelag",
        default=20,
        help=("Time lag in seconds before updating. Defaults to 60"),
    )
    parser.add_argument(
        "-s",
        "--silence",
        dest="silence",
        action="store_true",
        help=("Whether to silence warnings. Defaults to False"),
    )

    return parser
