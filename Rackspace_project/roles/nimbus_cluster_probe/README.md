# nimbus_cluster_probe

Installs and configures Nimbus Cluster Probe on RHCS cluster node

## Task Summary
  - Gathers info about RHCS cluster (clustat)
  - Gathers info about Nimbus Robot
  - Moves both nodes in cluster to the same Nimbus hub they weren't
  - Install cluster probe if not running:
    - Reinstall cdm and processes probes (ensures they are at latest version)
    - Wait for them to start
    - Install cluster probe
    - Wait for it to start
 - Configure CDM probe to monitor cluster FS
 - Configure processes probe to monitor cluster processes
 - Configure cluster probe
 - Wait for the cluster probe to initialize correctly, fail otherwise


## Contributors
  - Author:          Tomas Mazak <tomas.mazak@rackspace.co.uk>
  - Maintainer(s):   Tomas Mazak

## Supporting Docs
  - [Nimbus Linux Clusters](https://one.rackspace.com/display/SegSup/Nimbus+Linux+Clusters)
  - [Nimbus Overview](https://one.rackspace.com/display/SegSup/Nimbus+Overview)

## Assumptions
  - Nimbus is already installed and working
  - Should be run against both nodes in the cluster in one run (otherwise Nimbus hub consistency can't be checked - warning displayed)

## Precautions
  - N/A

## Rollback
  - Manual (nimbus_install playbook can be used)

## Requirements
  - **Ansible**: >= 2.3.0.0
  - **Hammertime**: >= 3.4.0
  - **Jinja2**: >= 2.8
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated
  - OS: RHEL/Centos 6 RHCS clusters only
  - Idempotent: Yes
  - Check Mode: Yes
  - Diff Mode: Yes

## Variables
  - None

## Examples

### Install and configure nimbus cluster probe on two nodes

  ```bash
  TARGETS=200001,200002 \
    ansible-playbook -i $(which --skip-alias ht) \
      nimbus_cluster_probe.yml
```
