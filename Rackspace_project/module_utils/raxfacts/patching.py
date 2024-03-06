import json
import os
import platform
import re
import sys
import time

from ansible.module_utils.facts.utils import get_file_content, get_file_lines
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class PatchingFactsCollector(BaseRaxFactsCollector):

    name = "patching"

    def old_lock_file_detected(self, path):
        try:
            seconds = int(time.time() - os.path.getmtime(path))
            return seconds >= 21600
        except Exception:
            return False

    def _get_pkg_manager(self):
        PKG_MGRS = {
            "apt": "/usr/bin/apt-get",
            "dnf": "/usr/bin/dnf",
            "yum": "/usr/bin/yum",
        }

        if os.path.exists(PKG_MGRS["apt"]):
            return "apt"

        elif os.path.exists(PKG_MGRS["dnf"]):
            try:
                import dnf  # pylint: disable=unused-import
            except ImportError:
                raise Exception("Error using python dnf module")
            return "dnf"

        elif os.path.exists(PKG_MGRS["yum"]):
            try:
                import yum  # pylint: disable=unused-import
            except ImportError:
                raise Exception("Error using python yum module")
            return "yum"

        raise Exception("Unable to determine package manager")

    def needs_reboot(self, package_manager):
        if package_manager == "apt":
            return os.path.exists("/var/run/reboot-required")
        else:
            # We won't return a value if the needs-restarting binary is not found
            # or if the return code is not explicitly 1(reboot required) or 0(no reboot required)
            needs_restarting = self.module.get_bin_path("needs-restarting")
            if needs_restarting:
                rc, _, _ = self.module.run_command([needs_restarting, "-r"])
                if rc == 0:
                    return False
                if rc == 1:
                    return True
            return None

    def get_apt_facts(self, facts):
        auto_update_details = {}
        _, stdout, _ = self.module.run_command(
            'grep -Erh "^deb " /etc/apt/sources.list /etc/apt/sources.list.d/*.list',
            use_unsafe_shell=True,
            executable="/bin/bash",
        )

        facts["enabled_repos"] = stdout.splitlines()

        _, stdout, _ = self.module.run_command(
            "ls -t /var/lib/dpkg/info/*.list | head -1",
            use_unsafe_shell=True,
            executable="/bin/bash",
        )

        if stdout:
            mtime = os.path.getmtime(stdout.rstrip())
            facts["last_pkg_install_date"] = time.strftime(
                "%a %d %b %Y %I:%M:%S %p %Z",
                time.localtime(mtime),
            )

        apt_get = self.module.get_bin_path("apt-get")
        if apt_get:
            _, _, stderror = self.module.run_command(apt_get + " -qq update")
            if stderror:
                facts["repo_issue_detected"] = True
                facts["repo_issue_details"] = stderror

            rc, stdout, _ = self.module.run_command(
                [
                    apt_get,
                    '-oDir::Cache::archives=""',  # unset so we get uri's for downloaded pkgs
                    "--assume-yes",
                    "--print-uris",  # this just prints the URIs instead of making changes
                    "upgrade",
                ],
                use_unsafe_shell=True,
                executable="/bin/bash",
            )
            if rc == 0:
                # '<uri>' <filename> <pkg_size> MD5Sum:<md5sum>
                for uri_line in [
                    l for l in stdout.splitlines() if l.startswith("'http")
                ]:
                    _, filename, pkg_size, _ = uri_line.split()
                    facts["available_updates"].append(
                        "=".join(filename.replace("%3a", ":").strip(".deb").split("_"))
                    )
                    facts["available_updates_size"] += int(pkg_size)
            else:
                match = re.search(
                    r"^The following packages have unmet dependencies:\n(^\s.*\n)+",
                    stdout,
                    re.M,
                )

                if match:
                    facts["dependency_issue_detected"] = True
                    facts["dependency_issue_details"] = match.group()

        apt_mark = self.module.get_bin_path("apt-mark")
        if apt_mark:
            _, stdout, _ = self.module.run_command(apt_mark + " showhold")

            facts["pkg_excludes_from_pkg_mgr"] = stdout.splitlines()

        apt_config = self.module.get_bin_path("apt-config")
        if apt_config:
            config = {}
            _, stdout, _ = self.module.run_command(apt_config + " dump")

            for line in stdout.split("\n"):
                try:
                    k, v = line.split(None, 1)
                    if k in config:
                        config[k].append(v[1:-2])
                    else:
                        if v[1:-2]:
                            config[k] = [v[1:-2]]
                except Exception:
                    pass

            if config.get("APT::Periodic::Unattended-Upgrade") == ["1"]:
                facts["auto_update_service"] = "unattended-upgrades"
                daily_timer_rc, _, _ = self.module.run_command(
                    "systemctl is-enabled apt-daily.timer"
                )
                daily_upgrade_timer_rc, _, _ = self.module.run_command(
                    "systemctl is-enabled apt-daily-upgrade.timer"
                )
                facts["auto_update_enabled"] = all(
                    [daily_timer_rc == 0, daily_upgrade_timer_rc == 0]
                )
                if config.get("Unattended-Upgrade::Allowed-Origins::"):
                    auto_update_details["allowed_origins"] = config.get(
                        "Unattended-Upgrade::Allowed-Origins::"
                    )
                if config.get("Unattended-Upgrade::Origins-Pattern::"):
                    auto_update_details["origin_patterns"] = config.get(
                        "Unattended-Upgrade::Origins-Pattern::"
                    )
                facts["pkg_excludes_from_auto_update"] = config.get(
                    "Unattended-Upgrade::Package-Blacklist::"
                )
                facts["pkg_includes_from_auto_update"] = config.get(
                    "Unattended-Upgrade::Package-Whitelist::"
                )

                automatic_reboot_time = config.get(
                    "Unattended-Upgrade::Automatic-Reboot-Time"
                )
                auto_update_details["automatic_reboot_time"] = (
                    ",".join(automatic_reboot_time or []) or None
                )

                reboot_with_users = config.get(
                    "Unattended-Upgrade::Automatic-Reboot-WithUsers"
                )
                auto_update_details["reboot_with_users"] = (
                    json.loads(",".join(reboot_with_users))
                    if reboot_with_users
                    else reboot_with_users
                )

                reboot_enabled = config.get("Unattended-Upgrade::Automatic-Reboot")
                auto_update_details["automatic_reboot_enabled"] = (
                    json.loads(",".join(reboot_enabled))
                    if reboot_enabled
                    else reboot_enabled
                )

                remove_unused_dependencies = config.get(
                    "Unattended-Upgrade::Remove-Unused-Dependencies"
                )
                auto_update_details["remove_unused_dependencies"] = (
                    json.loads(",".join(remove_unused_dependencies))
                    if remove_unused_dependencies
                    else remove_unused_dependencies
                )

                remove_unused_kernel_packages = config.get(
                    "Unattended-Upgrade::Remove-Unused-Kernel-Packages"
                )
                auto_update_details["remove_unused_kernel_packages"] = (
                    json.loads(",".join(remove_unused_kernel_packages))
                    if remove_unused_kernel_packages
                    else remove_unused_kernel_packages
                )

                rc, apt_daily_timer_conf, _ = self.module.run_command(
                    "systemctl cat apt-daily.timer"
                )
                parsed_apt_daily_timer_conf = {}
                if rc == 0:
                    if apt_daily_timer_conf:
                        keys = ["OnCalendar", "RandomizedDelaySec"]
                        for key in keys:
                            match = re.search("%s=(.*)" % key, apt_daily_timer_conf)
                            if match:
                                parsed_apt_daily_timer_conf[key.lower()] = (
                                    match.group(1) or None
                                )

                auto_update_details["apt_daily_timer_conf"] = (
                    parsed_apt_daily_timer_conf or None
                )

                rc, apt_daily_upgrade_timer_conf, _ = self.module.run_command(
                    "systemctl cat apt-daily-upgrade.timer"
                )
                parsed_apt_daily_upgrade_timer_conf = {}
                if rc == 0:
                    if apt_daily_upgrade_timer_conf:
                        keys = ["OnCalendar", "RandomizedDelaySec"]
                        for key in keys:
                            match = re.search(
                                "%s=(.*)" % key, apt_daily_upgrade_timer_conf
                            )
                            if match:
                                parsed_apt_daily_upgrade_timer_conf[key.lower()] = (
                                    match.group(1) or None
                                )
                auto_update_details["apt_daily_upgrade_timer_conf"] = (
                    parsed_apt_daily_upgrade_timer_conf or None
                )

        facts["auto_update_details"] = auto_update_details or None
        facts["needs_reboot"] = self.needs_reboot("apt")
        return facts

    def get_dnf_facts(self, facts):
        import dnf

        base = None
        enabled_repo_ids = []
        try:
            base = dnf.Base()
            base.conf.debuglevel = 0
            base.conf.errorlevel = 0
            base.conf.read()
            base.init_plugins()

            # Explicitly set skip_if_unavailable for the transaction
            # https://dnf.readthedocs.io/en/stable/cli_vs_yum.html#skip-if-unavailable-could-be-enabled-by-default
            if not hasattr(base.conf, "skip_if_unavailable"):
                base.conf.skip_if_unavailable = True

            base.conf.substitutions.update_from_etc(base.conf.installroot)
            base.pre_configure_plugins()
            base.read_all_repos()
            base.configure_plugins()
            facts["pkg_excludes_from_pkg_mgr"] = list(set(base.conf.exclude))

            for repo in base.repos.iter_enabled():
                enabled_repo_ids.append(repo.id)
                facts["enabled_repos"].append(repo.name)
                facts["pkg_includes_from_repos"].extend(repo.includepkgs)
                if repo.exclude != facts["pkg_excludes_from_pkg_mgr"]:
                    facts["pkg_excludes_from_repos"].extend(repo.exclude)

            try:
                base.update_cache()
                base.fill_sack()
            except Exception:
                _, ex_msg = sys.exc_info()[:2]
                facts["repo_issue_details"] = str(ex_msg)
                facts["repo_issue_detected"] = True

            # Find disabled repos
            disabled_repo_ids = list(
                set(enabled_repo_ids) - set([r.id for r in base.repos.iter_enabled()])
            )
            if disabled_repo_ids:
                facts["repo_issue_details"] = facts.get(
                    "repo_issue_details"
                ) or "" + "Disabled repos: " + ", ".join(disabled_repo_ids)

            # Get candidate packages for upgrade
            update_list = base.sack.query().upgrades().latest()
            if update_list:
                for pkg in update_list:
                    name, arch, epoch, ver, rel = pkg.pkgtup
                    facts["available_updates"].append(
                        "%s-%s:%s-%s.%s" % (name, epoch, ver, rel, arch)
                    )
                    facts["available_updates_size"] += pkg.size

                try:
                    base.upgrade_all()
                    base.resolve()
                except Exception:
                    _, ex_msg = sys.exc_info()[:2]
                    facts["dependency_issue_details"] = str(ex_msg)
                    facts["dependency_issue_detected"] = True

            # Query object for installed packages (Explicitly use
            # rpmdb_sack in case repos are broken)
            # Uses the private method since this is available across all versions.
            # It is also what is returned when calling the public method.
            q = dnf.sack._rpmdb_sack(base).query()

            # Get last package install time
            install_times = sorted([pkg.installtime for pkg in q.installed()])
            if install_times:
                facts["last_pkg_install_date"] = time.strftime(
                    "%a %d %b %Y %I:%M:%S %p %Z",
                    time.localtime(install_times[-1]),
                )

            # Nightly patching
            if "dnf-automatic" in [pkg.name for pkg in q.installed()]:
                facts["auto_update_service"] = "dnf-automatic"
                facts["auto_update_enabled"] = False
                if self.module.get_bin_path("systemctl"):
                    _, stdout, _ = self.module.run_command(
                        "systemctl is-enabled dnf-automatic.timer; "
                        "systemctl is-active dnf-automatic.timer",
                        use_unsafe_shell=True,
                        executable="/bin/bash",
                    )
                    if all([x in stdout for x in ["active", "enabled"]]):
                        facts["auto_update_enabled"] = True

                dnf_automatic_conf = get_file_lines("/etc/dnf/automatic.conf")
                rows = [
                    row.replace(" ", "")
                    for row in dnf_automatic_conf
                    if row and not row.startswith("#")
                ]
                parsed_dnf_automatic_conf = dict(
                    key.lower().split("=") for key in rows if "=" in key
                )
                for k, v in parsed_dnf_automatic_conf.items():
                    if not v or v.lower() == "none":
                        parsed_dnf_automatic_conf[k] = None
                        continue
                    if v == "no":
                        parsed_dnf_automatic_conf[k] = False
                        continue
                    if v == "yes":
                        parsed_dnf_automatic_conf[k] = True
                        continue
                    try:
                        if v.strip("'\"").isdigit():
                            parsed_dnf_automatic_conf[k] = int(v.strip("'\""))
                        else:
                            parsed_dnf_automatic_conf[k] = json.loads(v)
                    except ValueError:
                        pass
                facts["auto_update_details"] = parsed_dnf_automatic_conf

                # Get dnf-automatic.timer
                rc, stdout, _ = self.module.run_command(
                    "systemctl cat dnf-automatic.timer"
                )
                if rc == 0:
                    dnf_timer_conf = {}
                    keys = ["OnCalendar", "RandomizedDelaySec"]
                    for key in keys:
                        match = re.search("%s=(.*)" % key, stdout)
                        if match:
                            dnf_timer_conf[key.lower()] = match.group(1) or None
                    facts["auto_update_details"].update(dnf_timer_conf)

        finally:
            if base:
                base.close()

        facts["needs_reboot"] = self.needs_reboot("dnf")
        return facts

    def get_yum_facts(self, facts):
        import yum

        yb = None
        try:
            try:
                yb = yum.YumBase()
                yb.preconf.debuglevel = 0
                yb.preconf.errorlevel = 0
                facts["pkg_excludes_from_pkg_mgr"] = yb.conf.exclude
                for repo in yb.repos.listEnabled():
                    facts["enabled_repos"].append(repo.name)
                    facts["pkg_includes_from_repos"].extend(repo.includepkgs)
                    if repo.exclude != facts["pkg_excludes_from_pkg_mgr"]:
                        facts["pkg_excludes_from_repos"].extend(repo.exclude)
                    try:
                        repo.ready()
                    except Exception:
                        _, ex_msg = sys.exc_info()[:2]
                        facts["repo_issue_details"] = str(ex_msg)
                        facts["repo_issue_detected"] = True

                if not facts["repo_issue_detected"]:
                    update_list = yb.doPackageLists("updates").updates
                    if update_list:
                        for pkg in update_list:
                            name, arch, epoch, ver, rel = pkg.pkgtup
                            facts["available_updates"].append(
                                "%s-%s:%s-%s.%s" % (name, epoch, ver, rel, arch)
                            )
                            facts["available_updates_size"] += pkg.size

                        yb.update()
                        rc, results = yb.resolveDeps()

                        if rc == 1:
                            facts["dependency_issue_details"] = "\n".join(results)
                            facts["dependency_issue_detected"] = True

            except Exception:
                _, ex_msg = sys.exc_info()[:2]
                facts["other_issue_details"] = str(ex_msg)
                facts["other_issue_detected"] = True
        finally:
            if yb:
                yb.close()
                yb.closeRpmDB()

        auto_update_details = {}
        rpm_path = self.module.get_bin_path("rpm")
        if rpm_path:
            rc, _, _ = self.module.run_command("rpm -q yum-cron")

            if rc == 0:
                facts["auto_update_service"] = "yum-cron"
                _, os_ver, _ = platform.dist()
                if os_ver.startswith("6"):
                    yum_cron_cmd = "/sbin/chkconfig --list yum-cron | egrep '3:on|5:on'"
                    yum_cron_file = "/etc/sysconfig/yum-cron"
                if os_ver.startswith("7"):
                    yum_cron_cmd = "systemctl -q is-enabled yum-cron.service"
                    yum_cron_file = "/etc/yum/yum-cron.conf"

                yum_cron_enabled_rc, _, _ = self.module.run_command(
                    yum_cron_cmd, use_unsafe_shell=True, executable="/bin/bash"
                )
                facts["auto_update_enabled"] = yum_cron_enabled_rc == 0

                yum_cron_conf = get_file_lines(yum_cron_file)
                # Look away...
                rows = [
                    row.replace(" ", "")
                    for row in yum_cron_conf
                    if row and not row.startswith("#")
                ]
                parsed_yum_cron_conf = dict(
                    key.lower().split("=") for key in rows if "=" in key
                )
                for k, v in parsed_yum_cron_conf.items():
                    if not v or v.lower() == "none":
                        parsed_yum_cron_conf[k] = None
                        continue
                    if v == "no":
                        parsed_yum_cron_conf[k] = False
                        continue
                    if v == "yes":
                        parsed_yum_cron_conf[k] = True
                        continue
                    try:
                        if v.strip("'\"").isdigit():
                            parsed_yum_cron_conf[k] = int(v.strip("'\""))
                        else:
                            parsed_yum_cron_conf[k] = json.loads(v)
                    except ValueError:
                        pass
                auto_update_details.update(parsed_yum_cron_conf)

            anacron_conf = get_file_content("/etc/anacrontab")
            parsed_anacron_conf = {}
            if anacron_conf:
                keys = ["START_HOURS_RANGE", "RANDOM_DELAY"]
                for key in keys:
                    match = re.search("%s=(.*)" % key, anacron_conf)
                    if match:
                        parsed_anacron_conf[key.lower()] = match.group(1) or None
            auto_update_details.update(parsed_anacron_conf)

            auto_update_details["cron_daily_enabled"] = os.path.exists(
                "/etc/cron.daily/0yum-daily.cron"
            )
            auto_update_details["cron_weekly_enabled"] = os.path.exists(
                "/etc/cron.hourly/0yum-hourly.cron"
            )

            _, stdout, _ = self.module.run_command(
                r"rpm -qa --last | head -1 | sed 's/[^ ]*[ ]*\(.*\)/\1/'",
                use_unsafe_shell=True,
                executable="/bin/bash",
            )

            if stdout:
                facts["last_pkg_install_date"] = stdout.rstrip()

        facts["auto_update_details"] = auto_update_details
        facts["needs_reboot"] = self.needs_reboot("yum")
        return facts

    def get_managed_patching_state(self):
        path = "/var/lib/rackspace/patching/enabled"
        return os.path.exists(path)

    def collect(self):
        facts = {
            "auto_update_details": None,
            "auto_update_enabled": False,
            "auto_update_service": None,
            "available_updates": [],
            "available_updates_size": 0,
            "dependency_issue_details": None,
            "dependency_issue_detected": False,
            "enabled_repos": [],
            "last_pkg_install_date": None,
            "needs_reboot": None,
            "other_issue_details": None,
            "other_issue_detected": False,
            "pkg_excludes_from_auto_update": None,
            "pkg_excludes_from_pkg_mgr": None,
            "pkg_excludes_from_repos": [],
            "pkg_includes_from_auto_update": None,
            "pkg_includes_from_repos": [],
            "pkg_manager": None,
            "repo_issue_details": None,
            "repo_issue_detected": False,
            "managed_patching_enabled": self.get_managed_patching_state(),
        }

        try:
            facts["pkg_manager"] = self._get_pkg_manager()
        except Exception:
            _, ex_msg = sys.exc_info()[:2]
            facts["other_issue_details"] = str(ex_msg)
            facts["other_issue_detected"] = True

        if facts["pkg_manager"] == "dnf":
            lock_file = "/var/cache/dnf/metadata_lock.pid"
            if self.old_lock_file_detected(lock_file):
                facts["other_issue_detected"] = True
                facts["other_issue_details"] = "Old lockfile found at %s" % lock_file
            else:
                facts.update(self.get_dnf_facts(facts))

        elif facts["pkg_manager"] == "yum":
            lock_file = "/var/run/yum.pid"
            if self.old_lock_file_detected(lock_file):
                facts["other_issue_detected"] = True
                facts["other_issue_details"] = "Old lockfile found at %s" % lock_file
            else:
                facts.update(self.get_yum_facts(facts))

        elif facts["pkg_manager"] == "apt":
            facts.update(self.get_apt_facts(facts))

        facts["available_updates_count"] = len(facts["available_updates"])
        facts["available_updates"] = sorted(facts["available_updates"]) or None
        facts["enabled_repos"] = facts["enabled_repos"] or None
        facts["pkg_excludes_from_pkg_mgr"] = facts["pkg_excludes_from_pkg_mgr"] or None
        facts["pkg_excludes_from_repos"] = facts["pkg_excludes_from_repos"] or None
        facts["pkg_includes_from_repos"] = facts["pkg_includes_from_repos"] or None

        return facts


class AuterFactsCollector(BaseRaxFactsCollector):

    name = "auter"

    def collect(self):
        def _auter_version():
            rpm_path = self.module.get_bin_path("rpm")
            if not rpm_path:
                return None

            (rc, stdout, _) = self.module.run_command(
                rpm_path + ' -q --queryformat "%{VERSION}" auter'
            )

            if rc != 0:
                return None

            return stdout

        def _auter_enabled():
            auter_path = self.module.get_bin_path("auter")

            if not auter_path:
                self.debug.append(
                    {"auter": "Auter script not found, cannot check status"}
                )
                return None, None

            (rc, stdout, stderr) = self.module.run_command(auter_path + " --status")
            if rc != 0:
                self.debug.append({"auter": "Auter script gave an error: " + stderr})
                return None, None

            is_enabled = "currently enabled" in stdout
            is_running = "not running" not in stdout

            return is_enabled, is_running

        def _auter_last_run():
            (_, stdout, _) = self.module.run_command("ls -1rt /var/log/")
            msgs_files = [
                "/var/log/" + filename
                for filename in stdout.split("\n")
                if "messages" in filename
            ]

            if not msgs_files:
                return None

            # Try to get the new style logging format with ISO-8601 date
            try:
                (_, stdout, _) = self.module.run_command(
                    'zgrep -h "Auter successfully ran at" ' + " ".join(msgs_files)
                )
                run_dates = stdout.strip().split("\n")
                last_run = " ".join(run_dates[-1].split()[-1])
                return last_run
            except (IndexError, TypeError):
                # IndexError thrown when run_dates is []
                # TypeError thrown when run_dates is None
                pass

            # Fall back to old (<=0.9) style printing of log message time
            (_, stdout, _) = self.module.run_command(
                'zgrep -h "auter.*complete" ' + " ".join(msgs_files)
            )

            run_dates = stdout.strip().split("\n")

            last_run = " ".join(run_dates[-1].split()[0:3])

            if last_run:
                return last_run
            else:
                return None

        version = _auter_version()

        if not version:
            self.debug.append({"auter": "Auter RPM not found on this server"})
            return None

        (enabled, running) = _auter_enabled()
        ret = {
            "version": version,
            "enabled": enabled,
            "running": running,
            "last_run": _auter_last_run(),
        }

        return ret
