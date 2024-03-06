# Standard Library
import glob
import os
import re
from collections import deque

# Third Party
from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector
from ansible.module_utils.six import iteritems


class HardwareFactsCollector(BaseRaxFactsCollector):

    name = "hardware"
    timeout = 60

    def collect(self):
        hw_facts = BaseHWFacts(self.module).populate()
        vendor = hw_facts["bios"].get("Vendor", "")

        if vendor == "Dell Inc.":
            hw_facts.update(DellFacts(self.module).populate())
        elif vendor == "HP":
            hw_facts.update(HpFacts(self.module).populate())

        return hw_facts


class PciIds(object):
    def __init__(self):
        self.pci_ids = self._parse_pci_ids()

    def _parse_pci_ids(self):
        pci_ids = {}

        for pci_ids_file in ["/usr/share/hwdata/pci.ids", "/usr/share/misc/pci.ids"]:
            pci_data = get_file_content(pci_ids_file)
            if pci_data:
                break

        if pci_data:
            for line in pci_data.splitlines():
                if line.startswith("#"):
                    continue
                if not line.rstrip():
                    continue

                match = re.match("^([0-9a-z]{4})(.+)", line)
                if match:
                    vendor_id = match.group(1)
                    vendor_name = match.group(2).lstrip()
                    pci_ids[vendor_id] = {"vendor": vendor_name, "devices": {}}
                    continue

                match = re.match("^\t([0-9a-z]{4})(.+)", line)
                if match:
                    device_id = match.group(1)
                    device_name = match.group(2)
                    pci_ids[vendor_id]["devices"][device_id] = device_name.lstrip()

        return pci_ids

    def get_pci_info(self, vendor_id, device_id):
        device = ""
        vendor = ""
        try:
            vendor_id = vendor_id.replace("0x", "")
            device_id = device_id.replace("0x", "")
            vendor = self.pci_ids[vendor_id]["vendor"]
            device = self.pci_ids[vendor_id]["devices"][device_id]
        except Exception:
            pass

        return (vendor, device)


class BaseHWFacts(object):
    def __init__(self, module):
        self.module = module
        self.pci_ids = PciIds()

    def get_ethool_data(self, interface):
        driver = {}
        features = {}
        ethtool_path = self.module.get_bin_path("ethtool")
        if ethtool_path:
            args = [ethtool_path, "-i", interface]
            _, stdout, _ = self.module.run_command(args)
            driver = convert_to_dict(stdout)

            args = [ethtool_path, "-k", interface]
            _, stdout, _ = self.module.run_command(args)
            stdout = "\n".join([x.lstrip() for x in stdout.split("\n") if x and not x[0].isupper()])
            features = convert_to_dict(stdout)

        data = {
            "driver": driver,
            "features": features,
        }

        return data

    def get_bios_facts(self):
        bios_dict = {}
        dmidecode_path = self.module.get_bin_path("dmidecode")
        if dmidecode_path:
            _, stdout, _ = self.module.run_command([dmidecode_path, "-qt", "bios"])
            try:
                bios_dict = convert_to_dict(stdout)["BIOS Information"]
                bios_dict.pop("BIOS Language Information", None)
            except Exception:
                pass
        return bios_dict

    def get_fc_host_facts(self):
        def _format_port_name(p_name):
            try:
                p_name = p_name.replace("0x", "")
                p_name = ":".join(p_name[i : i + 2] for i in range(0, len(p_name), 2))
            except Exception:
                pass

            return p_name

        def _get_brocade_host_facts(host_path):
            hba = {
                "fw_version": get_file_content("%s/firmware_version" % host_path, default=""),
                "model": get_file_content("%s/model" % host_path, default=""),
                "driver_version": get_file_content("%s/driver_version" % host_path, default=""),
                "serial_number": get_file_content("%s/serial_number" % host_path, default=""),
            }

            return hba

        def _get_emulex_host_facts(host_path):
            fw_version = get_file_content("%s/fwrev" % host_path, default="")
            driver_version = get_file_content("%s/lpfc_drvr_version" % host_path, default="")

            try:
                fw_version = fw_version.split(",")[0]
                driver_version = driver_version.split()[-1]
            except Exception:
                pass

            hba = {
                "driver_version": driver_version,
                "fw_version": fw_version,
                "model": get_file_content("%s/modelname" % host_path, default=""),
                "serial_number": get_file_content("%s/serialnum" % host_path, default=""),
            }

            return hba

        fc_hosts = []
        if os.path.isdir("/sys/class/fc_host"):
            for path in glob.glob("/sys/class/fc_host/*"):
                host = os.path.basename(path)
                port_name = _format_port_name(get_file_content("%s/port_name" % path))
                port_state = get_file_content("%s/port_state" % path)
                speed = get_file_content("%s/speed" % path)
                hba_device_path = os.path.dirname(os.path.realpath("%s/device" % path))
                bus_info = os.path.basename(hba_device_path)
                vendor_id = get_file_content("%s/vendor" % hba_device_path, default="")
                device_id = get_file_content("%s/device" % hba_device_path, default="")
                vendor, model = self.pci_ids.get_pci_info(vendor_id, device_id)

                if "qloqic" in vendor.lower() or "brocade" in vendor.lower():
                    vendor = "Brocade/Qlogic"

                fc_host = {
                    "bus_info": str(bus_info),
                    "model": model,
                    "port_name": port_name,
                    "port_state": port_state,
                    "speed": speed,
                    "sys_host": host,
                    "vendor": vendor,
                }
                fc_hosts.append(fc_host)

        return fc_hosts

    def get_fc_hba_facts(self, fc_host_facts=None):
        def _get_brocade_host_facts(host_path):
            hba = {
                "fw_version": get_file_content("%s/firmware_version" % host_path, default=""),
                "model": get_file_content("%s/model" % host_path, default=""),
                "driver_version": get_file_content("%s/driver_version" % host_path, default=""),
                "serial_number": get_file_content("%s/serial_number" % host_path, default=""),
            }

            return hba

        def _get_emulex_host_facts(host_path):
            fw_version = get_file_content("%s/fwrev" % host_path, default="")
            driver_version = get_file_content("%s/lpfc_drvr_version" % host_path, default="")

            try:
                fw_version = fw_version.split(",")[0]
                driver_version = driver_version.split()[-1]
            except Exception:
                pass

            hba = {
                "driver_version": driver_version,
                "fw_version": fw_version,
                "model": get_file_content("%s/modelname" % host_path, default=""),
                "serial_number": get_file_content("%s/serialnum" % host_path, default=""),
            }

            return hba

        hbas = []

        if fc_host_facts is None:
            fc_host_facts = self.get_fc_host_facts()
            if fc_host_facts is None:
                return hbas

        hba_pci_slots = set()
        for host in fc_host_facts:
            if host.get("bus_info"):
                hba_pci_slots.add(host["bus_info"].split(".")[0])

        for slot in hba_pci_slots:
            hba_ports = [fc_host for fc_host in fc_host_facts if slot in fc_host["bus_info"]]
            if hba_ports is None:
                continue

            all_ports_offline = True
            for port in hba_ports:
                if port["port_state"] == "Online":
                    all_ports_offline = False
                    break

            hba = {}
            vendor = hba_ports[-1].get("vendor")
            if "Brocade" in vendor:
                hba = _get_brocade_host_facts("/sys/class/scsi_host/" + hba_ports[-1]["sys_host"])
            elif "Emulex" in vendor:
                hba = _get_emulex_host_facts("/sys/class/scsi_host/" + hba_ports[-1]["sys_host"])
            hba.update(
                {
                    "all_ports_offline": all_ports_offline,
                    "bus_info": slot,
                    "fc_host_port_count": len(hba_ports),
                    "vendor": vendor,
                }
            )

            hbas.append(hba)

        return hbas

    def get_nic_facts(self):
        nics = []
        for path in glob.glob("/sys/class/net/*"):
            interface = os.path.basename(path)
            if interface in ["lo", "idrac", "bonding_masters"]:
                continue

            nic = {
                "address": get_file_content("%s/address" % path),
                "duplex": get_file_content("%s/duplex" % path),
                "interface": interface,
                "operstate": get_file_content("%s/operstate" % path),
                "speed": get_file_content("%s/speed" % path),
            }

            vendor_id = get_file_content("%s/device/vendor" % path, default="")
            device_id = get_file_content("%s/device/device" % path, default="")
            vendor, model = self.pci_ids.get_pci_info(vendor_id, device_id)
            for key, value in {"vendor": vendor, "model": model}.items():
                if value:
                    nic[key] = value

            nic.update(self.get_ethool_data(interface))
            nics.append(nic)

        return nics

    def populate(self):
        bios_facts = self.get_bios_facts()
        fc_host_facts = self.get_fc_host_facts()
        fc_hba_facts = self.get_fc_hba_facts(fc_host_facts=fc_host_facts)
        nic_facts = self.get_nic_facts()

        facts = {
            "bios": bios_facts,
            "fc_hbas": fc_hba_facts,
            "fc_ports": fc_host_facts,
            "nics": nic_facts,
        }
        return facts


class HpFacts(BaseHWFacts):
    def __init__(self, module):
        super(HpFacts, self).__init__(module)
        self.ssacli_path = self.module.get_bin_path("ssacli") or self.module.get_bin_path(
            "hpssacli"
        )
        self.hpasmcli_path = self.module.get_bin_path("hpasmcli")
        self.show_server_stdout = None

    def get_show_server_stdout(self):
        if not self.hpasmcli_path:
            return ""
        if self.show_server_stdout is None:
            args = self.hpasmcli_path + ' -s "show server"'
            rc, stdout, _ = self.module.run_command(args)
            self.show_server_stdout = "" if rc else stdout
        return self.show_server_stdout

    def get_chassis_facts(self):
        chassis = {}
        stdout = self.get_show_server_stdout()
        if not stdout:
            return chassis

        chassis = convert_to_dict(stdout)
        for key in list(chassis):
            if isinstance(chassis[key], dict):
                del chassis[key]

        return chassis

    def get_controller_facts(self):
        items = []
        if self.ssacli_path is None:
            return items

        args = [self.ssacli_path, "ctrl", "all", "show", "detail"]
        _, stdout, _ = self.module.run_command(args)
        stdout_dict = convert_to_dict(stdout)
        for key in stdout_dict:
            stdout_dict[key]["Name"] = key
            items.append(stdout_dict[key])

        return items

    def get_logical_drive_facts(self, controller_facts=None):
        items = []

        if self.ssacli_path is None:
            return items

        if controller_facts is None:
            controller_facts = self.get_controller_facts()

        for slot in (x["Slot"] for x in controller_facts if x.get("Slot")):
            args = [self.ssacli_path, "ctrl", "slot=%s" % slot, "ld", "all", "show", "detail"]
            _, stdout, _ = self.module.run_command(args)
            stdout_dict = convert_to_dict(stdout)
            items.extend(list(startswith_in_dict("Logical Drive", stdout_dict)))

        return items

    def get_physical_drive_facts(self, controller_facts=None):
        items = []

        if self.ssacli_path is None:
            return items

        if controller_facts is None:
            controller_facts = self.get_controller_facts()

        for slot in (x["Slot"] for x in controller_facts if x.get("Slot")):
            args = [self.ssacli_path, "ctrl", "slot=%s" % slot, "pd", "all", "show", "detail"]
            _, stdout, _ = self.module.run_command(args)
            stdout_dict = convert_to_dict(stdout)
            items.extend(list(startswith_in_dict("physicaldrive", stdout_dict)))

        return items

    def get_power_supply_facts(self):
        items = []
        if self.hpasmcli_path is None:
            return items

        args = self.hpasmcli_path + ' -s "show powersupply"'
        rc, stdout, _ = self.module.run_command(args, use_unsafe_shell=True)
        if rc != 0:
            return items

        stdout_dict = convert_to_dict(stdout)
        for key in stdout_dict:
            items.append(stdout_dict[key])

        return items

    def get_memory_facts(self):
        items = []
        if not self.hpasmcli_path:
            return items

        args = self.hpasmcli_path + ' -s "show dimm"'
        rc, stdout, _ = self.module.run_command(args)
        if rc != 0:
            return items

        return convert_to_dicts(stdout)

    def get_cpu_facts(self):
        items = []
        stdout = self.get_show_server_stdout()
        if not stdout:
            return items
        for item in [item for item in convert_to_dicts(stdout) if "Processor" in item]:
            items.append(item)
        return items

    def get_vendor_tool_facts(self):
        ssacli_found = bool(self.ssacli_path)
        hpasmcli_found = bool(self.hpasmcli_path)
        hp_health_running = False
        snmp_agents_running = False
        agentx_configured = False

        service_path = self.module.get_bin_path("service")
        if service_path:
            try:
                args = [service_path, "hp-health", "status"]
                rc, _, _ = self.module.run_command(args)
                hp_health_running = not bool(rc)

                args = [service_path, "hp-snmp-agents", "status"]
                rc, _, _ = self.module.run_command(args)
                snmp_agents_running = not bool(rc)
            except Exception:
                pass

        snmpd_conf = get_file_content("/etc/snmp/snmpd.conf")
        if snmpd_conf:
            pattern = re.compile(r"^\s*dlmod cmaX /usr/lib64/libcmaX64.so")
            for line in snmpd_conf.splitlines():
                match = pattern.match(line)
                if match:
                    agentx_configured = True
                    break

        tool_facts = {
            "hpasmcli_found": hpasmcli_found,
            "hp_health_running": hp_health_running,
            "ssacli_found": ssacli_found,
            "snmp_agents_running": snmp_agents_running,
            "snmpd_agentx_configured": agentx_configured,
        }

        return tool_facts

    def populate(self):
        chassis_facts = self.get_chassis_facts()
        controller_facts = self.get_controller_facts()
        logical_drive_facts = self.get_logical_drive_facts(controller_facts=controller_facts)
        physical_drive_facts = self.get_physical_drive_facts(controller_facts=controller_facts)
        power_supply_facts = self.get_power_supply_facts()
        vendor_tool_facts = self.get_vendor_tool_facts()
        memory_facts = self.get_memory_facts()
        cpu_facts = self.get_cpu_facts()

        facts = {
            "controllers": controller_facts,
            "chassis": chassis_facts,
            "cpus": cpu_facts,
            "memory": memory_facts,
            "logical_drives": logical_drive_facts,
            "physical_drives": physical_drive_facts,
            "power_supplies": power_supply_facts,
            "vendor_tools": vendor_tool_facts,
        }

        return facts


class DellFacts(BaseHWFacts):
    def __init__(self, module):
        super(DellFacts, self).__init__(module)
        self.omreport_path = self.module.get_bin_path(
            "omreport", opt_dirs=["/opt/dell/srvadmin/bin", "/opt/dell/srvadmin/sbin"]
        )
        self.omreport_error = False

    def _run_omreport(self, args):
        args = [self.omreport_path] + args
        rc, stdout, stderr = self.module.run_command(args)
        if rc != 0:
            self.omreport_error = True

        return rc, stdout, stderr

    def get_chassis_facts(self):
        chassis = {}
        if self.omreport_path is None:
            return chassis

        args = ["chassis", "info"]
        _, stdout, _ = self._run_omreport(args)
        stdout_items = convert_to_dicts(stdout)
        for item in stdout_items:
            chassis.update(item)

        args = ["chassis", "biossetup"]
        _, stdout, _ = self._run_omreport(args)
        stdout_items = convert_to_dicts(stdout)
        tmp_dict = {}
        for item in stdout_items:
            if "Attribute" in item:
                tmp_dict[item["Attribute"]] = item["Setting"]
            else:
                tmp_dict.update(item)
        items = [tmp_dict]

        if items and "Node Interleaving" in items[0]:
            chassis["Node Interleaving"] = items[0]["Node Interleaving"]

        return chassis

    def get_controller_facts(self):
        items = []
        if self.omreport_path is None:
            return items

        args = ["storage", "controller"]
        _, stdout, _ = self._run_omreport(args)
        stdout_items = convert_to_dicts(stdout)

        for item in stdout_items:
            if "ID" in item:
                items.append(item)
            else:
                items[-1].update(item)

        args = ["storage", "battery"]
        _, stdout, _ = self._run_omreport(args)
        stdout_items = convert_to_dicts(stdout)

        for i, item in enumerate(stdout_items):
            if i < len(items):
                for key in item:
                    items[i]["Battery_" + key] = item[key]

        return items

    def get_logical_drive_facts(self):
        items = []
        if self.omreport_path is None:
            return items

        args = ["storage", "vdisk"]
        _, stdout, _ = self._run_omreport(args)
        items = convert_to_dicts(stdout)

        return items

    def get_physical_drive_facts(self, controller_facts=None):
        items = []
        if self.omreport_path is None:
            return items

        if controller_facts is None:
            controller_facts = self.get_controller_facts()

        for cid in (x["ID"] for x in controller_facts if x.get("ID")):
            args = ["storage", "pdisk", "controller=%s" % cid]
            _, stdout, _ = self._run_omreport(args)
            items.extend(convert_to_dicts(stdout))

        return items

    def get_power_supply_facts(self):
        items = []
        if self.omreport_path is None:
            return items

        args = ["chassis", "pwrsupplies"]
        _, stdout, _ = self._run_omreport(args)
        stdout_items = convert_to_dicts(stdout)
        for item in [item for item in stdout_items if "Index" in item]:
            items.append(item)

        return items

    def get_memory_facts(self):
        items = []
        if not self.omreport_path:
            return items

        args = ["chassis", "memory"]
        _, stdout, _ = self._run_omreport(args)
        stdout_items = convert_to_dicts(stdout)
        for item in [item for item in stdout_items if item.get("Index")]:
            items.append(item)

        return items

    def get_cpu_facts(self):
        items = []
        if not self.omreport_path:
            return items

        args = ["chassis", "processors"]
        _, stdout, _ = self._run_omreport(args)
        stdout_items = convert_to_dicts(stdout)
        for item in [
            item for item in stdout_items if item.get("Index") and item.get("State") == "Present"
        ]:
            items.append(item)

        return items

    def get_vendor_tool_facts(self):
        omreport_found = bool(self.omreport_path)
        dataeng_running = False
        smuxpeer_configured = False
        all_dell_services_running = False

        if os.path.isfile("/etc/init.d/dataeng"):
            try:
                args = ["/etc/init.d/dataeng", "status"]
                rc, _, _ = self.module.run_command(args)
                dataeng_running = not bool(rc)
            except Exception:
                pass

        srvadmin_services_path = self.module.get_bin_path(
            "srvadmin-services.sh", opt_dirs=["/opt/dell/srvadmin/sbin"]
        )

        if srvadmin_services_path:
            try:
                args = [srvadmin_services_path, "status"]
                rc, _, _ = self.module.run_command(args)
                all_dell_services_running = not bool(rc)
            except Exception:
                pass

        snmpd_conf = get_file_content("/etc/snmp/snmpd.conf")
        if snmpd_conf:
            pattern = re.compile(r"^\s*smuxpeer .1.3.6.1.4.1.674.10892.1")
            for line in snmpd_conf.splitlines():
                match = pattern.match(line)
                if match:
                    smuxpeer_configured = True
                    break

        tool_facts = {
            "all_dell_services_running": all_dell_services_running,
            "dataeng_running": dataeng_running,
            "omreport_errors": self.omreport_error,
            "omreport_found": omreport_found,
            "srvadmin_services_found": bool(srvadmin_services_path),
            "snmpd_smuxpeer_configured": smuxpeer_configured,
        }

        return tool_facts

    def populate(self):
        chassis_facts = self.get_chassis_facts()
        controller_facts = self.get_controller_facts()
        logical_drive_facts = self.get_logical_drive_facts()
        physical_drive_facts = self.get_physical_drive_facts(controller_facts=controller_facts)
        power_supply_facts = self.get_power_supply_facts()
        vendor_tool_facts = self.get_vendor_tool_facts()
        memory_facts = self.get_memory_facts()
        cpu_facts = self.get_cpu_facts()

        facts = {
            "controllers": controller_facts,
            "chassis": chassis_facts,
            "memory": memory_facts,
            "cpus": cpu_facts,
            "logical_drives": logical_drive_facts,
            "physical_drives": physical_drive_facts,
            "power_supplies": power_supply_facts,
            "vendor_tools": vendor_tool_facts,
        }

        return facts


def _convert_to_dict(stdout):
    def _format_line(line):
        line = line.strip()
        if line.endswith(":"):
            line = line[:-1]

        return line

    def _get_key_value(line):
        key = ""
        value = ""
        kv_pattern = re.compile(r"^\s*(.+)\:(?:\s+|$)(.*)")
        match = kv_pattern.match(line)

        if match:
            key = match.group(1).strip()
            if match.group(2):
                value = match.group(2).strip()

        return key, value

    lines = list(filter(None, stdout.split("\n")))
    info = {}
    key_stack = [[0, None, info]]
    item_queue = deque()

    for i, line in enumerate(lines):
        current_line_indent = len(line) - len(line.lstrip())
        try:
            next_line_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
        except IndexError:
            next_line_indent = current_line_indent - 1

        if next_line_indent > current_line_indent:
            while item_queue:
                key_stack[-1][2].update(item_queue.popleft())

            key = _format_line(line)
            key = key.replace(": ", "")
            key_stack[-1][2][key] = {}
            key_stack.append([next_line_indent, key, key_stack[-1][2][key]])
        else:
            key, value = _get_key_value(line)
            if key:
                item_queue.append({key: value})
            else:
                item_queue.append([_format_line(line)])

            if next_line_indent < current_line_indent:
                _, key, key_dict = key_stack.pop()
                dict_items = {}
                list_items = []

                while item_queue:
                    item = item_queue.popleft()
                    if isinstance(item, dict):
                        dict_items.update(item)
                    elif isinstance(item, list):
                        list_items.extend(item)

                if (dict_items and list_items) or dict_items:
                    key_dict.update(dict_items)
                elif list_items:
                    # associate this list back to its key
                    key_stack[-1][2][key] = list_items

                while key_stack:
                    if next_line_indent >= key_stack[-1][0]:
                        break
                    key_stack.pop()

    return info


def convert_to_dict(stdout):
    """
    Tries to parse indent based output with colon separated key value pairs
    that appears to represent a dictionary.
    """
    try:
        info = _convert_to_dict(stdout)
    except Exception:
        info = {}

    return info


def convert_to_dicts(stdout):
    """
    Tries to parse output with colon separated key value pairs. After the first
    key value pair is encountered, subsequent line breaks will start a new dict.
    """
    items = []
    pattern = re.compile(r"\s*(.*[^ ]+)\s*:\s+(.*)")
    item_dict = {}
    for line in stdout.split("\n"):
        if not line:
            if item_dict:
                items.append(item_dict)
            item_dict = {}
        else:
            match = pattern.match(line)
            if match:
                item_dict[match.group(1)] = match.group(2)

    return items


def startswith_in_dict(key, value):
    for k, v in iteritems(value):
        if k.startswith(key):
            yield v
        elif isinstance(v, dict):
            for result in startswith_in_dict(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in startswith_in_dict(key, d):
                    yield result
