# alertlogic_logmanager_install

Install AlertLogic Log Manager agent

## Task Summary
  - Validate if agent is already installed and configured
  - Check connectivity to alert logic host
  - Push installer to server
  - Install the package
  - Configure and validate agent
  - Configure syslogs

## Contributors
  - Author:          Paolo Gigante <paolo.gigante@rackspace.co.uk>
  - Maintainer(s):   Paolo Gigante, Tony Garcia

## Supporting Docs
  - [Installing Alert Logic Log Manager Agent and Configuring Syslog](https://one.rackspace.com/display/ESS/Installing+Alert+Logic+Log+Manager+Agent+and+Configuring+Syslog)

## Assumptions
  - Supports rsyslog and syslog-ng

## Precautions
  - None at this time

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL/CentOS 6/7, OL 7, Ubuntu 14/16/18
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - `registration_key` - AlertLogic registration key
    - permitted values: A valid key
    - type: string
    - default: none
    - required: Yes

  - `syslog_daemon` - The syslog daemon to configure
    - permitted values: rsyslog or syslog-ng
    - type: string
    - default: rsyslog
    - required: No

## Examples

### Install AlertLogic Log Manager agent

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      alertlogic_logmanager_install.yml -e registration_key=123abc.. -e syslog_daemon=syslog-ng
```
