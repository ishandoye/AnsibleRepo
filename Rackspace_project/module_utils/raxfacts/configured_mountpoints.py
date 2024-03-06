import os
import re
from socket import gaierror, gethostbyname
import sys

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector

if sys.version_info[0] == 2:
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser

NFS_DEV_RE = re.compile(r"(^)([^/]+)(:/.*)$")
SMB_DEV_RE = re.compile(r"(//)([^/]+)(/.*)$")
NET_FS = {"cifs": SMB_DEV_RE, "smbfs": SMB_DEV_RE, "nfs": NFS_DEV_RE, "nfs4": NFS_DEV_RE}


class BaseMount(object):
    valid_parent_devs = []
    nodev_filesystems = []

    def __init__(self, module):
        self.module = module
        self.entries = list()
        self.debug = list()
        self.valid_parent_devs = list()
        self.record_block_devs("/sys/block", "/dev")
        self.record_block_devs("/dev/mapper")
        self.record_nodev_filesystems()
        self.blkid = module.get_bin_path("blkid")

    def record_block_devs(self, src_path, rec_path=None):
        """Gets the paths of known block/devicemapper devices"""
        rec_path = rec_path or src_path
        if os.path.isdir(src_path):
            self.valid_parent_devs.extend([os.path.join(rec_path, x) for x in os.listdir(src_path)])

    def record_nodev_filesystems(self):
        """Gets the list of filesystem types the kernel knows don't have a block device attached"""
        with open("/proc/filesystems", "r") as fs:
            self.nodev_filesystems.extend([l.split()[1] for l in fs if l.startswith("nodev")])

    def run_command(self, cmd, allowed_rc=None):
        allowed_rc = allowed_rc if allowed_rc else [0]
        if not isinstance(allowed_rc, (list, tuple)):
            allowed_rc = [allowed_rc]
        (rc, stdout, stderr) = self.module.run_command(cmd)
        if rc not in allowed_rc:
            self.debug.append(
                "Error running '{0}'. rc: '{1}', stderr: '{2}'".format(str(cmd), str(rc), stderr)
            )
        return (bool(rc), stdout)

    def get_results(self):
        return [e.to_dict() for e in self.entries]

    class Entry(object):
        def __init__(self, bm, what, where, vfs_type, options):
            self.bm = bm
            self.what = what
            self.where = where
            self.vfs_type = vfs_type
            self.options = options
            if "bind" in options or os.path.isfile(what):
                self.canonical_dev = os.path.realpath(os.path.normpath(what))
            elif vfs_type in NET_FS:
                self.canonical_dev = self.resolve_net_device(what)
            elif vfs_type in bm.nodev_filesystems:
                self.canonical_dev = "nodev"
            else:
                self.canonical_dev = self.canonicalize_device(os.path.normpath(what))

        def canonicalize_device(self, dev_path):
            """Turns the device reference into a path based on the block devices
            listed under /sys/block or device mapper paths under /dev/mapper
            The original reference from a config file may be one of something like:
            - LABEL=<value>
            - UUID=<value>
            - /dev/vgname/lvname
            - /dev/disk/by-id/<name>
            """
            if any([d for d in self.bm.valid_parent_devs if dev_path.startswith(d)]):
                # Reference already matches a known device path
                return dev_path
            # Use blkid to search for the UUID of the device
            cmd = [self.bm.blkid, "-s", "UUID", "-o", "value"]
            if "=" in dev_path:
                cmd.append("-t")
            cmd.append(dev_path)
            (err, stdout) = self.bm.run_command(cmd, [0, 2])
            if err or not stdout:
                # blkid couldn't find the device
                return "UNKNOWN"
            cmd = [self.bm.blkid, "-t", "UUID={0}".format(stdout.strip()), "-o", "device", "-l"]
            (err, stdout) = self.bm.run_command(cmd)
            if err or not stdout:
                return dev_path
            return stdout.strip()

        def resolve_net_device(self, dev_path):
            """Resolve a network device path to the IP address"""
            dev_re = NET_FS.get(self.vfs_type)
            if not dev_re:
                return dev_path
            mtch = dev_re.match(dev_path)
            if not mtch:
                return dev_path
            try:
                ipaddr = gethostbyname(mtch.group(2))
            except gaierror:
                return dev_path
            return "{0}{1}{2}".format(mtch.group(1), ipaddr, mtch.group(3))

        def to_dict(self):
            return {
                "what": self.what,
                "where": self.where,
                "vfs_type": self.vfs_type,
                "mount_options": self.options,
                "canonical_dev": self.canonical_dev,
            }


class Fstab(BaseMount):
    class Entry(BaseMount.Entry):
        def __init__(
            self, bm, line_num, fs_spec, fs_file, fs_vfstype, fs_mntops, fs_freq, fs_passno
        ):
            super(Fstab.Entry, self).__init__(bm, fs_spec, fs_file, fs_vfstype, fs_mntops)
            self.fs_freq = fs_freq
            self.fs_passno = fs_passno
            self.line_num = line_num

        def to_dict(self):
            rslt = super(Fstab.Entry, self).to_dict()
            rslt.update(
                {
                    "dump_freq": self.fs_freq,
                    "fsck_passno": self.fs_passno,
                    "source": "/etc/fstab",
                    "line_number": self.line_num,
                }
            )
            return rslt

    class BadLine(object):
        def __init__(self, line, line_num):
            self.line = line
            self.line_num = line_num

        def to_dict(self):
            return {
                "source": "/etc/fstab",
                "error": True,
                "raw_line": self.line,
                "line_number": self.line_num,
            }

    def __init__(self, module):
        super(Fstab, self).__init__(module)
        self.read_fstab()

    def read_fstab(self):
        with open("/etc/fstab", "r") as fstab:
            for line_num, line in enumerate(fstab, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                fstab_elements = line.split()
                # The last two fields on an fstab entry are optional,
                # and default to 0. This will add one or two '0's
                # if they are missing
                if len(fstab_elements) == 4:
                    fstab_elements.append("0")
                if len(fstab_elements) == 5:
                    fstab_elements.append("0")

                if len(fstab_elements) == 6:
                    self.entries.append(Fstab.Entry(self, line_num, *fstab_elements))
                else:
                    self.entries.append(Fstab.BadLine(line, line_num))


class SystemdMounts(Fstab):
    class Entry(BaseMount.Entry):
        def __init__(self, bm, src_file, what, where, fstype, options):
            super(SystemdMounts.Entry, self).__init__(bm, what, where, fstype, options)
            self.src_file = src_file

        def to_dict(self):
            rslt = super(SystemdMounts.Entry, self).to_dict()
            rslt["source"] = self.src_file
            return rslt

    def __init__(self, module, systemctl):
        super(SystemdMounts, self).__init__(module)
        self.systemctl = systemctl
        self.read_systemd_mounts()

    def read_systemd_mounts(self):
        # Look for any non-generated systemd mount units
        if not self.systemctl:
            return
        cmd = [
            self.systemctl,
            "list-unit-files",
            "--type",
            "mount",
            "--state",
            "enabled",
            "--no-legend",
        ]
        (err, stdout) = self.run_command(cmd)
        if err:
            return
        for mnt in [m.split(None, 1)[0] for m in stdout.splitlines()]:
            # We have to read the contents of the actual .mount config file
            # as `systemctl show` will only show running values, which may be
            # different
            cmd = [self.systemctl, "show", mnt, "--property=FragmentPath"]
            (err, stdout) = self.run_command(cmd)
            if err or "=" not in stdout:
                self.debug.append("No = found in {0}".format(stdout))
                continue
            srcfile = stdout.strip().split("=", 1)[1]
            if not os.path.isfile(srcfile):
                self.debug.append("{0} is not a file".format(srcfile))
                continue
            mntcfg = RawConfigParser()
            mntcfg.read(srcfile)
            optdict = dict(mntcfg.items("Mount"))
            self.entries.append(
                SystemdMounts.Entry(
                    self,
                    srcfile,
                    *[optdict.get(x, "") for x in ["what", "where", "type", "options"]]
                ),
            )


class ConfiguredMountpointsCollector(BaseRaxFactsCollector):

    name = "configured_mountpoints"
    timeout = 60

    def collect(self):
        systemctl = self.module.get_bin_path("systemctl", opt_dirs=["/usr/bin", "/usr/local/bin"])
        if systemctl:
            cfgd_mpts = SystemdMounts(self.module, systemctl)
        else:
            cfgd_mpts = Fstab(self.module)
        self.debug.extend(cfgd_mpts.debug)
        return cfgd_mpts.get_results()
