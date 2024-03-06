# Using molecule
Molecule is a test framework for ansible inspired by Chef's [test kitchen](https://kitchen.ci/).
Information on molecule best practices can be found in [SupportTools/development-guidelines](https://pages.github.rackspace.com/SupportTools/development-guidelines/ansible.html#testing)

## Installation
The recommended installation method is via pip inside of a virtual environment.
Its required dependencies may lag behind other Python tools you may already have installed.
```bash
python3 -m venv molecule-venv
source molecule-venv/bin/activate
pip install molecule ansible netaddr
```

Supporting libraries for any drivers should also be installed.
```bash
pip install docker openstacksdk rackspaceauth
```

## Caveats
Most, if not all, molecule scenarios will use the Docker driver for tests.
It's possible to force a scenario that's set up for Docker to use Red Hat's [podman](https://podman.io/) instead.
molecule's `create` and `test` both allow for overriding at runtime which driver to use for container setup.
```bash
molecule create --driver-name podman
molecule test --driver-name podman
```
Additionally, since Docker is the expected driver, the defined platforms should be set with elevated privileges if they will be running systemd.
This can be done by adding the `SYS_ADMIN` capability or by setting the container to be `privileged`.
For more information about elevated capabilities, please see the [Docker documentation](https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities).

Some roles may expect certain variables to be set by hammertime.
The role [`dummy_raxfacts`](../roles/dummy_raxfacts) can be called in `converge.yml` to set up various mock facts from core.

Some roles may expect a certain set of packages to be installed.
The role [`molecule_container_prep`](../roles/molecule_container_prep) was made to add any packages or configuration changes that may have been missing from a container base image.
The Dockerfile template or molecule instance configuration may also be modified for similar effects.

### molecule v3
molecule v3 made [certain backwards-incompatible changes to](https://github.com/ansible-community/molecule/issues/2560#issue-566151191) the molecule configuration.
Some changes include:
- `lint:` section has been removed and is now defined as shell script within a multiline string. Example:
```yaml
lint: |
set -e
yamllint .
ansible-lint .
```
- scenario name is determined exclusively by directory name not by a possible `scenario.name` option.
- `playbook.yml` is now `converge.yml`.
- ansible became the default verifier in place of testinfra.

## Sample commands
```bash
# Execute role on test systems
molecule converge

# Log in to test system
molecule login -h molecule-d9

# Run verifier on test systems
molecule verify

# Run all scenario tests with debugging and skip destroy phase
molecule test --debug --destroy never --all

# Delete all test systems
molecule destroy -f

# Clear molecule's temp state files
# This can be useful if you messed with docker image state outside of molecule
molecule reset
```
