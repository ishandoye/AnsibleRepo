# (oracle_prep)

Configures the server so it's ready to have Oracle installed by the DBA team (does not install Oracle)

## Task Summary
  - Installs relevant packages and configures yum
  - Configures NTP & SAR
  - Configures Transparent Huge Pages
  - If Sophos is installed on-access exclusions will be created for: `/u01/app` and `/dev/shm`

## Contributors
  - Author: Mike Frost <mike.frost@rackspace.co.uk>
  - Maintainer(s): Tony Garcia, Sean Dennis

## Supporting Docs
  - https://one.rackspace.com/pages/viewpage.action?spaceKey=Linux&title=Oracle+Linux+Node+Configuration
  - [Notes regarding sophos exclusions](https://one.rackspace.com/display/SegSup/Sophos+Linux+Installation#SophosLinuxInstallation-PostInstallationSteps)

## Assumptions
  - The /u01 partition is mounted and larger than 100Gb
  - The system has 32Gb swap
  - The server has access to the DBA servers (dfworacle1.racscan.com)

## Precautions
  - The Assumptions have been met

## Rollback
  - No

## Requirements
  - **Ansible**: >= 2.5.11
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
ht -A --playbook --ansibleargs='oracle_prep.yml' 200001
```

or

  ```bash
TARGETS=200001 ansible-playbook -i $(\which ht) oracle_prep.yml
```

