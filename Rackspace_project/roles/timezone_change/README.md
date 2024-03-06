# timezone\_change

Change system's timezone

## Task Summary
  - Change system's timezone
  - Restart affected services - cron, rsyslog, ntp and conditionally mysql

## Contributors
  - Author(s): Piers Cornwell and GTS Linux Automation Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automation Engineers <GTS-Linux-Automation-Engineers@rackspace.com>

## Supporting Docs
  - https://one.rackspace.com/display/Linux/Configuring+the+Time+Zone+on+Linux

## Assumptions
  - syslog/rsyslog and cron services are configured and running

## Precautions
  - None

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.2
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: All
  - OS: All
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - `data` - tzdata style timezone
    - permitted values: tzdata timezone
    - type: dictionary
    - default: none

  - `timezone` - tzdata style timezone (overrides data)
    - permitted values: tzdata timezone
    - type: str
    - default: data[rs\_server]

  - `restart_mysql` - controls whether the running mysql flavour will be restarted
    - permitted values: True/False
    - type: boolean
    - default: False

  - `mysql_name` - the name of the mysql service
    - permitted values: valid mysql service name
    - type: str
    - default: mysql for debian os family, mysqld for RHEL/CentOS 6, mariadb for RHEL/CentOS 7, mariadb for RHEL/CentOS 8

## Examples

### List here examples of usage
  The playbook allow to change timezone on multiple devices simultaneously thus requires extra-vars variable to be json format.
  Example json\_data file:
  ```json
  {
    "data":{
      "200001": "Europe/London",
      "200002": "Etc/UTC"
    }
  }
  ```

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      timezone_change.yml -e@json_data
  ```
