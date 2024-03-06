# rax_server_management_tools

Provides ad-hoc plays related to server management of Dell/HP servers.

## Task Summary

This role is intended to execute tasks in an ad-hoc manner. By default this role will not do anything without one of the following variables being set to true:

  - `reset_obm_root_pw` - Reset the root OBM user password. Requires obm_pass to be set. Requires vendor tools on server to already be installed.

  - `configure_obm_networking` - Configure networking for the OBM card. Requires `obm_ip, obm_nm and obm_gw`. If any of these values are not provided, a task will be executed to query core for all of them. Requires vendor tools on server to already be installed.

  - `configure_repo` - Configure Dell/HP yum/apt repos. Includes installing required gpg keys.

  - `install_vendor_tools` - Will execute the `configure_repo` set of tasks and also install the list of packages defined by `hp_install_pkgs` and `dell_install_pkgs`. Additionally the list of services defined by hp_services_to_enable and dell_services_to_enable will be started and enabled.

## Contributors
  - Author: Ed Velez
  - Maintainer(s): Ed Velez

## Assumptions
  - Server management tools are already installed when running `reset_obm_root_pw` or `configure_obm_networking`.
  - Hammertime is installed when querying core for obm networking info.

## Precautions
  - Existing vendor repo files will be overwritten if they have deviated from the template.
  - Running the `configure_networking` set of tasks will always cause DRAC cards to be reset even if the configuration has not changed. Drac cards will take several minutes to come back online.

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access
  - This playbook requires **gather_facts** to be run.

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL 6/7, CentOS 6/7, Ubuntu 14.04/16.04
  - Idempotent: Yes - `configure_repo` and `install_vendor_tools` only.
  - Check Mode: No

## Variables

  - `obm_user` - Username for OBM user to reset pw for. (HP Only)
    - type: string
    - default: root

  - `obm_pass` - Password to set for the root obm user
    - type: string

  - `obm_ip, obm_nm, obm_gw` - Networking information required for configuring drac/ilo
    - type: string
    - default: If **any** of these are not defined a task will be run to query all of them from core.

  - `hp_install_pkgs, c` - List of packages to install for HP and Dell servers respectively
    - type: list
    - default:
        - dell_install_pkgs:
            - srvadmin-all
        - hp_install_pkgs
            - srvadmin-all
            - hponcfg
            - ssacli
            - hp-health
            - hp-snmp-agents

  - `hp_services_to_enable, dell_services_to_enable` - List of services to start and enable for Dell/HP servers respectively.
    - type: list
    - default:
        - hp_services_to_enable:
            - hp-health
            - hp-snmp-agents
        - dell_services_to_enable:
            - dataeng
            - dsm_om_connsvc
## Examples

### Reset the root obm user password to whats in core:
```
TARGETS=777821 ansible-playbook server_management.yml -e "reset_obm_root_pw=true obm_pass={{ rs_obm_pass }}"
```
### Configure OBM card with the networking information provided in core:
```
TARGETS=777821 ansible-playbook server_management.yml -e "configure_obm_networking=true"
```
### Configure Dell/HP repo:
```
TARGETS=777821 ansible-playbook server_management.yml -e "configure_repo=true"
```
### Configure repo and install HP/Dell vendor tools:
```
TARGETS=777821 ansible-playbook server_management.yml -e "install_vendor_tools=true"
```