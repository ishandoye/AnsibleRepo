Raxfacts
=========

In a nutshell - raxfacts is an existing project developed mainly by the [GTSLAE](https://one.rackspace.com/display/support/GTS+Linux+Automation+Engineers) team, predominantly used in Stepladder.
Under the hood, it's an Ansible module - but in Stepladder it's wrapped in an API and we rely on it rather heavily. As a consequence, it's written to be very robust, and has been battle tested a fair bit. The differences between distributions are abstracted away as much as possible, as are the nuances of distribution versions. For example, as a rule, we avoid relying on parsing command line tools output as much as possible, and rely on the kernel interfaces etc. where applicable.

Using the aforementioned API, you can also get raxfacts via hammertime, using it's --raxfacts argument.
There is also a Python library which doubles up as a CLI client.
So whether you're writing shell scripts, playbooks or Python code (or any other language that can talk REST API and parse JSON..), you can (should!) use raxfacts.

It's main aim is to be the de-facto standard way of obtaining information about a remote system.
It's a living project, and we add new facts to it as and when we need them.
Originally each fact was its own plugin, and there was an action plugin that stitched them together, but for performance reasons, all facts are gathered in the same module - hence in the same connection.
So what could be numerous round-trips just to establish what's what and the ifs-and-buts, that's now cut down to one.

Presently available facts
------------

* `antivirus` - Provides configurations and status of AV (currently only Sophos).
* `listening_ports` - This will give you a list of dictionaries with information (host, port, protocol and PID) about ports that are in a LISTEN state on the server.
* `setup` - This is just a proxy for Ansible's standard facts. It can be used in combination with `gather_facts: False` to avoid an extra round-trip to collect the setup facts.
* `running_processes` - Returns a dictionary where the outer keys are the PID of a running process. Their values contains the executable, the process name, PID, command line, owner (UID) and RSS.
* `services` - A list of dictionaries describing services, values being source (upstart/sysv/systemd), state, name, and goal (parse of initctl's goal/state)
* `plesk` - If plesk is installed - returns a dictionary containing its numerical version, full version string, installed (boolean) and php_versions (list of dictionaries containing information on the PHP versions supported by Plesk)
* `webservers` - This gives you a dictionary containing two keys `apache` and `nginx`. These keys are set to null if that webserver isn't installed, or if it's got an unparseable config (configtest fails). These keys contains a swathe of information about the webservers, including virtualhosts, documentroots, ssl certificate information, pid file location, access- and error-log locations, startservers/maxclients, loaded modules, interfaces listened on, aliases etc.
* `users_groups` - Returns two keys, `users` and `groups`. These are lists of dictionaries containing all available fields extracted from /etc/passwd and /etc/group (uid, gid, home, shell ...)
* `packages` - This returns a list of all packages installed on the system. As with everything else, it's distro agnostic and handles both apt and yum. A list of dicts describes the packages with information such as package name, source, epoch, version, arch and release.
* `mysql` - This returns all information about all users (grants) on the server, all global variables and all global status. It also returns datadir size and whether replications is set up.
* `cluster` - This returns information about a cluster that the device(s) is part of. Null if no cluster was detected. The information includes services (owning device, state, name), and cluster peers and their statuses.
* `auter` - Checks to see whether project Auter is set up on the server. Returns whether it's `running`, its `version`, whether it's `enabled` or not and when it was `last_run`.
* `repositories` - This inspect all package manager repositories set up on a serve. Supports both yum repos and apt PPAs. Returns URIs, names, architectures and the file they're defined in.
* `sar` - If `sar` is installed and running on the system, this will return basic load information: `cpu_max|avg|min_pct` and `mem_max|avg|min_pct`. This data is derived from all available SAR files.
* `hardware` - Returns detailed hardware related information regarding bios, chassis, controllers, fc_hba, fc_ports, logical_drives, nics, physical_drives, power_supplies, and vendor_tools.
* `nimbus` - Returns information regarding nimbus installation and configuration.
* `patching` - Returns information regarding patching status and any available updates.
* `storage` -  Returns information about PowerPath and multipath SAN storage devices.
* `docker` -  Returns information about Docker info, containers and networks
* `kubernetes` -  Returns information about Kubernetes version, namespaces, pods and services

Module Variables
--------------
* `facts`: List of raxfacts modules to run.
* `list_modules`: Return a list of available raxfacts modules. (default: False)
* `namespace`: String to namespace top level facts keys with. (default: '')
* `debug`: Returns a debug key with any exception/debug information that has been appended to it during a modules execution. (default: False)

Example Playbook Usage:
```
---
- hosts: all
  become: true
  gather_facts: false
  tasks:
    - name: Gather patching facts for servers
      raxfacts:
        facts:
          - patching

	- debug: var=patching
```
Note: While the module does not explicitly require it, most raxfacts modules assume the module is running with `become: true`.

Developing a new raxfacts module
------------
To create a new raxfacts module:

1. Create a new class with the `BaseRaxFactsCollector` as the parent.  Your new collector class is responsible for implementing a `collect` method which should return a dictionary of facts. Here is an example:

```
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector

class ExampleFactsCollector(BaseRaxFactsCollector):

	name = 'example'

	def collect(self):
		facts = {
			'fake_fact': True,
		}
		return facts
```
2. Register your new facts collector class in the `collector_classes` list in [collectors.py](../module_utils/raxfacts/collectors.py)

The main raxfacts interface will call your classes `collect` method inside a try/except block. Exceptions caught here just set your modules key in the returned dictionary to None and appends the exception output to a `debug` list. Just set `debug: True` when testing your module to see this output.

Contributing Best Practices
------------
* For maximum compatibility - facts may NOT depend on any non-standard libraries.
* Distribution differences should be abstracted away as much as possible. If something applies to RHEL, but not to Ubuntu, include the keys anyway, but set them to None. The returned structure should be identical no matter the target distribution/version. Set keys to None if necessary.
* Leverage the Ansible module api as much as possible. For instance a lot of I/O and filesytem interfacing is provided there.


Dependencies
------------

None


Author Information
------------------

GTS Linux Engineers <gts-linux-engineers@rackspace.com>

