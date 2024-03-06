# sssd_ad

Configure sssd-ad for Customer, GlobalRS or Intensive AD.

## Task Summary
  - Install required packages.
  - Checks if the server has already joined the domain.
  - Tests that the `DNSSERVERS` provided will resolve Rackspace IPs (skippable) and required AD records (Customer AD only - GlobalRS/Intensive AD will check using the contents of `/etc/resolv.conf`)
  - Checks that the authconfig symlinks for pam are still present (EL7 only)
  - Changes resolv.conf by using the `DNSSERVERS` defined (Customer AD only).
  - Creates the kerberos configuration(krb5.conf).
  - Updates system crypto policy for AD (EL8/9 only)
  - Gets a kerberos ticket.
  - If rejoining, removes old kerberos keytab.
  - Disables services that are not needed, e.g. nslcd, winbind, nscd.
  - Clears any SSSD Cache.
  - Creates the samba configuration(smb.conf).
  - Joins the server to the domain.
  - Adds the server to the ACCT-AllUsers group (Intensive/GlobalRS AD only)
  - Creates the sssd configuration(sssd.conf).
  - Limit logins to customer AllUsers group and Racker Intensive .cust logins (GlobalRS/Intensive AD only)
  - Enable sudo for Intensive .cust users. (GlobalRS/Intensive AD only)
  - Sets the Max for UID and GID to avoid conflicts with AD.
  - Creates a backup of the authentication configurations in `/root/.rackspace/authbackup` (only for Red Hat based OS).
  - Enables sssd through authconfig/authselect (only for Red Hat based OS).
  - Enables automatic creation of home directories for new users.
  - Enables sssd service.
  - Remove kerberos ticket used for domain join
  - Warn if more than 3 DNS servers are defined
  - Provides any Manual steps to be completed including restarting sssd.

## Contributors
  - Author: Piers Cornwell
  - Maintainer(s): GTS Linux System Engineers

## Supporting Docs
  - https://one.rackspace.com/display/Linux/AD+on+Linux+-+sssd-ad

## Assumptions
  - Some form of network time sync (ntpd, chronyd, systemd-timesyncd, etc) must be in place. (On Dedicated ADC takes care of this already)
  - Default symlinks for authconfig must still be in place on EL6 & EL7 (e.g. /etc/pam.d/password-auth -> /etc/pam.d/password-auth-ac)

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.11 (for correct detection of Rocky Linux)
  - **Ansible**: >= 2.9.19 (for correct detection of AlmaLinux)
  - **Ansible**: >= 2.8
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL/CentOS/OracleLinux 6/7/8/9, Rocky Linux 8/9, AlmaLinux 8/9, Ubuntu 16.04/18.04/20.04/22.04
  - Idempotent: No
  - Check Mode: No

## Variables
  - `type` - Select `customer`, `intensive`, `globalrs`
    - permitted values: `customer` / `intensive` / `globalrs`
    - type: string
    - default: none

### For `intensive` or `globalrs`
  - `JOINACCT` - Username for AD join
    - permitted values: Intensive user name (`@INTENSIVE.INT` will be automatically appended if it isn't present)
    - type: string
    - default: none

  - `JOINPWD` - Password for `JOINACCT`
     - permitted values: Password
     - type: string
     - default: none

  - `JOINAGAIN` - Whether to attempt to join AD even if already joined
    - permitted values: `y` / `n`
    - type: string
    - default: `n`

### For `customer`

  - `DOMAIN` - AD domain
    - permitted values: *A domain name*, e.g. example.com
    - type: string
    - default: none

  - `WORKGROUP` - Windows workgroup
    - permitted values:*A Workgroup*, e.g. EXAMPLE, or `magic` to autogenerate
    - type: string
    - default: `magic`; this will use the subdomain, i.e. the left part of server's domain, e.g. for sub.example.com will use SUB, for example.com will use EXAMPLE

  - `JOINACCT` - AD join username
    - permitted values: *A username*, e.g. `rack` (`@DOMAIN` will be automatically appended if no `@` is present in the name)
    - type: string
    - default: none

  - `JOINPWD` - Password for JOINACCT
    - permitted values: Password - type: string - default: none

  - `DNSSERVERS` - Comma separated list of DNS IP servers
    - permitted values: DNS server IPs, e.g. 173.203.4.8,173.203.4.9
    - type: string
    - default: none

  - `ENUMERATE` - Whether to allow listing all users with for example getent passwd
    - permitted values: `y` / `n`
    - type: string
    - default: `n`

  - `JOINAGAIN` - Whether to attempt to join AD even if already joined
    - permitted values: `y` / `n`
    - type: string
    - default: `n`

  - `ALLOW_GROUPS` - A comma separated list of AD groups which SSSD will whitelist for login access.  Users who are a not a member of listed groups will not be allowed access.
    - type: string
    - permitted values: `n` for n/a (any valid user can log in) or comma separated list of validated AD groups
    - default: `n`
   
  - `DOMAIN_CONTROLLERS` - A comma separated list of preferred (datacenter local) domain controllers to be added to a `[realms]` block in krb5.conf and `ad_server` line in sssd.conf. For the case that a customer domain spans datacenters and DNS SRV records include unreachable IPs preventing successful domain joins. The `sssd_ad_customer_setup.yml` playbook does not prompt for this variable since it is not typically needed, but it can be specified with `-e` as in the examples below.
    - type: string
    - permitted values: domain controller hostnames, e.g. 123456-dc1.example.com,123457-dc2.example.com
    - default: none

  - `skip_rackspace_dns` - Allows skipping of the tests that various Rackspace hostnames resolve, for the case when the customer server is receiving packages from a non-Rackspace source (e.g. public repositories or directly from Red Hat), and therefore doesn't need to be able to resolve our IPs to install anything.  The `sssd_ad_customer_setup.yml` playbook does not prompt for this variable since it is not typically needed, but it can be specified with `-e` as in the examples below.
    - type: boolean
    - permitted values: anything that Ansible can resolve to a boolean value
    - default: false

## Examples

### For `Intensive` AD

  ```bash
  TARGETS=<SERVERNUM>[,<SERVERNUM>] ansible-playbook -i $( which --skip-alias ht ) \
    sssd_ad_intensive_setup.yml
```

OR

  ```bash
  TARGETS=<SERVERNUM>[,<SERVERNUM>] ansible-playbook -i $( which --skip-alias ht ) \
    sssd_ad_intensive_setup.yml \
    -e "JOINACCT=<sso.cust>"
```

### For `GlobalRS` AD

  ```bash
  TARGETS=<SERVERNUM>[,<SERVERNUM>] ansible-playbook -i $( which --skip-alias ht ) \
    sssd_ad_globalrs_setup.yml
```

OR

  ```bash
  TARGETS=<SERVERNUM>[,<SERVERNUM>] ansible-playbook -i $( which --skip-alias ht ) \
    sssd_ad_globalrs_setup.yml \
    -e "JOINACCT=<sso.cust>"
```

### For `Customer` AD

  ```bash
  TARGETS=<SERVERNUM>[,<SERVERNUM>] ansible-playbook -i $( which --skip-alias ht ) \
    sssd_ad_customer_setup.yml
```

OR
  ```bash
  TARGETS=<SERVERNUM>[,<SERVERNUM>] ansible-playbook -i $( which --skip-alias ht ) \
    sssd_ad_customer_setup.yml \
    -e "DOMAIN=<CUSTOMER.DOMAIN>" \
    -e "WORKGROUP=<CUSTOMERWORKGROUP>" \
    -e "ADDOMAIN=<CUSTOMER.DOMAIN>" \
    -e "JOINACCT=<user@WORKGROUP.COM>" \
    -e "DNSSERVERS=<DNS_IP1,DNS_IP2>" \
    -e "skip_rackspace_dns=1"
```
