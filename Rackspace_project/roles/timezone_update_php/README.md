# timezone_update_php

Change timezone on PHP config files

## Task Summary
  - Update timezone value on php.ini files
  - Verify if apache service running and restart it if necessary
  - Verify if php-fpm service running and restart it if necessary

## Contributors
  - Author: GTS Linux Automation Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automation Engineers 

## Supporting Docs
  - https://one.rackspace.com/display/Linux/Configuring+the+Time+Zone+on+Linux

## Assumptions
  - N/A

## Precautions
  - If Apache and php-fpm services exist, config test is performed and services are restarted based on config results.

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.2.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated and Cloud
  - OS: RHEL 6/7, CentOS 6/7, Ubuntu 14.04/16.04
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - `timezone` - tzdata style timezone
    - permitted values: tzdata timezone
    - type: dictionary
    - default: none
    - required: Yes

## Examples

### Change the timezone on multiple devices
Note: The playbook allows you to change php configuration timezone on multiple devices simultaneously and thus requires the extra-vars variable to be json format.  Example:
  ```bash
  cat json_data
  {
      "data":{
          "200001": "Europe/London",
          "200002": "Etc/UTC"
          }
  }
```


  ```bash
  ht -A --playbook --ansibleargs "timezone_update_php.yml -e@json_data" 200001 200002
```
Note: The content of json_data will be something similar to the above example data.

