# user_add

Add a new local user(s) optionally with sudo rights

## Task Summary
  - Add user(s)
  - Update and validate /etc/sudoers

## Contributors
  - Author:          Piers Cornwell <piers.cornwell@rackspace.co.uk>
  - Maintainer(s):   Piers Cornwell, Intl Custom Linux

## Supporting Docs
  - N/A

## Assumptions
  - Any existing entry for the user in sudoers will be lost

## Precautions
  - Sudoers will be validated after editing with visudo -c

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
  - `username` - Unix username
    - permitted values: any valid Unix username
    - type: string
    - default: none
    - required: Yes
  
  - `comment` - Gecos field value
    - permitted values: Any valid Gecos field value (or blank)
    - type: string
    - default: none
    - required: Yes
  
  - `pwdhash` - /etc/shadow salted password hash 
    - permitted values: Any valid salted password hash. You should 
    -   use SHA512 hashing
    - type: string
    - default: none
    - required: Yes
  
  - `group` - Primary group name
    - permitted values: comma delimited list or ansible list.
    - type: list or ansible list
    - default: same as username
    - required: Yes
  
  - `addgroups` - Supplemental group names
    - permitted values: comma delimited list or ansible list.
    - type: list or ansible list
    - default: none
    - required: Yes
  
  - `issudo` - Whether to add sudo access
    - permitted values: y OR n
    - type: string
    - default: 'n'
    - required: Yes


## Examples

### Add a local user (prompt for variables)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      user_add.yml
```

##### Note: 
- This role accepts either:
  - Just the variables above on their own (you will be prompted by default) OR
  - A list of named "users" containing one or more sets of users with the same variable names. 
- See user_add.yml for examples of both methods.
