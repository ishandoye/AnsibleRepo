# Tests for cohesity agent role

Three scenarios are provided
 - `default` tests the standard install
 - `uninstall` tests uninstalling when already installed
 - `reinstall` tests forced reinstall when already installed

Molecule files are provided to run with both docker & podman - symlink the one
that you want to `molecule.yml` in the scenario directories

Note that as the tests require a working service manager (systemd, sysvinit,
upstart) on the containers under test, and the EL7 only supports cgroups v1, if
your host device is running cgroups v2 you will need to add
`systemd.unified_cgroup_hierarchy=0` to your kernel boot options in order for
systemd to successfully
