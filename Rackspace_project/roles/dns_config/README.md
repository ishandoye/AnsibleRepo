# dns_config

Configure DNS resolver config file with Rackspace name servers

## Task Summary
  - Obtain and validate Primary and Secondary DNS FQDN and IP in the exec node
    - For MacOSX will use `dig`
    - For Anything else will use `getent`
  - Ensure RAX DNSs IPs and search domain are in resolver config file
  - Add Rackspace custom NetworkManager config (EL7 only)
  - Verify that server can resolve domains using configured name servers

## Contributors
  - Author: Sean Dennis
  - Maintainer(s): Sean Dennis, Tony Garcia

## Supporting Docs
  - https://one.rackspace.com/display/GET/Linux+ADC#LinuxADC-ConfigureDNS-LADC

## Assumptions
  - None

## Precautions
  - Default resolver config file (/etc/resolv.conf) will be replaced with Rackspace defaults.

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.7.x
  - **Hammertime**: >= 4.6.x
  - This playbook requires **root** access
  - MacOS users: `netaddr` python library is required (included in ansible install via brew)

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL 6/7, CentOS 6/7, Ubuntu 14.04/16.04/18.04
  - Idempotent: Yes
  - Check Mode: Yes
  - ACE support: Yes

## Variables
  - None

## Examples

### Configure resolver config file

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      dns_config.yml
```

### Configure resolver config file (check mode)

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(\which ht) \
      dns_config.yml --check
```
