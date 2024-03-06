import os
import re
from xml.etree import ElementTree as ET

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class AntiVirusFactsCollector(BaseRaxFactsCollector):

    name = "antivirus"

    def collect(self):
        av_facts = {}

        if self.module.get_bin_path("savdstatus", opt_dirs=["/opt/sophos-av/bin"]):
            av_facts["vendor"] = "Sophos"
            av_facts.update(SophosFacts(self.module).populate())
        elif os.path.exists("/opt/sophos-spl/bin"):
            av_facts["vendor"] = "Sophos Central"
            av_facts.update(SophosCentralFacts(self.module).populate())

        return av_facts


class SophosFacts(object):
    def __init__(self, module):
        self.module = module
        self.bin_status = self.module.get_bin_path(
            "savdstatus", opt_dirs=["/opt/sophos-av/bin"]
        )
        self.bin_config = self.module.get_bin_path(
            "savconfig", opt_dirs=["/opt/sophos-av/bin"]
        )
        self.service_path = self.module.get_bin_path("service")
        self.av_error = False

    def _get_type(self, variable):
        try:
            return int(variable)
        except ValueError:
            pass

        if variable == "true":
            return True
        elif variable == "false":
            return False
        else:
            return variable

    def _run_cmd(self, cmd, args):
        args = [cmd] + args
        rc, stdout, stderr = self.module.run_command(args)
        if rc != 0:
            self.av_error = True

        return rc, stdout, stderr

    def _pidof(self, name):
        name = str(name)
        pids = []
        if not name:
            return pids

        pattern = re.compile("/proc/([0-9]+)/cmdline")
        cmd = "grep -l ^" + name + " /proc/*/cmdline"
        _, stdout, _ = self.module.run_command(cmd, use_unsafe_shell=True)

        for line in stdout.splitlines():
            match = pattern.match(line)
            if match:
                pids.append(match.group(1))

        return pids

    def get_on_access_interface(self):
        talpa_sys_path = "/proc/sys/talpa/interceptors/VFSHookInterceptor/status"
        talpa_status = get_file_content(talpa_sys_path, default="")
        if talpa_status == "enabled":
            return "talpa"

        pids = self._pidof("savscand")
        if pids:
            for pid in pids:
                rc, _, _ = self.module.run_command(
                    "grep -q fanotify /proc/%s/fdinfo/*" % pid, use_unsafe_shell=True
                )
                if not rc:
                    return "fanotify"

        return None

    def get_sophos_config(self):
        av_config = {}
        if self.bin_config is None:
            return av_config

        cmd = self.bin_config
        args = ["--advanced", "--all"]
        _, stdout_lines, _ = self._run_cmd(cmd, args)

        # Example of the config output:
        #
        # EnableOnStart: true
        # EnableAutoUpdating (Locked): true
        # ExcludeFileOnGlob: /tmp/clamav*
        #                    /tmp/odeiavir*
        # FileCacheSizeBytes: 4096

        key_value_pattern = re.compile(r"^([^ ]+)\s*[^:]*:\s+(.*)$")
        value_only_pattern = re.compile(r"^\s+([^ ]+)$")
        list_values = []
        last_key = ""
        last_value = ""

        for line in stdout_lines.splitlines():
            key_value = key_value_pattern.match(line)
            if key_value:
                # When there are values in the list, add them to the last key
                if list_values:
                    av_config[last_key] = list_values
                    list_values = []
                else:
                    if last_key and last_value:
                        av_config[last_key] = self._get_type(last_value)

                last_key = key_value.group(1).strip()
                last_value = key_value.group(2).strip()
                continue

            value_only = value_only_pattern.match(line)
            if value_only:
                if last_value:
                    list_values.append(self._get_type(last_value))
                    last_value = ""

                list_values.append(value_only.group(1).strip())

        # Add the last key/value(s) pair
        if last_key:
            if list_values:
                av_config[last_key] = list_values
            else:
                av_config[last_key] = self._get_type(last_value)

        # Some configs are "hidden" as they are in beta, get them manually
        beta_keys = ["PreferFanotify", "DisableFanotify"]
        for beta_key in beta_keys:
            args = ["get", beta_key]
            _, stdout, _ = self._run_cmd(cmd, args)
            if stdout:
                av_config[beta_key] = self._get_type(stdout.strip())

        return camel_dict_to_snake_dict(av_config)

    def get_sophos_status(self):
        av_status = {}
        if self.bin_status is None:
            return av_status

        cmd = self.bin_status
        args = ["--version"]
        _, stdout_lines, _ = self._run_cmd(cmd, args)

        # Example of the status output:
        #
        # Copyright 1989-2018 Sophos Limited. All rights reserved.
        # Sophos Anti-Virus       = 9.15.1
        # Last update             = Thu 22 Aug 2019 12:10:32 PM CDT

        pattern = re.compile(r"^(.*)\s*=\s*(.*)$")

        for line in stdout_lines.splitlines():
            match = pattern.match(line)
            if match:
                key = match.group(1).strip()
                # Get CamelCase, removing "-" from it
                key = re.sub("-", "", key)
                key = "".join(key.title().split(" "))

                av_status[key] = self._get_type(match.group(2).strip())

        # Add version details
        if av_status.get("SophosAntivirus"):
            version = av_status.get("SophosAntivirus")
            av_status["full_version"] = version
            av_status["major_version"] = self._get_type(version.split(".")[0])
            av_status["minor_version"] = self._get_type(version.split(".")[1])
            av_status["point_release"] = self._get_type(version.split(".")[2])

        args = ["--verbose"]
        _, stdout_lines, _ = self._run_cmd(cmd, args)

        # Example of the status output:
        #
        # Sophos Anti-Virus daemon is (active|inactive)
        # On-access scanning is (not) running

        for line in stdout_lines.splitlines():
            match = re.match("^Sophos.*daemon is (.*)$", line)
            if match:
                # savdstatus only checks for sav-protect daemon
                av_status["sav_protect_active"] = match.group(1).strip() == "active"

            match = re.match("^On-access.*is (.*)$", line)
            if match:
                av_status["on_access_active"] = match.group(1).strip() == "running"

        # Check sav-rms status
        cmd = self.service_path
        if cmd:
            try:
                args = ["sav-rms", "status"]
                rc, _, _ = self._run_cmd(cmd, args)
                sav_rms_active = not bool(rc)
            except Exception:
                pass

            av_status["sav_rms_active"] = sav_rms_active

        # Add hostname and description from sophos config
        description = get_file_content("/opt/sophos-av/etc/description", default="")
        hostname = get_file_content("/opt/sophos-av/etc/hostname", default="")
        update_ts = get_file_content(
            "/opt/sophos-av/etc/update.last_update", default=""
        )
        av_status["sophos_description"] = description or None
        av_status["sophos_hostname"] = hostname or None
        av_status["last_update_ts"] = self._get_type(update_ts) or None

        # Get on-access interface (talpa or fanotify)
        if av_status.get("on_access_active"):
            av_status["on_access_interface"] = self.get_on_access_interface()

        return camel_dict_to_snake_dict(av_status)

    def populate(self):
        config_facts = self.get_sophos_config()
        status_facts = self.get_sophos_status()

        facts = {
            "config": config_facts,
            "status": status_facts,
            "av_cmd_errors": self.av_error,
        }

        return facts


class XMLData(object):
    NS_RE = re.compile(r"\{([^\}]+)\}(.+)")

    def __init__(self, fname):
        self.root = ET.parse(fname)
        self.ns = {}
        top = next(iter(self.root.findall(".")), None)
        if top is None:
            raise ValueError("No XML data")

    def get_namespace_from_element(self, start, elem, tag):
        start = self.find_single_element(".")
        for m in filter(None, [self.NS_RE.match(e.tag) for e in start]):
            if m.group(2) == elem:
                self.ns[tag] = m.group(1)
                break

    def find_elements(self, xpath, start=None):
        return (start or self.root).findall(xpath, self.ns) or []

    def find_single_element(self, xpath, start=None):
        return (start or self.root).find(xpath, self.ns)

    def get_single_element_text(self, xpath, start=None, default=None):
        elem = self.find_single_element(xpath, start)
        if elem is None:
            return default
        return elem.text

    def element_as_bool(self, xpath, start=None):
        return self.get_single_element_text(xpath, start, "").lower() == "true"

    def element_as_list(self, xpath, start=None):
        return [e.text for e in self.find_elements(xpath, start)]


class SophosCentralFacts(object):
    def __init__(self, module):
        self.module = module
        self.av_error = False
        self.systemctl = self.module.get_bin_path("systemctl")

    def _run_cmd(self, cmd, args):
        args = [cmd] + args
        rc, stdout, stderr = self.module.run_command(args)
        if rc != 0:
            self.av_error = True

        return rc, stdout, stderr

    def parse_xml(self, fname):
        try:
            return XMLData(fname)
        except Exception:
            # File missing, unreadable, empty, etc
            self.av_error = True
            return None

    def parse_version_ini(self, fname):
        data = {}
        for k, _, v in [
            l.partition("=") for l in get_file_content(fname, "").splitlines() if "=" in l
        ]:
            data[k.strip().upper()] = v.strip()
        ret = {}
        if "PRODUCT_NAME" in data:
            prd_name = data["PRODUCT_NAME"].replace("-", "_").lower()
            ret["%s_version" % prd_name] = data.get("PRODUCT_VERSION", "unknown")
            ret["%s_build_date" % prd_name] = data.get("BUILD_DATE", "unknown")
        return ret

    def get_sophos_config(self):
        cfg = {}
        core_policy = self.parse_xml("/opt/sophos-spl/base/mcs/policy/CORE_policy.xml")
        ops = {
            "read": "./onAccessScan/onRead",
            "write": "./onAccessScan/onWrite",
            "exec": "./onAccessScan/onExec",
        }
        if core_policy:
            cfg["on_access_enabled"] = core_policy.element_as_bool("./onAccessScan/enabled")
            cfg["on_access_operations"] = " ".join(
                ["+%s" % op for op in ops if core_policy.element_as_bool(ops[op])]
            )
            cfg["exclude_file_path"] = core_policy.element_as_list(
                "./onAccessScan/exclusions/filePathSet/filePath"
            )
            cfg["exclude_remote_files"] = core_policy.element_as_bool(
                "./onAccess/exclusions/excludeRemoteFiles"
            )
        for key, _, val in [
            l.partition("=")
            for l in get_file_content("/opt/sophos-spl/base/etc/sophosspl/mcs.config").splitlines()
            if "=" in l
        ]:
            if key in ("MCSID", "device_id", "tenant_id"):
                cfg["sophos_%s" % key.lower()] = val
        return cfg

    def get_sophos_status(self):
        sts = {}
        for ver_file in (
            "/opt/sophos-spl/base/VERSION.ini",
            "/opt/sophos-spl/plugins/runtimedetections/VERSION.ini",
            "/opt/sophos-spl/plugins/eventjournaler/VERSION.ini",
            "/opt/sophos-spl/plugins/av/VERSION.ini",
        ):
            sts.update(self.parse_version_ini(ver_file))
        rc, _, _ = self._run_cmd(self.systemctl, ["is-active", "sophos-spl.service"])
        sts["sophos_spl_active"] = rc == 0
        alc_status = self.parse_xml("/opt/sophos-spl/base/mcs/status/ALC_status.xml")
        if alc_status:
            alc_status.get_namespace_from_element(alc_status.root, "autoUpdate", "au")
            items = {
                "auto_update_download_state": "./au:autoUpdate/au:downloadState/au:state",
                "auto_update_install_state": "./au:autoUpdate/au:installState/au:state",
                "auto_update_last_good": "./au:autoUpdate/au:installState/au:lastGood",
            }
            for key, xpath in items.items():
                state = alc_status.get_single_element_text(xpath)
                if state:
                    sts[key] = state
        return sts

    def populate(self):
        config_facts = self.get_sophos_config()
        status_facts = self.get_sophos_status()

        return {"config": config_facts, "status": status_facts, "av_cmd_errors": self.av_error}
