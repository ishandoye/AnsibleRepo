# sftp_useradd

Allow to create a chrooted sftp user.

## Task Summary
  - Validates `sftp_user` if provided
  - Creates a sftp group
  - Creates sftp user
  - Fails if user is already in place, unless `force_user` is defined
  - Creates a random password for the sftp user
  - Includes sftp subsystem configuration content into sshd_config
  - Adds sshd_config sftp config block
  - Reloads sshd service
  - Correct home directory permissions
  - Create/set permissions to the `real_mount` directory (if `real_mount` is provided)
  - Creates a bind mount to a specific directory if it is specified (if `real_mount` is provided)
  - Prints out the login credentials

## Contributors
  - Author(s): GTS Linux Automation Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automation Engineers

## Supporting Docs
  - https://one.rackspace.com/display/Linux/Configuring+a+Chrooted+SFTP-Only+User

## Assumptions
  - sshd service is installed and configured on server
  - sftp users will be chrooted to their home directory('/home/chroot/USER')
  - bind mount(s) will only be created for external directory access if `real_mount` or `multi_mount` is
    provided (otherwise no bind mount is created)
  - If the provided 'real_mount' is provided and is already created, the permissions will be modified, see Precautions

## Precautions
  - sshd configuration file will be modified.
  - The sshd service will be reloaded when config test is successful.
  - The `real_mount` will change permissions
    - Mode: 2775
    - Ownership: root:`sftp_group`

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.7.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated and Cloud
  - OS: RHEL 6/7/8, CentOS 6/7, Ubuntu 14.04/16.04/18.04/20.04
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - `sftp_user` - Username to be created
    - permitted values: a valid unix username
    - type: string
    - default: None
    - required: Yes

  - `sftp_group` - Group name to be created
    - permitted values: a valid unix group name
    - type: string
    - default: sftponly
    - required: No

  - `real_mount` - The directory which requires access by the sftp user
    - permitted values: A valid unix path
    - type: string
    - default: None
    - required: Yes

  - `bind_mount` - A directory name which will be created on chrooted home folder and will be bind mounted to the 'real_mount' directory
    - permitted values: a valid folder name
    - type: string
    - default: sftp_upload
    - required: No

  - `multi_mount` - A list of dictionaries containing `real_mount` and `bind_mount` that will be used to
  configure multiple bind mounts in a users chrooted home folder.
    - permitted values: a list of dictionaries (`[{"real_mount": PATH, "bind_mount": DIR}]`)
    - type: list
    - default: None
    - required: No

## Examples

### Create a chrooted sftp user called `peter` when `peter` does not already exist on the device

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      sftp_useradd.yml \
      -e sftp_user=peter \
      -e sftp_group=sftponly \
      -e real_mount=/var/www/vhosts/example.com \
      -e bind_mount=website
```

### Create a chrooted sftp user where the user already exists on the device (resets the user password)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      sftp_useradd.yml \
      -e sftp_user=peter \
      -e sftp_group=sftponly \
      -e real_mount=/var/www/vhosts/example.com \
      -e bind_mount=website
      -e force_user=yes'
```
