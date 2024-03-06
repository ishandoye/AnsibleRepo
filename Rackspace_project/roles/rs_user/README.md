# rs_user

Creates `rack` user and required groups if missing.

This is mainly executed through ACE, but can be executed with hammertime's inventory as well as long as valid credentials are defined in the `login user` and `login password` for the device(s) in CORE.

## Task Summary
  - Obtain CORE data
  - Fail if a Core Token is not provided
  - Create default groups depending on the distribution.
  - Obtain the rack password from core or the inventory and create a hash from it.
  - Create rack group and a rack user with the hash created.
  - Add rack to sudoers.
  - Disable requiretty in sudoers.

## Contributors
  - Author: Tony Garcia <tony.garcia@rackspace.com>
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Precautions
  - This role expects valid credentials to be set in the "login user" and "login password" fields in CORE. 
The role cannot complete with just "rack" credentials in place since the role will update the shadow file even if the current password is valid.

## Rollback
  - Manual intervention is required to roll back changes.

## Requirements
  - **Ansible**: >= 2.5.0
  - root privileges
  - Valid credentials must be defined for the `login user` and `login password` in CORE

## Compatibility
  - Rackspace platform: Dedicated(RPC-V)
  - OS: RHEL / CentOS / Ubuntu / Debian
  - Idempotent: No
  - Check Mode: No

## Variables
  - `core_token` - Used for obtaining rack user password listed in CORE.
    - permitted values: Must be a valid hash.
    - type: string
    - default: None

  - `remove` - Sets whether the rack user is removed or added.
    - permitted values: true, false
    - type: boolean
    - default: false

## Examples

This role is mainly executed through ACE.

This is an example when executed using hammertime's inventory:
  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      rs_user.yml -e core_token=TOKEN
```
