# Cohesity Agent

Playbook to install/uninstall Cohesity Agent

## Tasks summary

For each device:
  - validates the OS is supported
  - validates the requested action is one of (`install`, `uninstall`)
  - check if cohesity agent is already installed
  - stop immediately if cohesity agent is in the desired state
  - for install/reinstall
    - download the installer to the device
    - unpack the installer to disk
  - for uninstall/reinstall, if agent is installed
    - uninstall cohesity agent
    - report version that was uninstalled
  - for install/reinstall
    - run the downloaded installer
    - report the installed version

## Contributors
  - Author: Paul Whitaker
  - Maintainers: GTS Linux Automation Engineers

## Requirements:
  - Ansible version >= 2.11
    - python `lxml` module is required on the ansible controller (i.e. the device
      running the role, not the target)
  - Hammertime >= 6.4.0
  - This playbook requires **root** access

## Compatibility
  - Rackspace platform: Anything hammertime can connect to
  - OS: CentOS 6/7, RHEL 6/7/8/9, AlmaLinux/Rocky Linux 8/9, Ubuntu 18.04/20.04/22.04
  - Idempotent: Yes (except `force_reinstall`)
  - Check Mode - No

## Variables

  - `role_action`: One of `install`, `uninstall`
    - default: `install`
  - `force_reinstall`: Force a reinstall of cohesity agent (uninstalls then
    reinstalls cohesity agent) if set to a value that evaluates as `true`
    - default: `false`
  - `debug_script`: Pass the `-d` debug flag to the cohesity installer script if
    set to a value that evaluates as `true`
    - default: `false`

## Support Docs
 - https://one.rackspace.com/display/MBU/Linux+File+System+Install+Guide+Cohesity

## Examples

### Install (default action)

```bash
$ TARGETS=200001,200002 ansible-playbook -i $(which ht) cohesity_agent.yml
```

### Uninstall

```bash
$ TARGETS=200001,200002 ansible-playbook -i $(which ht) cohesity_agent.yml \
    -e role_action=uninstall
```

### Force reinstall

```bash
$ TARGETS=200001,200002 ansible-playbook -i $(which ht) cohesity_agent.yml \
    -e force_reinstall=1
```
