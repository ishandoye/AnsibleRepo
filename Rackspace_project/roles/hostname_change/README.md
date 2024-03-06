# hostname_change

Change system hostname

## Task Summary
  - Check whether Plesk CP is installed on the server, if it is hostname is updated via plesk cli.
  - For non plesk servers, update hostname
  - Update /etc/hosts with FQDN hostname and shortname
  - Update /etc/sysconfig/network with FQDN hostname and domain prefix
  - Update /etc/resolv.conf with new domain prefix
  - Update Postfix /etc/postfix/mydomains and /etc/postfix/main.cf
  - Verify whether any mysql user names available with old hostname
  - If mysql binary log enabled, requests to update my.cnf file with new hostname

## Contributors
  - Authors: Piers Cornwell and GTS Linux Automation Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automation Engineers

## Supporting Docs
  - https://one.rackspace.com/display/Linux/Changing+the+Hostname+on+Linux

## Assumptions
  - N/A

## Precautions
  - N/A

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.2.0.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated and Cloud
  - OS: RHEL + clones 6/7/8, Ubuntu 14.04/16.04/18.04/20.04
  - Idempotent: Yes
  - Check Mode: No

## Variables
  - `hostname` - New fully qualified hostname
    - permitted values: Valid hostname(s) with device ids
    - type: dictionary
    - default: none
    - required: Yes

## Examples

### Change the system hostname
Note: The playbook allows you to change hostname on multiple devices simultaneously and thus requires the extra-vars variable to be json format. 

  ```bash
  cat json_data
  {
      "hostname":{
          "200001": "200001-example.co.uk",
          "200002": "test.co.uk"
          }
  }
```

  ```bash
  TARGETS=200001,200002 ansible-playbook -i $(which ht) -e @json_data
```
Note: The content of json_data will be something similar to the above example data.

