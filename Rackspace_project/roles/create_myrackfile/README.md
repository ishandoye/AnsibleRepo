# create_myrackfile

Create a MyRackFile in a customers MyRackspace Portal's File Manager.

## Task Summary
  - Creates file in rs_server's MyRackspace Portal File Manager
  - Checks the status of the previous task

## Contributors
  - Author(s): GTS Linux Automation Engineers <GTS-Linux-Automation-Engineers@rackspace.com>
  - Maintainer(s): GTS Linux Automation Engineers

## Supporting Docs
  - None

## Assumptions
  - A Core Device or Core Account is required
  - If a Core Device AND Core Account is provided, the Core Device will be used to set the permissions

## Precautions
  - Device Permissions - Only contacts with direct device permissions will have access to the file (this excludes Account Admins)
  - Account Account Permissions - If only an account is provided, the MyRackFile will be created with no permissions. 
  - Verify the correct recipients once the file has been uploaded

## Rollback
  - Manual

## Requirements
  - **Ansible**: >= 2.7.0

## Compatibility
  - Rackspace platform: Dedicated
  - Idempotent: Yes
  - Check Mode: Yes

## Variables
  - `rs_server` - Device used to set permissions of the created file
    - permitted values: Any valid Core server number
    - type: string
    - default: None
    - required: no

  - `account_number` - Account used to set permissions of the created file
    - permitted values: Any valid Core account number
    - type: string
    - default: None
    - required: no

  - `myrackfile_name` - Group name to be created
    - permitted values: any
    - type: string
    - default: "YYYY-MM-DDThh:mm:ss".txt (ISO 8601.txt)
    - required: No

  - `myrackfile_content` - The directory which requires access by the sftp user
    - permitted values: any
    - type: string
    - default: None
    - required: Yes

## Example

### Upload a file called user_details.txt with the permissions of device 200002

  ```bash
      ansible-playbook \
      create_myrackfile.yml \
      -e rs_server=200002 \
      -e myrackfile_name=user_details.txt \
      -e myrackfile_content="Username: luke\nPassword: password\n"
```

### Upload a file called user_details.txt with no permissions


  ```bash
      ansible-playbook \
      create_myrackfile.yml \
      -e account_number=000000 \
      -e myrackfile_name=user_details.txt \
      -e myrackfile_content="Username: luke\nPassword: password\n"
```
