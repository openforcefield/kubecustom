"""Create and manage Persistent Volume Claims"""

import time
import warnings

from kubernetes import client, config

from .utils import MyData, convert_memory_use

try:
    MyDataInstance = MyData()
except Exception:
    warnings.warn(
        "Could not import namespace, functions imported from this module may not operate as expected until "
        "you set manually with 'kubecustom.MyData.add_data()' or interactively with `python -c 'from "
        "kubecustom import MyData; obj=MyData(); obj.add_interactively()'`"
    )


def create_volume_mount(name, mount_path, read_only=False):
    """Create a volume mount for a container

    Args:
        name (str): This must match the Name of a Volume.
        mount_path (str): Path within the container at which the volume should be mounted. Must not contain ':'.
        read_only (bool, optional): Mounted read-only if true, read-write otherwise (false or unspecified). Defaults to False.

    Returns:
        V1VolumeMount: Volume mount object
    """

    config.load_kube_config()
    return client.V1VolumeMount(
        name=name,
        mount_path=mount_path,
        read_only=read_only,
    )


def delete_pvc(pvc_name, namespace=None):
    """Delete a persistent volume claim

    Args:
        pvc_name (str): Name of persistent volume claim
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
    """

    config.load_kube_config()
    try:
        client.CoreV1Api().delete_namespaced_persistent_volume_claim(
            name=pvc_name,
            namespace=namespace,
        )
    except Exception as e:
        raise RuntimeError(
            f"Could not delete PV {pvc_name}. Another pod may be looking at storage. Error : {e}"
        )


def create_pvc(
    pvc_name,
    storage_space=2,
    timeout=1000,
    timelag=5,
    namespace=None,
):
    """Create persistent volume claim for kubernetes

    Args:
        pvc_name (str): Name of persistent volume claim
        storage_space (int, optional): Required storage space in TB. Defaults to 2.
        timeout (int, optional): Duration in seconds to wait for PVC bound state, otherwise error. Defaults to 1000.
        timelag (int, optional): Amount of time to wait in seconds before checking that the part connection is
        established, Defaults to 5.
        namespace (str, optional): Kubernetes descriptor to indicate a set of team resources. Defaults to
        :func:`kubecustom.secret.MyData.get_namespace`.
    """

    namespace = MyDataInstance.get_namespace() if namespace is None else namespace
    storage_class_name = MyDataInstance.get_storage_class_name()

    config.load_kube_config()
    pvc_spec = client.V1PersistentVolumeClaimSpec(
        access_modes=["ReadWriteMany"],
        storage_class_name=storage_class_name,
        resources=client.V1ResourceRequirements(
            requests={
                "storage": f'{convert_memory_use(f"{storage_space}TB")}GB',
            }
        ),
    )

    metadata = client.V1ObjectMeta(name=pvc_name)
    pvc = client.V1PersistentVolumeClaim(
        api_version="v1",
        kind="PersistentVolumeClaim",
        metadata=metadata,
        spec=pvc_spec,
    )

    api_response = client.CoreV1Api().create_namespaced_persistent_volume_claim(
        namespace=namespace, body=pvc
    )

    print(f"Created PVC {pvc.metadata.name}. State={api_response.status.phase}")

    # wait to make sure it binds
    end_time = time.time() + timeout
    while time.time() < end_time:
        pvc = client.CoreV1Api().read_namespaced_persistent_volume_claim(
            name=pvc_name, namespace=namespace
        )
        if pvc.status.phase == "Bound":
            print(f"PVC '{pvc_name}' is Bound.")
            return pvc_name
        print(
            f"Waiting for PVC '{pvc_name}' to become Bound. Current phase: {pvc.status.phase}"
        )
        time.sleep(timelag)
