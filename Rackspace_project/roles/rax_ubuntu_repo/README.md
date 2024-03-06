# rax_ubuntu_repo

Installs the Rackspace ubuntu repository and rs-inventory for dedicated servers
only.

There are four playbooks that call the role:
  - rax_ubuntu_repo_auth.yml - This playbook will prompt for credentials to be used to generate a token required to interact with the RHN API, it will also save the token in `/tmp/rhnapi_token` by default.
  - rax_ubuntu_repo.yml - This playbook will read from the cache file and will validate the token to be used.
  - patching_auth.yml - Similarly as `rax_ubuntu_repo_auth.yml` prompts for credentials to generate the token.  This play uses this role `rax_ubuntu_repo` as well as `rhn` removing the need to know upfront what type of Linux distro requires the patching/repo registration.
  - patching.yml - As the one above but does not prompt for credentials, it reads the cache token.

When adding repos to **only** cloud devices there is no need to use `rax_ubuntu_repo_auth.yml` this is meant for dedicated devices.

## Task Summary
  - Validates the server is supported.
  - For Dedicated servers:
    - Verify if cached token is valid
    - Authenticate when the cached token is not valid
  - Install python-apt (required by apt_repository)
  - Add rackspace pub key
  - Removes http rackspace repository
  - Adds https rackspace repository
  - For Dedicated Servers:
    - Install rs-inventory
    - Register

## Contributors
  - Author: Tony Garcia
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Supporting Docs
  - https://one.rackspace.com/display/Linux/Add+Rackspace+Ubuntu+Repo
  - https://one.rackspace.com/display/Linux/rs-inventory

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.4.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated, Public Cloud
  - OS: Ubuntu 14.04/16.04/18.04
  - Idempotent: Yes
  - Check Mode: Yes
  - ACE support: Yes

## Variables
  - `force` - Forces a registration, i.e recreates the registration code and the configuration file.
    - default: undefined
  - rhn_token - Uses a CORE token (this is used only for ACE)
  - `unregister` - Unregisters a server. This simply removes the package and cron job associated with rs-inventory.
    - default: false

## Examples

### Register dedicated devices performing authentication

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      rax_ubuntu_repo_auth.yml
```

Note: This is going to prompt for `username(SSO):` and `PIN+RSA` for authentication.
The token will be stored in `/tmp/rhnapi_token` by default.

### Register dedicated devices using cached token

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      rax_ubuntu_repo.yml
```

Note: This is going to read the token from `/tmp/rhnapi_token` by default, and will validate the token.

### Register dedicated devices using cached token and add repository to cloud servers

  ```bash
  TARGETS=200001,200002,12345678-90ab-cdef-1234-567890abcdef \
    ansible-playbook -i $(which --skip-alias ht) \
      rax_ubuntu_repo.yml
```

### Force Register dedicated devices using cached token

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      rax_ubuntu_repo.yml -e "force=true"
```
