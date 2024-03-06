# pcs_hide_fence_passwords

Hides fencing passwords on PCS clusters

## Task summary
  - Check all hosts are in a PCS cluster
  - Check playbook is being run against all of the nodes in the cluster
  - Check directory /var/lib/pacemaker/.gnupg does not exist on any host
  - Gather current passwords from PCS configuration
  - One ONE host:
    - Install & start haveged daemon to ensure sufficient entropy is present
    - Generate gpg keyring in /var/lib/pacemaker/.gnupg with blank passphrase
    - Create one gpg encrypted file per fence device with the password for that fence device
    - Archive gpg files & transfer to localhost
  - Copy & unpack gpg file archive to all hosts
  - Create one script per fence device in /usr/local/bin to return the password from the gpg file
  - Configure each fence device to retrieve the password via script
  - Stop & uninstall the haveged daemon if we installed it
  - Cleanup temporary files

## Contributors
  - Author: Paul Whitaker <paul.whitaker@rackspace.co.uk>
  - Maintainer(s): Paul Whitaker

## Supporting Docs
  - https://one.rackspace.com/display/Linux/PCS+-+Hiding+Fence+Passwords

## Assumptions
  - PCS cluster configured
  - Playbook is run against all nodes in a single cluster
  - All stonith resources have passwords configured

## Precautions
  - Checks /var/lib/pacemaker/.gnupg does not exist
  - Checks all hosts are part of the same PCS cluster
  - Checks that the playbook is run against all nodes in the cluster
  - Any failure of the checks will stop the playbook before any changes are made

## Rollback
  - Manual:
    - Until the step to update the stonith resources is run, you can clean up by
      just deleting the /var/lib/pacemaker/.gnupg directory on each node, and removing
      the password retrieval scripts from /usr/local/bin

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access
  - Remote:
    - PCS cluster configured
    - Playbook is run against all nodes in the cluster
    - /var/lib/pacemaker/.gnupg does NOT exist on any host

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL 7, CentOS 7
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - None

## Examples

### Run against all nodes in a cluster
  ```bash
  TARGETS=661129,661130 ansible-playbook -i $(which --skip-alias ht) pcs_hide_fence_passwords.yml
  ```
