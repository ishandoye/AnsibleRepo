# nimbus_disable_fs_monitor

Disable Nimbus monitor for filesystem in cdm probe either fully or only for space alerts (including inodes)

## Task Summary
  - Check for mount point
  - Work out where Nimbus config is
  - Backup cdm.cfg
  - Modify config, now includes ensuring targeted mount point is actively monitored when desired
  - Restart Nimbus

## Contributors
  - Author:          Ricardo Cordeiro <ricardo.cordeiro@rackspace.co.uk>
  - Maintainer(s):   Ricardo Cordeiro, Intl Custom Linux

## Supporting Docs
  - N/A

## Assumptions
  - N/A

## Precautions
  - Old config is backed up

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.2.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL 6/7, CentOS 6/7, Ubuntu 14.04/16.04
  - Idempotent: No
  - Check Mode: No

## Variables
  - `ticket` - For backup directory under /home/rack
    - permitted values: Ticket number
    - type: string
    - default: none
    - required: Yes
 
  - `mount_point` - Mount point to disable, e.g. /var/log
    - permitted values: Mount point number
    - type: string
    - default: none
    - required: Yes

  - `disable_check` - Whether the mount point is to be fully disabled or only for space monitoring.
    - permitted values: Yes, No, True, False
    - type: boolean
    - default: none
    - required: Yes

## Examples

### Disable monitor for a mount point (prompt for variables)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      nimbus_disable_fs_monitor.yml
```

### Fully disable monitoring of /data

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      nimbus_disable_fs_monitor.yml -e ticket=180529-00000 -e mount_point="/data" -e disable_check=Yes
```
