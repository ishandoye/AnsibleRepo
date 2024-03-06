# (oracle_rac_prep)

Configures the server ready to have Oracle RAC installed by the DBA team (does not install oracle)

## Task Summary
  - Configures second bonded interface (heartbeat)
  - Configures MTU on heartbeat interface
  - Configures NTP
  - Ensures SAN names match

## Contributors
  - Author: Mike Frost <mike.frost@rackspace.co.uk>
  - Maintainer: Mike Frost

## Supporting Docs
  - https://one.rackspace.com/display/Linux/Oracle+Linux+RAC+Configuration

## Assumptions
  - The oracle_prep playbook has been run before this
  - The playbook is being run on exactly 2 servers
  - Networking is patched appropriately
  - SAN storage is presented

## Precautions
  - The Assumptions have been met

## Rollback
  - No

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - Requires **root**

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL / CentOS
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - None

## Examples

  ```bash
ht -A --playbook --ansibleargs='oracle_rac_prep.yml -b ' 674529
```
