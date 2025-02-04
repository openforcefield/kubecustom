"""Kubernetes assessment functions to handle multiple deployments"""

# Add imports here
from .kubecustom import create_secret_deployment as create_secret_deployment
from .kubecustom import delete_secret_deployment as delete_secret_deployment
from .deployment import utilization_per_deployment as utilization_per_deployment
from .secret import MyData as MyData

from ._version import __version__ as __version__
