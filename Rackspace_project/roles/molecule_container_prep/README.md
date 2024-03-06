# molecule\_container\_prep

This role is intended to make a containerized operating system closer to Rackspace's dedicated server environment.
This allows for roles written to be executed on Rackspace managed devices to be executed in a containerized environment for testing.

## Task Summary
  - Installs packages specified in list `packages` defined in `vars/main.yml`.
    - If the initial package installation fails then the selinux pseudo file system is remounted as read-only and package installation is reattempted.

## Contributors
  - Author: Sean Dennis <Sean.Dennis@rackspace.com>
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Supporting Docs
N/A

## Assumptions
This will only run on RHEL, CentOS, and Ubuntu.

## Precautions
This role will attempt to remount the psuedo filesystem `/sys/fs/selinux` as read-only if the initial package installation fails.

## Rollback
N/A

## Requirements
  - **Ansible**: >= 2.5.0
  - Requires **root**

## Compatibility
  - Rackspace platform: Cloud / Dedicated / All
  - OS: RHEL / CentOS / Ubuntu
  - Idempotent: Yes
  - Check Mode: No

## Variables
N/A

### Describe and list examples of usage here

```yaml
- name: Prepare container for testing
  include_role:
	name: molecule_container_prep
```

