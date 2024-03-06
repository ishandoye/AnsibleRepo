# SAN storage checker

## Task Summary
 - Initialize variables to hold data
 - Collect data from servers via the following raxfacts modules
   - setup
   - storage
   - cluster
 - Extract various values from the data returned from raxfacts
   - **NB This will generate a LOT of output to screen if you have many servers and/or many paths to storage**
   - Red Hat Cluster and Oracle detection
   - Red Hat Cluster members if appropriate (**NB** Oracle RAC members are **not** determined)
   - Powerpath and/or multipathd version
   - Dead subpaths (any path where `state` is not `alive`)
   - Subpaths with errors (any path where `error` count is greater than `0`)
   - Powerpath devices where the load-balancing/failover policy is not one of `CLAROpt` or `SymmOpt`
   - Any subpaths that are directly mounted as filesystems
   - Any subpaths that are directly used as LVM PVs (indicating the LVM filter is incorrect)
   - All pseudo-devices that are correctly used (mounted directly, used as LVM PVs, used in cluster config)
   - Any pseudo-devices that are not used either as LVM PVs or directly mounted as filesystems (so are apparently unused)
   - **NB** Pseudo-devices used by Oracle are **NOT** detected (so will always be listed as unused). Correct usage of SAN storage will need to be determined manually by DBAs
 - Store final results
 - Output results to stdout (if requested)
 - Output results to CSV file

## Contributors
  - Author:          Paul Whitaker <paul.whitaker@rackspace.co.uk>
  - Maintainer(s):   Paul Whitaker

## Supporting Docs
  - N/A

## Assumptions

## Precautions
  - Output CSV file will be overwritten (default name is storage_check.csv)

## Rollback
  - None - no changes are made on target servers

## Requirements
  - **Ansible**: Tested with 2.8.5
  - **Hammertime**: Tested with 5.1.0 (any version capable of generating Ansible inventory should work)
  - **Python**: `jmespath` module is required due to the use of `json_query` Ansible filter
  - **root** access to target servers

## Compatibility
  - Rackspace platform: Dedicated
  - OS: EL 6/7/8
  - Idempotent: yes
  - Check Mode: no

## Variables
  - `report_filename` - the file that the CSV report will be written to
    - type: string
    - default: ./storage_check.csv
  - `screen_output` - whether to report results to `stdout` as well as to file
    - type: boolean
    - default: false
    - required: false

## Examples
  Run with default values (no results to `stdout`, CSV results to `./storage_check.csv`)
  ```bash
  TARGETS=200001,200002 ANSIBLE_LIBRARY=library ANSIBLE_MODULE_UTILS=module_utils \
    ansible-playbook -i $(which --skip-alias ht) storage_check.yml
  ```

  Enable output to `stdout`, CSV results to `/tmp/my_results.csv`
  ```bash
  TARGETS=200001,200002 ANSIBLE_LIBRARY=library ANSIBLE_MODULE_UTILS=module_utils \
    ansible-playbook -i $(which --skip-alias ht) -e 'screen_output=true' \
    -e 'report_filename=/tmp/my_results.csv' storage_check.yml
  ```
