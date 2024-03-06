# mysql_upgrade

Upgrade MySQL-family database software on Red Hat Enterprise Linux-family servers.

## Task Summary
  - Verify if the given server belongs to RedHat family
  - Creates a working directory under `/home/rack` named as a ticket number or a timestamp.
  - Identify the database vendor (MySQL, MariaDB or Percona).
  - Backup yum configuration and remove MySQL exclusions if there are any.
  - Determine datadir, mysql version and tmpdir variables.
  - Verifies whether installed MySQL is the latest or not.
  - Backup mysql datadir using either rsync or holland.
  - Upload `upgrade_mysql_config.py` to server.
  - Back up existing MySQL configuration file (`/etc/my.cnf`).
  - Create new MySQL configuration file using `upgrade_mysql_config.py` when not using MariaDB.
  - Configure MySQL Community or MariaDB repositories; uses Percona percona-release command for configuring Percona repositories.
  - Remove old MySQL packages.
  - Install new MySQL packages.
  - Run `mysql_upgrade`.
  - Restore `yum.conf` file.
  - Display optional rollback information to users.

## Contributors
  - Authors: Cristian Banciu and GTS Linux Automation Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automation Engineers

## Supporting Docs
  - https://one.rackspace.com/display/Linux/MySQL+Upgrades

## Assumptions
  - MySQL service is installed and running. 
  - Holland packages are installed if backup method `holland` is chosen.
  - If MySQL version to be upgraded is not specified default version of MySQL 5.6 will be selected.
  - Assumes latest MySQL version is 8.0 or MariaDB 10.8.
  - The role performs step upgrades when upgrading between multiple MySQL versions i.e. MySQL 5.5 to 8.0.
  - Step upgrades are not required for MariaDB.

## Precautions
  - Old MySQL packages will be removed and new specified packages will be installed. 
  - This role backs up MySQL's data before upgrading. Manual verification of backups is also recommended.
  - It does NOT allow upgrade from one vendor to another, for example MySQL to Percona or MySQL to MariaDB.
  - Ensure that there is enough disk space available for data backup.
  - Do NOT run this on RHCS cluster devices.
  - It does not detect whether database replication is configured. Ensure you have verified whether mysql replication is setup.

## Rollback
  - Manual (it provides the original mysql packages that were removed as ansible output.)

## Requirements
  - **Ansible**: >= 2.8.0
  - **Hammertime**: >= 3.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Dedicated and Cloud
  - OS: EL7 and EL8; Ubuntu 18.04 and 20.04
  - Idempotent: No
  - Check Mode: No

## Variables
  - `backup_method` - The method to backup mysql datadir before upgrading mysql
    - permitted values: "rsync" or "holland"
    - type: string
    - default: rsync
    - required: No

  - `backup_time` - The time taken to backup mysql data can take long time thus the backup task may take longer than SSH timeout. To keep alive such long running task the backup is performed as asynchronous mode and poll at regular intervals. The default keep alive time is chosen as 2 hours but this can be specified by user using this variable.  
    - permitted values: number (seconds)
    - type: integer
    - default: 7200 seconds
    - required: No

  - `upgrade_version` - The version mysql has to be upgraded to.
    - permitted values: "5.5", "5.6", "5.7", "8.0", "10.1" through "10.8"
    - type: string
    - default: "5.6"
    - required: No

  - `mysql_master` - Specify whether replication is enabled or not, so when `mysql_upgrade` command is executed skip-binlog option is specified for master servers.
    - permitted values: "Yes" or "No"
    - type: string
    - default: "Yes"
    - required: No

  - `my_cnf` - The location of mysql configuration file. 
    - permitted values: A file path
    - type: string
    - default: "/etc/my.cnf"
    - required: No

  - `ticket_no` - The ticket_no will be used to create a folder inside `/home/rack` and files will be backed up in there.
    - permitted values: any valid ticket number
    - type: string
    - default: If no ticket number is provided the timestamp will be used for creating the folder.
    - required: No

## Examples

### Install

```bash
env TARGETS=200001,200002 \
  ansible-playbook -i $(command -v ht) \
  mysql_upgrade.yml -e "upgrade_version=5.7 backup_method=holland ticket_no=180529-00000"
```
