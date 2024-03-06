# (Role name, example: role_name)

Configures MySQL master/slave replication on 2+ dedicated servers 

## Task Summary
  - Checks server status
  - Configures master
  - Configures slave(s)
  - Copies data
  - Starts slave

## Contributors
  - Author: Mike Frost
  - Maintainer: GTS Linux Automation Engineers

## Supporting Docs
  - https://one.rackspace.com/display/Linux/MySQL%3A++Setup+-+MySQL+Master+Slave+Replication

## Assumptions
  - MySQL is already installed and running.
  - OS is RHEL6+ (may work on ubuntu, but untested)
  - There is no replication already set up
  - Master and slave(s) are both newly configured

## Precautions
  - None

## Rollback
  - No

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - Requires **root**

## Compatibility
  - Rackspace platform: Cloud / Dedicated
  - OS: RHEL / CentOS / Ubuntu
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - `master` - Replication Master server ID
    - permitted values: Any valid server number
    - type: string
    - default: -
    - required: Yes

## Examples

  ```bash
ht -A --playbook --ansibleargs='mysql_replication.yml -b --extra-vars="master=111111"' 111111,222222
```
