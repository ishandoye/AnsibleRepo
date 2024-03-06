# Default scenario

## Requirements
* [Docker SDK for Python](https://pypi.org/project/docker/)


## Example
```bash
# Create docker images and execute init
molecule create -s default

# Execute playbooks on containers
molecule converge -s default
```
