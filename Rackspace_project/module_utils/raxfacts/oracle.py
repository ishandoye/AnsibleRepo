import glob
import os
import re
import shlex

from ansible.module_utils.basic import is_executable
from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class OracleFactsCollector(BaseRaxFactsCollector):

    name = "oracle"
    timeout = 180

    def _version_tuple(self, version):
        return tuple(map(int, (version.split("."))))

    def _stdout_to_dict(self, stdout):
        data = {}
        if not stdout:
            return data
        pattern = re.compile(r"\s*(.*[^ ]+)\s*:\s+(.*)")
        for line in stdout.splitlines():
            match = pattern.match(line)
            if match:
                data[match.group(1)] = match.group(2)
        return data

    def detect_oracle_apps(self):
        args = (
            "ps -eo cmd | grep -v grep| egrep -q '(FNDSM|FNDLIBR|instancename=oacore)'"
        )
        rc, _, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        return rc == 0

    def detect_oracle(self):
        args = "ps -eo cmd | grep -v grep| grep -q [_]pmon_"
        rc, _, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        return rc == 0

    def get_crsctl_resources(self, grid_user, grid_home):
        if not grid_user or not grid_home:
            return []

        args = "su %s -c '%s/bin/crsctl stat res'" % (grid_user, grid_home)
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        resources = []
        if rc == 0 and stdout:
            resource = {}
            for line in stdout.splitlines():
                if not line:
                    if resource:
                        resources.append(resource)
                        resource = {}
                elif not any(
                    [
                        line.startswith("%s=" % x)
                        for x in ["NAME", "TYPE", "TARGET", "STATE"]
                    ]
                ):
                    continue
                else:
                    key, value = line.split("=")
                    if key in ["STATE", "TARGET"]:
                        value = [x.strip() for x in value.split(",")]
                    resource[key.lower()] = value
            # Append last resource in case we didn't get a newline at the end
            if resource:
                resources.append(resource)
        return resources

    def get_grid_facts(self):
        facts = {
            "asm_instance": None,
            "asm_instance_no": None,
            "asm_pmon_detected": False,
            "asm_pmon_pid": None,
            "asm_disks": None,
            "asmlib_detected": False,
            "grid_home": None,
            "grid_user": None,
            "grid_major_version": None,
            "grid_minor_version": None,
            "grid_version": None,
            "local_node": None,
            "ocssd_detected": False,
        }

        args = "ps -eo user:32,pid,cmd | grep [a]sm_pmon_"
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc == 0 and stdout:
            user, pid, cmd = stdout.split()
            asm_instance = cmd.replace("asm_pmon_", "")
            facts["asm_pmon_detected"] = True
            facts["asm_instance"] = asm_instance
            facts["asm_instance_no"] = asm_instance.replace("+ASM", "") or None
            facts["asm_pmon_pid"] = pid
            facts["grid_user"] = user

        args = "ps -eo cmd | grep -v grep | grep [o]cssd.bin | tail -1"
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )

        if rc == 0 and stdout:
            facts["ocssd_detected"] = True
            facts["grid_home"] = stdout.strip().replace("/bin/ocssd.bin", "")

        if not facts["grid_user"] or not facts["grid_home"]:
            return facts

        facts["asmlib_detected"] = bool(self.module.get_bin_path("oracleasm"))
        blkid_path = self.module.get_bin_path("blkid")
        if blkid_path:
            args = "%s -t TYPE=oracleasm /dev/emcpower*" % blkid_path
            rc, stdout, stderr = self.module.run_command(
                args, use_unsafe_shell=True, executable="/bin/bash"
            )
            if rc == 0 and stdout:
                asm_disks = []
                for line in stdout.splitlines():
                    if not line:
                        continue

                    asm_disk = {}
                    line_split = shlex.split(line)
                    asm_disk["device"] = line_split.pop(0)[:-1]
                    for item in line_split:
                        try:
                            key = item.split("=", 1)[0].lower()
                            value = item.split("=", 1)[1]
                            asm_disk[key] = value
                        except Exception:
                            pass
                    asm_disks.append(asm_disk)
                facts["asm_disks"] = asm_disks

        args = "ls %s/inventory/Components21/oracle.crs" % facts["grid_home"]
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc == 0 and stdout:
            facts["grid_version"] = stdout.strip()

        if not facts["grid_version"]:
            args = "ls %s/inventory/Components21/oracle.server" % facts["grid_home"]
            rc, stdout, _ = self.module.run_command(
                args, use_unsafe_shell=True, executable="/bin/bash"
            )
            if rc == 0 and stdout:
                facts["grid_version"] = stdout.strip()

        if facts["grid_version"]:
            facts["grid_major_version"] = facts["grid_version"].split(".")[0]
            facts["grid_minor_version"] = facts["grid_version"].split(".")[1]
        args = "su %s -c  '%s/bin/olsnodes -l'" % (
            facts["grid_user"],
            facts["grid_home"],
        )
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc == 0 and stdout:
            facts["local_node"] = stdout.strip()

        return facts

    def get_instance_facts(self, crsctl_resources):
        args = "ps -eo user:32,pid,cmd | grep [o]ra_pmon_"
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc != 0 or not stdout:
            return None

        instances = []
        for line in stdout.splitlines():
            user, pid, cmd = line.split()
            instances.append(
                {"user": user, "pid": pid, "pmon_name": cmd.replace("ora_pmon_", "")}
            )

        for instance in instances:
            args = "dirname $(readlink -e /proc/%s/cwd)" % instance["pid"]
            rc, stdout, _ = self.module.run_command(
                args, use_unsafe_shell=True, executable="/bin/bash"
            )
            if rc == 0 and stdout:
                instance["home"] = stdout.strip()
                args = "ls %s/inventory/Components21/oracle.server" % instance["home"]
                rc, stdout, _ = self.module.run_command(
                    args, use_unsafe_shell=True, executable="/bin/bash"
                )
                version = stdout.strip() if rc == 0 and stdout else None
                instance["db_version"] = version
                sqlplus_cmd = (
                    "ORACLE_SID=%s "
                    "ORACLE_HOME=%s "
                    "LD_LIBRARY_PATH=%s/lib "
                    "%s/bin/sqlplus -s '/ as sysdba'"
                    % (
                        instance["pmon_name"],
                        instance["home"],
                        instance["home"],
                        instance["home"],
                    )
                )
                fields = [
                    "host_name",
                    "instance_name",
                    "name",
                    "version",
                    "database_role",
                    "open_mode",
                ]
                if version:
                    version_tuple = self._version_tuple(version)
                    if version_tuple[0] > 9:
                        fields.append("db_unique_name")
                    if version_tuple[:4] >= self._version_tuple("12.2.0.2"):
                        fields.append("version_full")

                query = (
                    "set pagesize 0 linesize 900 feedback off "
                    "verify off heading off echo off colsep ,;\n"
                    r"select %s from v\$instance, v\$database;" % ",".join(fields)
                )
                args = "su -s /bin/bash %s -c \"echo -e '%s' | %s\"" % (
                    instance["user"],
                    query,
                    sqlplus_cmd,
                )
                rc, stdout, _ = self.module.run_command(
                    args, use_unsafe_shell=True, executable="/bin/bash"
                )
                if rc != 0 or not stdout or "ERROR" in stdout:
                    instance["sqlplus_query_error"] = True
                    continue
                if len(stdout.splitlines()) > 1:
                    for line in stdout.splitlines():
                        if line.count(",") == len(fields) - 1:
                            stdout = line
                            break
                values = [x.strip() for x in stdout.split(",")]
                instance.update(dict(zip(fields, values)))

                # Sets db_unique_name to db_name in cases where its not
                if "db_unique_name" not in instance:
                    instance["db_unique_name"] = instance["name"]
                srvctl_cmd = (
                    "ORACLE_SID=%s "
                    "ORACLE_HOME=%s "
                    "LD_LIBRARY_PATH=%s/lib "
                    "%s/bin/srvctl config database -d %s"
                    % (
                        instance["pmon_name"],
                        instance["home"],
                        instance["home"],
                        instance["home"],
                        instance["db_unique_name"],
                    )
                )
                rc, stdout, _ = self.module.run_command(
                    srvctl_cmd, use_unsafe_shell=True, executable="/bin/bash"
                )
                if rc == 0 and stdout:
                    srvctl_config = self._stdout_to_dict(stdout)
                    instance.update(
                        {
                            "srvctl_db_instance": srvctl_config.get(
                                "Database instance"
                            ),
                            "srvctl_db_uniq_name": srvctl_config.get(
                                "Database unique name"
                            ),
                            "srvctl_type": srvctl_config.get("Type"),
                            "srvctl_candidate_servers": srvctl_config[
                                "Candidate servers"
                            ].split(",")
                            if srvctl_config.get("Candidate servers")
                            else None,
                            "srvctl_configured_nodes": srvctl_config[
                                "Configured nodes"
                            ].split(",")
                            if srvctl_config.get("Configured nodes")
                            else None,
                        }
                    )
                db_services = [
                    x
                    for x in crsctl_resources or []
                    if "svc" in x["name"]
                    and instance["db_unique_name"].lower() in x["name"].lower()
                ]
                for service in db_services:
                    svc_name = service["name"].replace(
                        "ora.%s." % instance["db_unique_name"], ""
                    )
                    service["svc_name"] = svc_name.replace(".svc", "")
                instance["db_services"] = db_services
                instance["db_in_crsctl"] = any(
                    [
                        instance["db_unique_name"].lower() in x["name"].lower()
                        for x in crsctl_resources or []
                    ]
                )
        return instances

    def get_listener_facts(self, crsctl_resources):
        args = "ps -eo user,pid,cmd | grep [t]nslsnr | grep -v SCAN"
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc != 0 or not stdout:
            return None

        resource_names = [
            x["name"].lower()
            for x in crsctl_resources or []
            if "LISTENER_SCAN" not in x["name"]
        ]
        listeners = []
        for line in stdout.splitlines():
            user, pid, bin_path, name = line.split()[:4]
            listeners.append(
                {
                    "user": user,
                    "pid": pid,
                    "home": bin_path.replace("/bin/tnslsnr", ""),
                    "name": name,
                    "listener_in_crsctl": any(
                        [name.lower() in x.lower() for x in resource_names]
                    ),
                }
            )

        return listeners

    def get_enterprise_manager_facts(self, instances):
        args = "ps -eo user,pid,cmd | grep [e]mwd.pl"
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc != 0 or not stdout:
            return

        em_facts = []
        for line in stdout.splitlines():
            facts = {
                "user": line.split()[0],
                "pid": line.split()[1],
                "path": line.split()[3].replace("/bin/emwd.pl", ""),
                "type": line.split()[4],
            }
            if facts["type"] == "dbconsole":
                facts["dbconsole_instance_name"] = None
                facts["dbconsole_oracle_sid"] = None
                if len(line.split()) == 6:
                    match = re.search(r"([^/]+)/sysman", line.split()[5])
                    if match:
                        facts["dbconsole_instance_name"] = match.group(1).split("_")[1]
                        for instance in instances:
                            if (
                                instance["pmon_name"].lower()
                                == facts["dbconsole_instance_name"].lower()
                            ):
                                facts["dbconsole_oracle_sid"] = instance["pmon_name"]
                                break
            em_facts.append(facts)
        return em_facts

    def get_acfs_facts(self):
        facts = {
            "acfs_detected": False,
            "acfs_mounts": None,
            "acfsutil_info_fs_detected": False,
            "acfsutil_registry_detected": False,
        }
        args = "df -Ph | grep '/dev/asm' | awk '{print $6}'"
        rc, stdout, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc == 0 and stdout:
            facts["acfs_detected"] = True
            facts["acfs_mounts"] = []
            for path in stdout.splitlines():
                args = "lsof %s" % path
                rc, _, _ = self.module.run_command(
                    args, use_unsafe_shell=True, executable="/bin/bash"
                )
                facts["acfs_mounts"].append(
                    {
                        "path": path,
                        "locks_detected": rc == 0,
                    }
                )
        if os.path.exists("/sbin/acfsutil"):
            args = "/sbin/acfsutil registry"
            rc, stdout, _ = self.module.run_command(
                args, use_unsafe_shell=True, executable="/bin/bash"
            )
            if rc == 0 and stdout:
                facts["acfsutil_registry_detected"] = True

            args = "/sbin/acfsutil info fs"
            rc, stdout, _ = self.module.run_command(
                args, use_unsafe_shell=True, executable="/bin/bash"
            )
            if rc == 0 and stdout:
                facts["acfsutil_info_fs_detected"] = True
        return facts

    def detect_oracle_sysv_script(self):
        return os.path.exists("/etc/init.d/oracle") and bool(
            is_executable("/etc/init.d/oracle")
        )

    def detect_sync_cron(self):
        content = get_file_content("/var/spool/cron/oracle")
        if content:
            pattern = re.compile(r"^\s*#")
            for line in content.splitlines():
                if not pattern.match(line) and "sync.sh" in line:
                    return True
        return False

    def detect_data_guard(self):
        args = "ps -eaf | grep -q [o]ra_dmon_"
        rc, _, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        return rc == 0

    def detect_golden_gate(self):
        args = "ps -eaf | grep -q [e]xtract"
        rc, _, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        return rc == 0

    def detect_erp_server_type(self):
        args = "ps -ef|grep [a]pprfs|egrep -qi 'fs1|fs2'"
        rc, _, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc == 0:
            return "ERP R12.2"

        args = "ps -ef|grep [A]pa | grep -qi 10.1.3"
        rc, _, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc == 0:
            return "ERP R12.1"

        args = r"ps -ef |egrep  -v 'beam\.smp|rabbit'| egrep -qi '[p]sdstsrv'"
        rc, _, _ = self.module.run_command(
            args, use_unsafe_shell=True, executable="/bin/bash"
        )
        if rc == 0:
            return "Peoplesoft"

        return None

    def get_inventory_pointer_path(self):
        paths = [
            "/etc/oraInst.loc",
            "/var/opt/oracle/oraInst.loc",
        ]
        inv_path = None
        for path in paths:
            if os.path.exists(path):
                inv_path = path
                break
        return inv_path

    def get_inventory_details(self, path):
        if not path:
            return []
        content = get_file_content(path) or ""
        return content.splitlines()

    def get_oratab_details(self):
        valid_lines = []
        content = get_file_content("/etc/oratab")
        if content:
            for line in content.splitlines():
                if line and not line.strip().startswith("#"):
                    valid_lines.append(line.strip().replace("\t\t", " "))
        return valid_lines

    def get_oracle_homes(self, facts):
        if facts["instances"]:
            return [x["home"] for x in facts["instances"]]
        homes = []
        for line in facts["oratab_details"]:
            # if any([ x in line for x in ['ASM', 'MGMTDB']]):
            #     continue
            try:
                homes.append(line.split(":")[1])
            except Exception:
                pass
        return homes

    def get_install_type(self, facts):
        if not facts["asm_pmon_detected"]:
            if self.module.get_bin_path("clustat"):
                return "rhcs"
            return "standalone"

        if not facts["asm_instance_no"]:
            return "has"

        grep = self.module.get_bin_path("grep")
        if not grep:
            return "unknown"

        homes = self.get_oracle_homes(facts)
        for home in homes:
            args = [
                grep,
                "oracle_install_db_InstallType",
                "%s/inventory/globalvariables/oracle.server/globalvariables.xml" % home,
            ]
            rc, stdout, _ = self.module.run_command(args)
            if rc == 0 and stdout:
                if any([x in stdout for x in ['VALUE="SE"', 'VALUE="STD"']]):
                    return "seha"
                if 'VALUE="EE"' in stdout:
                    return "rac"

            paths = glob.glob(
                "%s/inventory/Components21/oracle.server/*/context.xml" % home
            )
            if not paths:
                continue
            args = [grep, "s_serverInstallType", paths[0]]
            rc, stdout, _ = self.module.run_command(args)
            if rc == 0 and stdout:
                if any([x in stdout for x in ['VAL="SE"', 'VAL="STD"']]):
                    return "seha"
                if 'VAL="EE"' in stdout:
                    return "rac"
        return "unknown"

    def collect(self):
        if not self.detect_oracle() and not self.detect_oracle_apps():
            return None

        facts = self.get_grid_facts()
        crsctl_resources = self.get_crsctl_resources(
            facts["grid_user"], facts["grid_home"]
        )
        instances = self.get_instance_facts(crsctl_resources)
        inventory_ptr_path = self.get_inventory_pointer_path()
        facts.update(
            {
                "detected_oracle_apps": self.detect_oracle_apps(),
                "detected_erp_server_type": self.detect_erp_server_type(),
                "data_guard_detected": self.detect_data_guard(),
                "emwd": self.get_enterprise_manager_facts(instances),
                "golden_gate_detected": self.detect_golden_gate(),
                "instances": instances,
                "inventory_details": self.get_inventory_details(inventory_ptr_path),
                "inventory_pointer_path": inventory_ptr_path,
                "listeners": self.get_listener_facts(crsctl_resources),
                "oratab_details": self.get_oratab_details(),
                "sync_cron_detected": self.detect_sync_cron(),
                "sysv_init_detected": self.detect_oracle_sysv_script(),
            }
        )
        facts.update(self.get_acfs_facts())
        facts["install_type"] = self.get_install_type(facts)

        return facts
