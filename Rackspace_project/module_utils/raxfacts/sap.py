import os
import re

from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class SAPFactsCollector(BaseRaxFactsCollector):

    name = "sap"

    def _extract_fields(self, fields, output, key_prefix=None):
        data = {}
        key_prefix = key_prefix if key_prefix else ""
        for field in fields:
            key = "%s%s" % (key_prefix, field.strip().replace(" ", "_"))
            match = re.search(r"^%s\s+(.+)$" % field, output, flags=re.MULTILINE)
            data[key] = match.group(1) if match else None
        return data

    def get_host_profile_details(self):
        details = {}
        host_profile_path = "/usr/sap/hostctrl/exe/host_profile"
        if not os.path.exists(host_profile_path):
            return details

        content = get_file_content(host_profile_path)
        if content:
            pattern = re.compile(r"(.+)\s+=\s+(.+)")
            for line in content.splitlines():
                match = pattern.match(line)
                if match:
                    key = "sap_host_profile_%s" % match.group(1).lower().replace(
                        "/", "_"
                    )
                    details[key] = match.group(2)
        return details

    def get_host_agent_details(self):
        details = {}
        hostexec_log_path = "/usr/sap/hostctrl/work/dev_saphostexec"
        if not os.path.exists(hostexec_log_path):
            return details

        content = get_file_content(hostexec_log_path)
        if content:
            fields = [
                "kernel release",
                "kernel make variant",
                "compiled on",
                "compiled for",
                "compilation mode",
                "compile time",
                "update level",
                "patch number",
                "latest change number",
            ]
            details = self._extract_fields(
                fields, content, key_prefix="sap_host_agent_"
            )
        return details

    def get_instance_profiles(self):
        profile_data = []
        args = "ls -1 /usr/sap/???/SYS/profile/???_D*_$HOSTNAME 2>/dev/null"
        _, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if not stdout:
            args = "ls -1 /usr/sap/???/SYS/profile/???_*_* 2>/dev/null"
            _, stdout, _ = self.module.run_command(
                args, use_unsafe_shell=True, executable="/bin/bash"
            )
            if not stdout:
                return profile_data

        fields = [
            "kernel release",
            "kernel make variant",
            "compiled on",
            "compiled for",
            "compilation mode",
            "compile time",
            "update level",
            "patch number",
        ]
        for profile in stdout.splitlines():
            sys_id = os.path.basename(profile)[:3]
            disp_work_path = "/usr/sap/%s/SYS/exe/run/disp+work" % (sys_id)
            cmd_output = ""
            if os.path.exists(disp_work_path):
                ld_library_path = "/usr/sap/%s/SYS/exe/run:$LD_LIBRARY_PATH" % (sys_id)
                args = "LD_LIBRARY_PATH=%s %s" % (ld_library_path, disp_work_path)
                rc, stdout, _ = self.module.run_command(
                    args, use_unsafe_shell=True, executable="/bin/bash"
                )
                if rc == 0:
                    cmd_output = stdout
            profile_details = {
                "profile_path": profile,
                "system_id": sys_id,
            }
            profile_details.update(
                self._extract_fields(fields, cmd_output, key_prefix="profile_")
            )
            profile_data.append(profile_details)
        return profile_data

    def get_subscription_details(self):
        details = {
            "sap_subscription_rhel_detected": False,
            "sap_subscription_sles_detected": False,
        }
        if os.path.exists("/etc/SuSE-release"):
            if os.path.exists("/etc/products.d/SLES_SAP.prod"):
                details["sap_subscription_sles_detected"] = True
        elif os.path.exists("/etc/yum.repos.d/redhat.repo"):
            args = r"egrep -q '(-\ SAP\ |for\ SAP\ HANA|for\ SAP\ )' /etc/yum.repos.d/redhat.repo"
            rc, _, _ = self.module.run_command(
                args, use_unsafe_shell=True, executable="/bin/bash"
            )
            if rc == 0:
                details["sap_subscription_rhel_detected"] = True
        return details

    def collect(self):
        facts = self.get_host_profile_details()
        if not facts:
            return None
        facts.update(self.get_host_agent_details())
        facts.update(self.get_subscription_details())
        facts["sap_instance_profiles"] = self.get_instance_profiles()
        return facts
