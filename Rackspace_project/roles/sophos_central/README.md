# Sophos Central

Installs/uninstalls Sophos Central

**NOTE** This is the same playbook used by the Sophos Central module in Stepladder
(https://stepladder.rax.io/sophos_central)  
Recommend you use that module to handle Sophos Central instead of running this
playbook manually

## Tasks summary

For each device:
  - validates the OS is supported
  - validates the requested action is valid (one of `install`, `remove`)
  - check if Sophos Central is installed
  - stop immediately if Sophos Central is already in the requested state, i.e.
    - not installed when `remove` is requested
    - already installed when `install` is requested (unless `force_reinstall`
      is true)
  - retrieve installer links from Stepladder (unless `linux_installer` is set)
  - download the installer to the device
  - fail at this point if the installer is required and unavailable, before any
    modifications are made to the device
  - uninstall Sophos Central (if either `remove` or `force_reinstall` are
    requested)
    - report ID of removed agent(s) to assist finding it/them in the Sophos
      Central console
  - install Sophos Central (if `install` is requested)
    - the installer will be run with the `--group='<group>'` flag if `group`
      is set

## Contributors
  - Author: Paul Whitaker
  - Maintainers: GTS Linux Automation Engineers

## Requirements:
  - Ansible version >= 2.12
  - Hammertime >= 6.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated (CORE)
  - OS: CentOS 7, RHEL 7/8/9, AlmaLinux/Rocky Linux 8/9, Ubuntu 18.04/20.04/22.04
  - Idempotent: Yes
  - Check Mode - No

## Variables

  - `role_action`: One of `install`, `remove`
    - default: `install`
  - `force_reinstall`: Force a reinstall of Sophos Central (uninstalls then
    reinstalls Sopos Central) if set to a value that evaluates as `true`
    - default: `false`
  - `group`: Name of Sophos policy group to add device to on install
    - default: `None`
  - `linux_installer`: URL for Linux installer script (when all devices use the
    same script)
    - default: `None` (playbook will get script URLs from Stepladder)
  - `rackertoken`: Racker's identity token, required if you want to lookup the
    installer script(s) in Stepladder
    - default: read from `RACKERTOKEN` environment variable (see below)

## Environment Variables

  - `RACKERTOKEN`: Racker's identity token, required if you want to lookup the
    installer script(s) in Stepladder

## Examples

### Install Sophos Central, lookup installer URLs

```bash
$ RACKERTOKEN=$(ht credentials --identity) TARGETS=200001,200002 \
    ansible-playbook -i $(which ht) sophos_central.yml
```

### Install Sophos Central, installer URL provided

```bash
$ TARGETS=200001,200002 ansible-playbook -i $(which ht) sophos_central.yml \
    -e 'linux_installer=https://host/path/to/installer/SophosSetup.sh'
```

### Reinstall Sophos Central with a policy group

```bash
$ RACKERTOKEN=$(ht credentials --identity) TARGETS=200001,200002 \
    ansible-playbook -i $(which ht) sophos_central.yml \
    -e force_reinstall=1 -e group='My Policy Group'
```

### Uninstall Sophos Central

```bash
$ TARGETS=200001,200002 ansible-playbook -i $(which ht) sophos_central.yml \
  -e role_action="uninstall"
```
