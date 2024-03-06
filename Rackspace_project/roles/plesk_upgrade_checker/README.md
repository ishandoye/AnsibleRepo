# Plesk Upgrade Checker

Runs through Plesk upgrade checks

## Task Summary

## Contributors
  - Author: Dan Hand <daniel.hand@rackspace.co.uk>
  - Maintainer: Dan Hand

## Supporting Docs
  - https://one.rackspace.com/display/Linux/Linux+Plesk+Upgrade+-+Policy

## Assumptions
  - Server does have plesk installed and is running a supported OS

## Precautions
 - Assumptions have been met

## Rollback
  - No

## Requirements
  - **Ansible**: >= 2.5.0.0
  - **Hammertime**: >= 3.4.0
  - **Librack**
  - Requires **root**
   
## Compatibility
  - Rackspace platform: Dedicated devices ONLY
  - OS: RHEL / CentOS
  - Idempotent: Yes

## Variables
  - upgrade_to - Specify the version you'd like to upgrade to here. See example command below.

## Examples

   ```bash
   TARGETS=431848,431849 ansible-playbook -i $(which ht) plesk_upgrade_checker.yml -e upgrade_to=17.8.11
```
