# nimbus_fix_clonedvm_robot_cfg

Fixes Nimbus robot and primary_ip when vms are cloned.

## Task Summary
 - gathers facts as needed
 - update robot.cfg robotname and robotip_alias

## Contributors
  - Author: Joe Esposito
  - Maintainer(s): Joe Esposito

## Supporting Docs
  - https://jira.rax.io/browse/DCXADC-651 is the bug this is working around
  
## Assumptions
  - Nimbus is installed.
  - VM has a primary IP.

## Precautions
  - This is safe to run against a vm that is correct.
  
## Rollback
  - Manual

## Requirements
  - **Hammertime**: working version.
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: All
  - Idempotent: Yes
  - Check Mode: Yes
  
 
