# user_lock

Lock and expire local Unix username

## Task Summary
  - Check if user exits
  - Get info from shadow file
  - Lock user
  - Update Gecos field with ticket number
  - Expire user

## Contributors
  - Author:          Piers Cornwell <piers.cornwell@rackspace.co.uk>
  - Maintainer(s):   Piers Cornwell, Intl Custom Linux

## Supporting Docs
  - N/A

## Assumptions
  - N/A

## Precautions
  - Won't operate on non-local (e.g. AD) users

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

  - `ticket` - Ticket number to use as a reference
    - permitted values: Any ticket number
    - type: string
    - default: none
    - required: Yes


## Examples

### Lock and expire the `dev` user

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      user_lock.yml -e username=dev -e ticket=180529-00000
   ```

### use the role to remove a list of users by creating a playbook

```yaml
  - name: lock this list of users
    hosts:
     - "200002"
     - "200001"
     gather_facts: false
     become: true
     vars:
       ticket: 700101-02010
       users_to_lock:
         - billy
         - hank
         - james
      tasks:
        - include_role:
            name: user_lock
          loop: "{{ users_to_lock }}"
          loop_control:
            loop_var: username
```
    
#### then invoke it

```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      your_user_lock.yml 
``` 
