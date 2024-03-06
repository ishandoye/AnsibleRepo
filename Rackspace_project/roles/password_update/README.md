# password_update

Set local user password and saves password to __/tmp/$(username).credentials.txt__

Alternatively, if you already have a predefined password, simply create __/tmp/$(username).credentials.txt)__ with the desired password as its only content.

## Task Summary
  - Check username is local
  - Update password

## Contributors
  - Author:          Pete Travis <pete.travis@rackspace.com>
  - Maintainer(s):   Pete Travis

## Supporting Docs
  - Note that the password will have rounds=656000 which will make log ins a little slower than by default, ref. https://github.com/ansible/ansible/pull/26640

## Assumptions
  - Password complexity will be alphanumberic, 12 chars

## Precautions
  - Checks user is local (i.e. not a domain user)

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.3.0.0
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

## Examples

### (Re)Set a local user's password to something random

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      password_update.yml -e username=racker
```
