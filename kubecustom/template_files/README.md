## Including package data

Update the [tool.setuptools.package_data](https://setuptools.pypa.io/en/latest/userguide/datafiles.html#package-data) in `pyproject.toml` and point it at the correct files.

Package data can be accessed at run time with `importlib.resources` or the `importlib_resources` back port.
See https://setuptools.pypa.io/en/latest/userguide/datafiles.html#accessing-data-files-at-runtime
for suggestions.

## Manifest

* `deployment.yaml`: Template yaml file containing information needed to create a kubernetes deployment
* `manager.yaml`: Template yaml file containing information needed to make a kubernetes secret
* `secret.txt`: Non-distributed file, created upon installation for user secret information
