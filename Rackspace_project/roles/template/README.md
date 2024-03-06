# (Role name, example: role_name)

High level overview of what the playbook does and attempts to achieve.

## Task Summary
  - Outline of relevant/impactful tasks and what their purpose is, example:
    - Checks apache config test
    - Updates config file
    - Checks apache config test
    - Restarts apache web server

## Contributors
  - Author: Full Name <name.last_name@rackspace.com[.uk]>[, Full Name <name.last_name@rackspace.com[.uk]>]
  - Maintainer: Full Name[, Full Name]

## Supporting Docs
  - If your playbook automates/supports a written process - insert a link to it here.

## Assumptions
  - Any assumptions your playbook is making - such as packages already being installed, target operating system or environment.

## Precautions
 - Any config tests done,
 - Any backup files taken and their location
 - Other checks.
 - This aids in manual interventions, should the execution of this playbook fail.

## Rollback
  - Does the playbook have the facility to roll itself back?
  - Include a description of any potentially destructive actions here, such as; deleting files, overwriting files

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - Requires **root**

## Compatibility
  - Rackspace platform: Cloud / Dedicated / All
  - OS: RHEL / CentOS / Ubuntu / Debian / All (include versions where needed).
  - Idempotent: Yes/No (can the playbook be executed repeatedly without breaking anything on the target system?)
  - Check Mode: Yes/No (Does this support Ansible Check mode?)

## Variables
  - Any external variables/inputs the playbook takes. Internal, transient and state-keeping variables does not need to be declared here:
  - `variable_name` - The purpose of this variable
    - permitted values: (Example: True/False/Yes/No)
    - type: (Example: boolean)
    - default: (Example: True)
    - required: (Example: Yes/No)

## Examples

### Describe and list examples of usage here

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      playbook_name.yml
```
