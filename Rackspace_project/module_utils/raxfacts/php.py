# Standard Library
import os
from itertools import chain, takewhile

# Third Party
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class PhpFactsCollector(BaseRaxFactsCollector):

    name = "php"

    def __init__(self, *args, **kwargs):
        super(PhpFactsCollector, self).__init__(*args, **kwargs)
        self.pgrep_path = self.module.get_bin_path("pgrep")
        self.rpm_path = self.module.get_bin_path("rpm")
        self.php_path = None
        self.fpm_path = None
        self.php_m_stdout = None
        self.php_m_stderr = None

    def get_php_cli_path(self):
        if self.php_path is None:
            php = self.module.get_bin_path("php")
            self.php_path = os.path.realpath(php) if php else ""
        return self.php_path or None

    def get_php_m_output(self):
        if self.php_m_stdout is None:
            _, stdout, stderr = self.module.run_command([self.php_path, "-m"])
            self.php_m_stdout = stdout.splitlines()
            self.php_m_stderr = stderr.splitlines()
        return self.php_m_stdout, self.php_m_stderr

    def get_running_fpm_path(self):
        if not self.pgrep_path:
            return None
        if self.fpm_path is None:
            self.fpm_path = ""
            pid_args = [self.pgrep_path, "-f", "php-fpm"]
            _, stdout, _ = self.module.run_command(pid_args)
            # Gets the first line of output, if there is one
            pid = next(iter(stdout.splitlines()), None)
            if pid:
                self.fpm_path = os.path.realpath(os.path.join("/proc", pid, "exe"))
        return self.fpm_path or None

    def get_php_version(self):
        args = [self.php_path, "-v"]
        _, stdout, _ = self.module.run_command(args)
        # This picks the first line of the output, and splits out the second item on that line
        # e.g. From
        # PHP 7.4.3 (cli) (built: Mar  2 2022 15:36:52) ( NTS )
        # it will return '7.4.3'
        version = next(iter(stdout.splitlines()), "").partition(" ")[2].partition(" ")[0]
        return (version, ".".join(version.split(".")[:2]))

    def get_php_warnings(self):
        # get_php_m_output returns a tuple (stdout, stderr) which are lists (from .splitline())
        # itertools.chain glues the lists together into a single iterable
        return [line for line in chain(*self.get_php_m_output()) if "PHP Warning:" in line]

    def get_php_modules(self):
        return [
            m
            # get_php_m_output returns a tuple (stdout, stderr) which are lists (from .splitline())
            # itertools.takewhile stops reading from the iterable when it sees 'Zend Modules'
            for m in takewhile(lambda line: "Zend Modules" not in line, self.get_php_m_output()[0])
            if m and "Modules" not in m
        ]

    def get_php_pkg_source(self):
        source = "unknown"
        if self.rpm_path:
            args = [
                self.rpm_path,
                "-qf",
                "--queryformat",
                "%{name}-%{version}-%{release}.%{arch} %{vendor}",
                self.php_path,
            ]
            rc, stdout, _ = self.module.run_command(args)
            if rc == 0 and stdout:
                if ".ius." in stdout:
                    source = "ius"
                elif ".remi." in stdout:
                    source = "remi"
                elif ".art." in stdout:
                    source = "atomic"
                elif "CentOS" in stdout:
                    source = "centos"
                elif "Red Hat" in stdout:
                    source = "redhat"
                elif "SUSE" in stdout:
                    source = "suse"
                elif "Webtatic" in stdout:
                    source = "webtatic"
                elif "ScienceLogic" in stdout:
                    source = "sciencelogic"
                elif "(none)" not in stdout:
                    vendor = " ".join(stdout.split()[1:]).lower()
                    source = vendor
        return source

    def get_php_pkg_repo(self):
        repo = "unknown"
        if self.rpm_path:
            args = [self.rpm_path, "-qf", self.php_path]
            rc, stdout, _ = self.module.run_command(args)
            if rc == 0 and stdout:
                yum_path = self.module.get_bin_path("yum")
                if yum_path:
                    args = [
                        yum_path,
                        "--setopt=exit_on_lock=1",
                        "info",
                        "--disablerepo=*",
                        stdout.strip()
                    ]
                    _, stdout, _ = self.module.run_command(args)
                    for rname in [
                        line for line in stdout.splitlines() if line.startswith("From repo")
                    ]:
                        repo = rname.partition(":")[2].strip()
        return repo

    def fpm_config_has_errors(self):
        if not self.get_running_fpm_path():
            return False
        args = [self.get_running_fpm_path(), "-t"]
        return bool(self.module.run_command(args)[0])

    def collect(self):
        # Ensure we have full path to actual binary
        if not self.get_php_cli_path():
            return None

        php_facts = {}
        full_version, major_version = self.get_php_version()
        php_facts["php_detected_path"] = self.php_path
        php_facts["php_version_full"] = full_version
        php_facts["php_version_major"] = major_version
        php_facts["php_enabled_modules"] = self.get_php_modules()
        php_facts["php_warnings_detected"] = bool(self.get_php_warnings())
        php_facts["php_pkg_source"] = self.get_php_pkg_source()
        php_facts["php_pkg_repo"] = self.get_php_pkg_repo()

        # FPM Checks
        php_facts["fpm_detected_path"] = self.get_running_fpm_path()
        php_facts["fpm_running"] = bool(self.get_running_fpm_path())
        php_facts["fpm_config_has_errors"] = self.fpm_config_has_errors()

        return php_facts
