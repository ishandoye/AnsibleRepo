# vmtools_install

Install VM Tools

## Task Summary
  - Install the open-vm-tools package
  - Start and enable the vmtools service

## Contributors
  - Author: Sean Dennis
  - Maintainer: Sean Dennis, Tony Garcia

## Supporting Docs
  - None

## Assumptions
  - For CentOS/RHEL 6 EPEL repo needs to be enabled

## Precautions
  - None 

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
  - Check Mode: Yes
  - ACE support: Yes

## Variables 
  - None

## Examples
### Install (check-mode)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      vmtools_install.yml --check
```

### Install

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      vmtools_install.yml
```
