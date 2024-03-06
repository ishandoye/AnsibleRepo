# newrelic_update_php
Enable newrelic PHP APM


## Task Summary
  - Install newrelic PHP packages
  - Identify newrelic.ini file(s)
  - Update newrelic licence key on the identified newrelic.ini files
  - Update newrelic appname (if provided, otherwise default name is used) on the identified newrelic.ini files
  - Verifies apache webservice is running, if so check for config errors and restart apache if no errors.
  - Verifies php-fpm is running, if so check for config errors and restart php-fpm if no errors.

## Contributors
  - Author: GTS Linux Automaton Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automaton Engineers

## Supporting Docs
  - https://one.rackspace.com/display/Linux/New+Relic

## Assumptions
  - Newrelic-infra package is already installed

## Precautions
  - Apache and php-fpm services will be restarted once licence key is added to php config files.

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 4.0.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated and Cloud
  - OS: RHEL 6/7, CentOS 6/7, Ubuntu 14.04/16.04
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - license - To configure newrelic service
     - permitted values: 40 characters
     - type: string
     - default: None

  - AppName - name of the php app. Optional parameter.
     - permitted values: any string
     - type: string
     - default: empty string

## Examples

  ```bash
  ht -A --playbook --ansible-args "newrelic_update_php.yml -e'license=1ebd3467afec78da28d345cbe15a9ef135cbae68'" 200001,200002
```

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      newrelic_update_php.yml -e license=1ebd3467afec78da28d345cbe15a9ef135cbae68
```
