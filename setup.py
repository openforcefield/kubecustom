import os
from setuptools import setup

filename = "kubecustom/template_files/secret.txt"
if not os.path.isfile(filename):
    with open(filename, "w") as f:
        f.write("username: None\n")
        f.write("password: None\n")
        f.write("user: None\n")
        f.write("namespace: None\n")
        f.write("container_name: None\n")
        f.write("container_image: None\n")
        f.write("cluster_name: None\n")

if __name__ == "__main__":
    setup(
        name="kubecustom",
    )
