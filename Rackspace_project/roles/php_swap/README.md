# php_swap

Ansible playbook for performing PHP upgrades/downgrades. Also available via https://stepladder.rax.io/phpswap

## Task Summary
  - OS family, IUS repo, yum-plugin-replace, Plesk, target PHP package

## Prerequisites
  - Plesk, Magento, and WordPress are not installed
  - PHP is not installed via remi-safe
  - It is allowed to upgrade from a deprecated PHP version to a newer version, but not to downgrade to a deprecated version

### Pre swap:
  - Distro version agnostic prerequisites, followed by distro specific prerequisites, are run
  - PHP information is gathered via the `php` Raxfact
  - Currently installed PHP packages are enumerated
  - The execution will stop at this stage if playbook is run in "check-only" mode

### During swap:
  - EL7 will use yum-plugin-replace to perform the swap; the plugin will be installed if needed
  - EL8 will uninstall all PHP packages, reset the PHP module, enable the new module, and install either php or php-fpm as directed

### Post swap:
  - PHP packages and modules installed prior to the swap are reinstalled if possible. EL7 will appropriately rename the packages, e.g. if `php-xml` was installed, it will attempt to install `php74-xml` if installing `mod_php74`.
  - The php-fpm service is started if it was running before the swap

## Contributors
  - Maintainers: GTS Linux System/Automation Engineers

## Assumptions
  - No file/config backups are being taken and the only information provided is the prechecks/execution ansible runtime output
  - Plesk PHP swaps are not supported and the execution will stop when package sw-cp-server is installed
  - Likewise Magento and WordPress are unsupported
  - remi-safe is unsupported
  - Any PHP module warnings must be resolved before using this tool
  - The IUS repository needs to be already installed when trying to upgrage to an IUS version of PHP for EL7
  - Only PHP modules installed from the repositories can be handled (no pecl/pear compiled modules can be replaced)

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.8
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: Red Hat family version 7 and 8 (e.g. RHEL 7/8, CentOS 7/8, Oracle Linux 7/8)
  - Idempotent: No
  - Check Mode: No

## Variables
  - `replace_with` - PHP module to swap to
  	- required: True
    - type: string
    - permitted_values: `php`, `php-fpm`, `mod_php74`, `php74-fpm`
    - for EL8, only `php` and `php-fpm` are permitted
  - `appstream_version` - the PHP version to enable using EL8's appstreams
    - default: `7.2`
    - type: string
    - permitted_values: `7.2`, `7.3`, `7.4`, `8.0`, `remi-7.2`, `remi-7.3`, `remi-7.4`,`remi-8.0`, `remi-8.1`
