# nimbus_proc_q

## Description
  - Sets nimbus proc q monitor to proper number (# of CPU Cores * 4), enables/disables CPU usage warning and error and allows for the %CPU usage for those monitors to be set. Uses vars_prompts, but can be skipped with --extra-vars

## Contributors       
  - Author: Ryan Francis <ryan.francis@rackspace.com>
  - Maintainer(s) Ryan Francis

## Assumptions     
  - Nimbus cdm probe is installed with its config file at /opt/nimsoft/probes/system/cdm/cdm.cfg or /opt/nimsoft/probes/system/cdm/cdm.cfg
                 
## Precautions
  - Operation carries little risk as we are just editing the nimbus config

## Requires root   
  - Yes

## Rollback
  - Copy timestamped backup from /home/rack/<ticket> back to /opt/nimsoft/probes/system/cdm/cdm.cfg
                 

## Supporting Docs 

## Tasks summary   
  - Takes a backup of the cdm probe config file, makes its changes using sed and restarts the nimbus service    
                 

## Compatibility   
  - Ansible version: 2.4, 2.5.2 (Tested)
  - Rackspace platform: Cloud / Dedicated / All
  - OS: RHEL 6,7/ CentOS 6,7/ Ubuntu 14.04,16.04

## Idempotent      
  - No
              

## Check Mode      
  - No    

## Requirements
  - This playbook uses the nimbus_config module so it is required that this playbook is run from the playbooks git repo directory. Additionally, you will need to add the playbooks repo's path to your `~/.ansible.cifg` under [defaults]: `library = /home/ryan/Documents/git/playbooks/library`. The playbooks will not work otherwise.
  - Requirements for execution of playbook (python modules/versions, filesystem biaries, etc.):
  - Local: Ansible 2.4+, hammertime
  - Remote: Nimbus installation, python2.7, sudo access for rack user
                 

## Variables:       
  - Playbook takes vars prompts. 

        name: ticket_num
        purpose: Prompt for the backup directory 
        permitted values: any
        type: string
        default: "nimbus_proc_q"
         
        name: cpu_warning_prompt
        purpose: Ask to enable CPU usage WARNING. If not set to Y/y, cpu usage warnings will be disabled.
        permitted values: Y/N
        type: string
        default: "N"
         
        name: cpu_warning_threshold
        purpose: Set % of total cpu usage that will trigger a warning alert. Value will be ignored if cpu_warning_prompt is set to N/n.
        permitted values: Any integer 1-100
        type: string
        default: 90                 
         
        name: cpu_error_prompt
        purpose: Ask to enable CPU usage ERROR.  If not set to Y/y, cpu usage warnings will be disabled.
        permitted values: Y/N
        type: string
        default: "N"
         
        name: cpu_error_threshold
        purpose: Set % of total cpu usage that will trigger an error alert. Value will be ignored if cpu_error_prompt is set to N/n.
        permitted values: Any integer 1-100
        type: string
        default: 95

## Example 
  `# TARGETS=11111,22222 ansible-playbook -i $(which ht) nimbus_proc_q.yml --extra-vars='ticket_num=123456-98765 cpu_warning_prompt=y cpu_warnining_threshold=95 cpu_error_prompt=y cpu_error_threshold=99'`                 
