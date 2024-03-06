# SSM Agent Installer
## Task Summary
Downloads and installs the SSM agent on devices by default. 
An `install` tag can be provided to be explicit, or `uninstall` to 
uninstall the `amazon-ssm-agent` package

## Contributors
  - Author: Dan Hand <dan.hand@rackspace.com>
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Rollback
  - No

## Requirements
  - **Ansible**: >= 2.10.0
  - **Hammertime**: >= 6.5.0
  - Librack2
  - Requires **root**

## Compatibility
  - Rackspace platform: All
  - OS: RHEL >= 7 / CentOS >= 7 / Ubuntu >= 20.04
  - Idempotent: No
  - Check Mode: No

## Examples
### Install SSM Agent
```bash
TARGETS=431848 ansible-playbook -i $(which ht) ssm_agent_install.yml -t install -e rackertoken=$(ht credentials)
```

### Uninstall SSM Agent
```bash
TARGETS=431848 ansible-playbook -i $(which ht) ssm_agent_install.yml -t uninstall -e rackertoken=$(ht credentials)
```
