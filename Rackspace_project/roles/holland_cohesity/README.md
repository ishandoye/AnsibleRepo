# Install rs-holland-cohesity

Role to install rs-holland-cohesity package on servers, replacing
rs-holland-config if present.

Any existing holland configuration will be preserved

Ubuntu servers will be switched from getting holland from the RS repostories on
rax.mirror.rackspace.com to our mirror of the upstream SUSE Open Build System
repository instead

## Task summary

- Check if `rs-holland-cohesity` is already installed, stop immediately if it is
- Check for and backup existing holland config files that have been changed from
  the version present in the install packages (using `rpm -V` or `dpkg -V`)
- Ensure repositories for installation are configured properly  
  - **RHEL-based devices**
    - rackspace-rax repo (to get packages from rax.mirror.rackspace.com)
    - EPEL (to get holland packages)
        - `epel-release-rackspace` will be installed if no other EPEL repository
          is already present
  - **Debian/Ubuntu devices**
    - `rax.mirror.rackspace.com/ubuntu` or `rax.mirror.rackspace.com/debian`
    - OBS holland-backup mirror at 
        `mirror.rackspace.com/opensuse/repositories/home:/holland-backup`
        - Upstream repo will be left in place if it is already configured
    - `holland` package will be pinned to only install from the OBS repo
- Uninstall `rs-holland-config` if it is present
  - Ubuntu 18.04 & 20.04 **only**
    - Uninstall any other `holland*` packages that might have come from
      `rax.mirror.rackspace.com`
- Install `rs-holland-cohesity`
- Restore backups of holland configuration files if they were taken earlier

## Precautions
Any configuration files that have been modified from the base packages are
backed up before any further actions are taken, and will be restored at the end
of the process.  
The backup files will be created by copying the config file with the extension
`.backup` in the same directory - any pre-existing `.backup` file will be
renamed by Ansible to include a timestamp

## Rollback
- Manual

## Requirements:
 - Ansible >= 2.11
 - **root** access
 - Devices need access to
   - https://mirror.rackspace.com
   - https://rax.mirror.rackspace.com

## Compatibility:
 - OS:
    - RHEL & clones 6/7/8/9
    - Ubuntu 18.04, 20.04, 22.04
    - Debian 10 & 11
 - Idempotent: Yes

## Example
```bash
TARGETS=200001,200002 ansible-playbook -i $(which ht) holland-cohesity.yml
```

## Molecule testing
Tests are provided via Molecule - there is one environment variable that can be
set to control whether the tests should pre-install `rs-holland-config` and
change some config files (to verify that configs are retained), or if a clean
install should be performed:
 - `INSTALL_RS_HOLLAND_CFG`: whether to pre-install `rs-holland-config`
   - 1 (default): pre-install `rs-holland-config`
   - 0: leave the test container empty of any holland packages

Note that the molecule tests **do not** verify the functionality of the
`rs-holland-cohesity` packages (that testing is done in the main
[rs-holland-cohesity](https://github.rackspace.com/SupportTools/rs-holland-cohesity)
repository) - only that the packages install correctly, and retain previous
configuration files.
