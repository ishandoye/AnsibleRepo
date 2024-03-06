import os
import re

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class MPDev(object):
    """Base class for multipath devices"""
    BLOCK_BASE = "/sys/class/block"

    def __init__(self, devname):
        self.controller = "not set"
        self.name = devname
        self.array_id = None
        self.array_description = None
        self.lun_id = None
        self.lun_description = None
        self.platform = None
        self.wwn = None
        self.subgroups = []
        self.subgroup_count = 0
        self.subpaths = []
        self.subpath_count = 0
        self.size = None
        self.sector_size = 512

    def read_lun_size(self, dev_name):
        # /sys/class/block/<dev_name>/size - contains device size in sectors
        spath = os.path.join(self.BLOCK_BASE, dev_name, "size")
        try:
            with open(spath, "r") as f:
                size = int(f.read().strip())
            # SSD storage might have a different sector size to the 512B default
            # so read what the storage tells us
            # /sys/class/block/<dev_name>/queue/hw_sector_size
            hpath = os.path.join(
                self.BLOCK_BASE, dev_name, "queue", "hw_sector_size")
            try:
                with open(hpath, "r") as f:
                    self.sector_size = int(f.read().strip())
            except Exception:
                self.sector_size = 512
            self.size = size * self.sector_size
        except Exception:
            # If the device size file doesn't exist, is non-readable or doesn't
            # contain an int, then we can't work out the device size
            pass

    def todict(self):
        self.subpath_count = len(self.subpaths)
        self.subgroup_count = len(self.subgroups)
        return self.__dict__


class PowerPathDev(MPDev):
    """Class to hold powerpath device info"""
    PLATFORMS = ["Symmetrix", "VNX", "Unity", "CLARiiON"]
    DRIVERS = ["lpfc", "bfa", "qla2xxx"]

    def __init__(self, devname):
        super(PowerPathDev, self).__init__(devname)
        self.controller = "powerpath"
        self.subgroups.append({
            'id': 0,
            'state': None,
            'policy': None,
            'priority': None
        })
        self.subgroup_count = 1
        self.read_lun_size(devname)

    def add_data(self, line):
        vals = [x for x in line.split(' ') if x]
        if len(vals) > 8:
            if any(x in vals for x in PowerPathDev.DRIVERS):
                self.subpaths.append({
                    'subgroup': 0,
                    'name': vals[2],
                    'mode': vals[5],
                    'path_state': vals[6],
                    'dm_state': vals[6],
                    'errors': int(vals[8])
                })
        elif '=' in line:
            key, value = line.split('=', 1)
            desc = None
            if ' [' in value:
                value, desc = value.split(' [', 1)
                desc = desc.rstrip(']')
            if 'Logical' in vals:
                self.lun_id = value
                if len(value) > 12:
                    self.wwn = value
                if desc:
                    self.lun_description = desc
            if 'Device' in vals:
                self.wwn = value
                if desc:
                    self.lun_description = desc
            if any(x in key for x in PowerPathDev.PLATFORMS):
                self.platform = key
                self.array_id = value
                if desc:
                    self.array_description = desc
            if 'state' in vals[0]:
                self.subgroups[0]['state'] = vals[0].split('=')[1].rstrip(';')
            if 'policy' in vals[1]:
                self.subgroups[0]['policy'] = vals[1].split('=')[1].rstrip(';')


class MultipathdDev(MPDev):
    """Class to hold multipathd controlled devices"""
    DEV_PAT = re.compile(
        r'^(?:([^(]+)\s+\()?([a-f0-9]{12,})\)?\s+(dm-\d+)\s+([^,]+?)\s*,([^,]+)'
    )
    SUBGROUP_PAT = re.compile(
        r"policy='([^']+)'\s+prio=(\w+)\s+status=(\w+)"
    )
    SUBPATH_PAT = re.compile(
        r"(?:\d+:){3}\d+\s+(\w+)\s+\d+:\d+\s+(\w+)\s+(\w+)\s+(\w+)$"
    )

    def __init__(self, alias, wwn, devname, vendor, product):
        if not alias:
            alias = wwn
        super(MultipathdDev, self).__init__(alias)
        self.controller = "multipathd"
        self.platform = vendor
        self.array_id = product
        self.wwn = wwn
        self.lun_id = devname
        self.read_lun_size(devname)

    def add_data(self, line):
        sg_match = self.SUBGROUP_PAT.search(line)
        sp_match = self.SUBPATH_PAT.search(line)
        if sg_match:
            self.subgroup_count = len(self.subgroups)
            self.subgroups.append({
                'id': self.subgroup_count,
                'policy': sg_match.group(1),
                'priority': sg_match.group(2),
                'state': sg_match.group(3),
            })
        elif sp_match:
            self.subpaths.append({
                'subgroup': self.subgroup_count,
                'name': sp_match.group(1),
                'mode': sp_match.group(4),
                'dm_state': sp_match.group(2),
                'path_state': sp_match.group(3),
                'errors': None
            })


class StorageFactsCollector(BaseRaxFactsCollector):

    name = "san_storage"
    aliases = set(["storage"])

    def __init__(self, *args, **kwargs):
        super(StorageFactsCollector, self).__init__(*args, **kwargs)
        self.facts = {
            'powermt_version': None,
            'powerpath_running': False,
            'multipath_version': None,
            'multipath_running': None,
            'multipath_devices': [],
        }

    def parse_powermt_output(self, data):
        ppdevs = []
        ppdev = None
        for line in data.splitlines():
            line = line.strip()
            if line.startswith('Pseudo'):
                if ppdev:
                    ppdevs.append(ppdev.todict())
                ppdev = PowerPathDev(line.split('=')[1])
            elif (ppdev and not line.startswith(('=', '#', '-'))):
                ppdev.add_data(line)
        if ppdev:
            ppdevs.append(ppdev.todict())
        return ppdevs

    def parse_multipath_output(self, data):
        mpdevs = []
        mpdev = None
        for line in data.splitlines():
            line = line.strip()
            match = MultipathdDev.DEV_PAT.match(line)
            if match:
                if mpdev:
                    mpdevs.append(mpdev.todict())
                mpdev = MultipathdDev(*match.groups())
            else:
                mpdev.add_data(line)
        if mpdev:
            mpdevs.append(mpdev.todict())
        return mpdevs

    def collect_powerpath_data(self, powermt_path):
        (rc, powermt_ver, stderr) = self.module.run_command(
            [powermt_path, 'version']
        )
        if rc == 0:
            powermt_ver = powermt_ver.rstrip()
            match = re.search(r'Version (.*)$', powermt_ver)
            if match:
                powermt_ver = match.group(1)
            self.facts['powermt_version'] = powermt_ver
        else:
            self.facts['powermt_version'] = 'Unknown'
            self.debug.append({'powermt_version': stderr})

        (rc, powermt_out, stderr) = self.module.run_command(
            [powermt_path, 'display', 'dev=all']
        )
        if rc == 0:
            self.facts['powerpath_running'] = True
            self.facts['multipath_devices'].extend(
                self.parse_powermt_output(powermt_out)
            )
        else:
            self.facts['powerpath_running'] = False
            self.debug.append({'powerpath_devices': stderr})

    def collect_multipathd_data(self, multipath_path):
        rpm_cmd = self.module.get_bin_path('rpm')
        dpkg_cmd = self.module.get_bin_path('dpkg-query')
        if rpm_cmd:
            (rc, package, stderr) = self.module.run_command(
                [rpm_cmd, '-q', 'device-mapper-multipath']
            )
        elif dpkg_cmd:
            (rc, package, stderr) = self.module.run_command(
                [dpkg_cmd, '-W', r"-f='${binary:Package}-${Version}'",
                 'multipath-tools']
            )
        else:
            (rc, package, stderr) = (-1, 'unknown', "Didn't find rpm or dpkg")
        if rc == 0:
            self.facts['multipath_version'] = package.rstrip()
        else:
            self.debug.append({'multipath_version': stderr})

        (rc, multipath_out, stderr) = self.module.run_command(
            [multipath_path, '-ll']
        )
        if rc == 0:
            self.facts['multipath_devices'].extend(
                self.parse_multipath_output(multipath_out)
            )
        else:
            self.debug.append({'multipathd_devices': stderr})

    def multipath_running(self):
        if self.facts['multipath_running'] is None:
            service_cmd = self.module.get_bin_path('service')
            (rc, _, _) = self.module.run_command(
                [service_cmd, 'multipathd', 'status']
            )
            self.facts['multipath_running'] = not bool(rc)
        return self.facts['multipath_running']

    def collect(self):
        powermt_path = self.module.get_bin_path('powermt')
        if powermt_path:
            self.collect_powerpath_data(powermt_path)

        if self.multipath_running():
            multipath_path = self.module.get_bin_path('multipath')
            if not multipath_path:
                self.debug.append({'multipath_binary': 'not found'})
            else:
                self.collect_multipathd_data(multipath_path)

        # If there is no sign of powermt, HBAs or any multipath devices
        # return None instead of a set of empty info
        if (not powermt_path and not os.path.isdir('/sys/class/fc_host') and
            not self.facts['multipath_devices']):
            return None

        # Check for /boot/.rackspace/rbsemcmpio
        self.facts["rbsemcmpio_cookie_found"] = os.path.exists("/boot/.rackspace/rbsemcmpio")
        return self.facts
