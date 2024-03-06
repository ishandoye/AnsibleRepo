# group_add
Add new local group(s) optionally with sudo rights

## Task Summary
  - Add group(s), optionally updates sudoers configuration to add entry for selected group(s)
  - Update and validate /etc/sudoers or /etc/sudoers.d/<newgroup> depending on chosen options

## Contributors
  - Author: Jean Michaud
  - Maintainer(s): Jean Michaud

## Supporting Docs
N/A

## Assumptions
  - This play should only be used to **create new** group(s). Running this against groups existing before the first run of the playbook is **not** recommended, as this playbook will **not** look for existing groups/ sudo-related configuration.
  - Any existing entry for the group in sudoers _might_ be lost.

## Precautions
  - sudoers will be validated after editing with visudo -c


## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: All
  - OS: RHEL 6/7, CentOS 6/7, Ubuntu 14.04/16.04
  - Idempotent: Yes
  - Check Mode: No

## Variables
This role accepts a list of groups containing one or more sets of groups with the
same variable names.

While some variables have default values, it is recommended to be as explicit as possible
when preparing **required** file **roles/group_add/vars/groups.yml**

  - name: groupname
    - purpose: Unix group
    - permitted values: any valid Unix group name
    - type: string
    - default: none

  - name: issudo
    - purpose: Whether to add sudo access
    - permitted values: yes|no|true|false
    - type: string
    - default: undefined

  - name: issudoseparate
    - purpose: let operator decide whether to put sudo line in separate sudoers file in /etc/sudoers.d
    - permitted values: yes|no|True|False (not case sensitive)
    - type: bool
    - default: undefined

  - name: gid
    - purpose: GID number for the group
    - permitted values: number
    - default: undefined

  - name: sudo_definition
    - purpose: sudo line definition to add into sudoers
    - permitted values: sudo-compliant rule
    - default: 'ALL=(ALL) ALL'

## Examples

### Creating new groups for target devices

  - Prepare groups.yml with one or more groups (more examples are present in the file):
```
allgroups:
  - groupname: 'mygroup1'
    issudo: False
    issudoseparate: False
    gid: 2000
  - groupname: 'mygroup2'
    issudo: True
    issudoseparate: False
    sudo_definition: "ALL=(ALL) NOPASSWD: ALL"
```

  ```bash
  ht -A --playbook --ansible-args 'group_add.yml -v' 200001,200002
```

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      group_add.yml
```
