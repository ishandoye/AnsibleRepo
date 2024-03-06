# nimbus

(Re|Un)Installs Nimbus.

## Task Summary

- On install:
  - Either pulls or pushes installer file
  - Installs and start nimbus
  - Removes the installer
  - Verifies that nimbus is installed

- On remove:
  - Stops nimbus daemon
  - Archives the current install
  - Removes the install
  - Verifies that nimbus is removed

## Contributors
  - Author: Richard Harwood
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Supporting Docs
  - https://one.rackspace.com/display/SegSup/Linux+Installation+-+Nimbus

## Precautions
  - On remove it always maintains a backup copy of the install under ~rack/nimbus-<TIMESTAMP>.tar.gz

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.5.0
  - **Hammertime**: >= 3.4.0
  - **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL 6/7, CentOS 6/7, Oracle 7, Ubuntu 14.04/16.04/18.04
  - Idempotent: Yes
  - Check Mode: No
  - ACE support: Yes

## Variables
  - `remove` - Removes nimbus if defined
    - default: undefined

  - `push` - Downloads the installer locally and push it to the server.
    - default: undefined

  - `force` - Forces a remove of the software then installs.
    - default: undefined

## Examples

### Install (default)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      nimbus.yml
```

### Install (pushing the installer)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      -e 'push=yes' \
      nimbus.yml
```

### Reinstall

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      -e 'force=yes' \
      nimbus.yml
```

### Uninstall

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      -e 'remove=yes' \
      nimbus.yml

```
