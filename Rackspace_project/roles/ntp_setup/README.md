# ntp_setup

Installs default time service package, configure Rackspace time servers (optional) and synchronize system time.

## Task Summary
  - Obtain and validate Rackspace NTP FQDN and IP
  - Remove conflicting non-default time service packages (if any).
  - Install default time service packages.
  - Stop the time service.
  - Configure time services accordingly, using Rackspace Time servers (default action, optional).
    - NTP - Update config files
    - Chrony - Drop-in config files
    - Timesyncd - Update config files
  - Synchronize the server's time.
  - Start the time service and enable it to start on boot.

## Contributors
  - Author: Sean Dennis
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Supporting Docs
  - https://one.rackspace.com/pages/viewpage.action?title=Linux+ADC&spaceKey=GET#LinuxADC-ConfigureTime-LADC

## Assumptions
  - Rackspace time servers will be used. Override default behaviour by setting "rs_ntp=no".

## Precautions
  - For certain distros the time config will be overridden, unless this behaviour is changed by the variable below.
  - The server's time will be updated (synchronized) if it's off.
  - The 'ntp' package will be removed and replaced with timesyncd (Ubuntu 16 only).

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.7.x
  - **Hammertime**: >= 4.6.x
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL 6/7/8, CentOS 6/7/8, Ubuntu 14.04/16.04/18.04
  - Idempotent: Yes
  - Check Mode: No
  - ACE support: Yes

## Variables
  - `rs_ntp` - Determines if Rackspace default configs and time servers are used.
    - permitted values: True/False, yes/no
    - type: boolean
    - default: True

## Examples

### Install (with Rackspace time servers - default)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      ntp_setup.yml
```

### Install (without Rackspace time servers)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      ntp_setup.yml -e "rs_ntp=no"
```
