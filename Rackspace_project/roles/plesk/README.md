# Plesk
## Task Summary
  - Uninstalls packages that would conflict with Plesk
  - Downloads Plesk installer
  - Installs Plesk
  - Configures with best practices
  - Downloads and installs license from [Stepladder Plesk License Manager](https://stepladder.rax.io/plm) (optional)

## Contributors
  - Author: Mike Frost <mike.frost@rackspace.co.uk>
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Supporting Docs
  - https://one.rackspace.com/pages/viewpage.action?spaceKey=Linux&title=Linux+Plesk+Fresh+Install+of+Plesk
  - https://one.rackspace.com/display/Linux/Linux+Plesk+Licensing

## Assumptions
  - Machine is running a supported operating system.
  - Role will only attempt to open access to Plesk panel if firewalld is installed. Opening access via any other firewall will need to be handled manually.
  - When passing the variable `racker_token`, the role will assume the intent is to retrieve a license for Plesk. This will require the user to be part of the LDAP group `lnx-gts-plesk-admins`.

## Precautions
  - This role should only be run on servers not yet in production.
  - The environment variable `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` may need to be set to avoid errors on macOS.
  - This role will not overwrite a license if one is already installed. Consider [manually installing a license](https://one.rackspace.com/display/Linux/Linux+Plesk+Licensing#LinuxPleskLicensing-AddingPleskStep2-AllocateLicense) or removing the installed license in [`/etc/sw/keys/keys`](https://support.plesk.com/hc/en-us/articles/214027409-How-to-remove-a-license-from-Plesk-server-via-CLI-).

## Rollback
  - No

## Requirements
  - **Ansible**: >= 2.11
  - **Hammertime**: >= 3.11.0
  - Requires **root**

## Compatibility
  - OS:
      - RHEL/Rocky/AlmaLinux 8
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - `release_tier`: Defaults to `stable`. This variable is used to set the release tier from which to install Plesk components. Four tiers are available for selection: development, testing, release, stable.
  - `racker_token`: Used to authenticate to Stepladder to retrieve license. Requires user to be part of LDAP group `lnx-gts-plesk-admins`.


## Examples
### Install Plesk
```bash
env TARGETS=12345 ansible-playbook --inventory $(which ht) plesk.yml
```

### Install Plesk on core device and avoid prompts
Execution may be paused for a prompt to retrieve a CORE token. This can be avoided by setting the variable `core_token` at execution time.
```bash
env TARGETS=12345 ansible-playbook --inventory $(which ht) --extra-vars core_token=2fdb57632a37a38d43b6c386ccab9125 release_tier=stable plesk.yml
```

### Install Plesk and install license
Retrieving a license via Stepladder requires the var `racker_token` to be set.
```bash
env TARGETS=12345 ansible-playbook --inventory $(which ht) --extra-vars racker_token=$(ht --get-token) plesk.yml
```
