# sophos

(Un)Installs sophos

## Tasks summary

This role includes a "connectivity_check" variable that's used to only perform OUTBOUND connectivity tests, see examples for further details.

By default attempts to install sophos even if a missmatch on the configuration is found (this is helpful with cloned devices), unless a variable is used to modify the behavior, see below.

### Notes

- This playbook is only capable of testing OUTBOUND connections. Any firewall rule blocking INBOUND connections should be solved apart.
- Genesis/Racknest rules allow INBOUND connection from the Sophos Update Manager (SMU) servers. The Racknest rules must be in the customer FW to allow that INBOUND traffic.

### On install
  - Validates Linux distro is supported.
  - Verifies if sophos is already installed.
    - If installed, it will verify if the files taking care of the ID for sophos matches the information of the server in question.
      - If there is a missmatch forces a reinstall of sophos.
  - Performs connectivity tests to sophos update managers.
  - On Debian based distros enables the 32bit architecture packages
  - Attempt to install the rs-sophosav-installer package
  - If that package is unavailable:
    - Installs package dependencies for sophos.
    - Downloads the python script to install sophos from http://rax.mirror.rackspace.com/segsupport/sophos/.
  - Runs the installer script (either from the package or the downloaded version)
  - For Ubuntu 16.04+ and RHEL/CentOS 7+ switches the on-access detection from talpa to fanotify.
  - Adds a list of temporal exclusions until there is a sync with the Sophos Update Manager server.

### On remove
  - Archives the configuration under `~rack/sophos-<TIMESTAMP>.tar.gz`.
  - Uninstalls sophos.
  - Removes the rs-sophos-installer package.

## Contributors
  - Author: Piers Cornwell
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Supporting Docs
  - https://one.rackspace.com/display/SegSup/Useful+Commands+for+Administering+Sophos+on+Linux+Servers
  - https://one.rackspace.com/display/SegSup/Sophos+Anti-Virus+for+Linux+9+Installation+Guide
  - https://one.rackspace.com/display/SegSup/Switching+Sophos+from+Talpa+to+Fanotify
  - https://one.rackspace.com/display/SegSup/Sophos+Endpoint+Networking+Requirements
  - https://one.rackspace.com/display/SegSup/Sophos+Anti-Virus+for+Linux+9+Troubleshooting+Guide
  - https://one.rackspace.com/display/SegSup/Rackspace+Default+Sophos+Endpoint+Ext%2C+File+and+Path+Exclusions#RackspaceDefaultSophosEndpointExt,FileandPathExclusions-LinuxFileandPathExclusions

## Assumptions
  - The server is able to install packages through a registration or a valid repository.
    - It is not a requirement to be registered against Rackspace infrastructure
    - However, access to either a Rackspace software repo (for the `rs-sophosav-installer` package) OR to https://rax.mirror.rackspace.com **IS** required

## Rollback
  - Manual

## Requirements
  - Ansible version: >= 2.5
  - Hammertime: >= 3.4.0
  - This playbook requires **root** access
  - Package dependency, documented in the [Sophos Linux Installation wiki](https://one.rackspace.com/display/SegSup/Sophos+Anti-Virus+for+Linux+9+Installation+Guide#SophosAnti-VirusforLinux9InstallationGuide-Prerequisites)
    - glibc.i686, kernel-headers (RHEL/CentOS)
    - libc6-i386, linux-generic (Ubuntu)

## Compatibility
  - Rackspace platform: Dedicated (CORE)
  - OS: RHEL/CentOS/OracleLinux 6/7/8, Ubuntu 16.04/18.04/20.04
  - Idempotent: Yes
  - Check Mode - No
  - ACE support: Yes

## Variables
  - `connectivity_check` - Only performs OUTBOUND connectivity checks
    - default: undefined

  - `remove` - Removes sophos when defined
    - default: undefined

  - `force` - Forces a install, i.e re-installs the AV by removing and then installing it again.
    - default: undefined

## Examples

### Connectivity Check

  ```
TARGETS=200001,200002 \
  ansible-playbook -i $( \which ht ) \
  sophos.yml -e connectivity_check=yes
```

NOTES:
  - Connectivity check will not be executed when attempting to remove.
  - The connectivity check always runs when installing(forced or default).
  - When `connectivity_check` is used no action(install/remove) is performed.

### Install

  ```
TARGETS=200001,200002 \
  ansible-playbook -i $( \which ht ) \
  sophos.yml
```
### Remove

  ```
TARGETS=200001,200002 \
  ansible-playbook -i $( \which ht ) \
  sophos.yml -e 'remove=yes'
```

NOTE: See that `remove` variable has to be defined to take effect, it means it does not matter the value passed to it, it could take `remove=1` or even `remove=dontknowwhattouse` and both will work.

### Reinstall (force)

  ```
TARGETS=200001,200002 \
  ansible-playbook -i $( \which ht ) \
  sophos.yml -e 'force=yes'
```

NOTE: See that `force` variable has to be defined to take effect, it means it does not matter the value passed to it, it could take `force=1` or even `force=dontknowwhattouse` and both will work.

---
