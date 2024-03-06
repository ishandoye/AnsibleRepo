# newrelic_install
Install newrelic package and configure licence key.


## Task Summary
  - Newrelic repository is added to servers package manager (apt or yum) thus newrelic future updates can be done automatically.
  - Verifies that newrelic is installed on server(s)
  - Install newlic packages (newrelic-infra) if it is not already installed
  - Configure newrelic licence key at /etc/newrelic-infra.yml

## Contributors
  - Author: GTS Linux Automaton Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automaton Engineers

## Supporting Docs
  - https://one.rackspace.com/display/Linux/New+Relic

## Assumptions
  - None

## Precautions
  - Default /etc/newrelic-infra.yml will be replaced with given license key.
  - Newrelic repositories will be added.

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

## Examples


  ```bash
  ht -A --playbook --ansible-args "newrelic_install.yml -e'license=1ebd3467afec78da28d345cbe15a9ef135cbae68'" 200001,200002
```

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      newrelic_install.yml -e license=1ebd3467afec78da28d345cbe15a9ef135cbae68
```
