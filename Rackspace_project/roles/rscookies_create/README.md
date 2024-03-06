# rscookies_create

Creation of Rackspace cookie files consumed by other tools.

## Tasks summary
  - Creates Rackspace cookies and sets the noadc file.
  - Cookies are located by default in `/root/.rackspace` and they are:
    - customer_number
    - datacenter
    - kick
    - kick_date
    - segment
    - server_number
    - primary_user
  - The `noadc` file is located in `/boot/.rackspace/noadc`
  - If the expected content for a cookie is in place it will not change, but for:
    - kick_date  - This is always set to the time the playbook was executed.

## Contributors
  - Author: Sean Dennis, Tony Garcia
  - Maintainer: GTS Linux Systems Engineers <GTS-Linux-Systems-Engineers@rackspace.com>

## Supporting Docs
  - [KickCookies](https://one.rackspace.com/display/Linux/Kick+Cookies)


## Assumptions
  - None

## Precautions
  - Will override files if they don't match the values obtained from CORE.


## Rollback
  - Manual

## Requirements
  - **Ansible** >= 2.4.0.0
  - **Hammertime** >= 3.4.0
  - This playbook requires **root** access.

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL / CentOS / Ubuntu
  - Idempotent:  No (`kick_date` will be different each time, **does not** break a box)
  - Check Mode: Yes
  - ACE support: Yes

## Variables
  - remove: Defaults to false. Set to true if you want to remove Rackspace cookies.

## Examples

1. Define an env variable with list of devices then run ansible and use ht as the inventory script:

    ```
    TARGETS=DEVICE[,DEVICE] ansible-playbook -i $(which --skip-alias ht) rscookies_create.yml
    ```

1. Run ansible with a wrapper script that runs ht

    ```
    ansible-playbook -i wrapper.sh playbook.yml
    ```

    Where `wrapper.sh` is a call to ```ht --ansible-dyn-inv DEVICE[,DEVICE]```


1. Create the inventory, then have ansible read it, this helps to allow multiple runs on ansible without hammering CORE.

    ```
    ht --ansible-dyn-inv [DEVICE[,DEVICE]] > /some/path/inventory.json
    ansible-playbook -i cat_wrap.sh rscookies_create.yml
    ```

    Where `cat_wrap.sh` is simply an execution of `cat` of the json inventory file.

