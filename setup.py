import os
from setuptools import setup

filename = "kubecustom/template_files/config.yaml"
if not os.path.isfile(filename):
    with open(filename, "w") as f:
        f.write("")

if __name__ == "__main__":
    setup(
        name="kubecustom",
    )
