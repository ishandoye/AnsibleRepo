from datetime import datetime

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class PackageFactsCollector(BaseRaxFactsCollector):

    name = "packages"
    timeout = 600

    def collect(self):
        def _rpm_package_list():
            packages = []
            pkg_mgr = None
            try:
                import yum

                pkg_mgr = "yum"

                base = yum.YumBase()
                base.preconf.debuglevel = 0
                base.preconf.errorlevel = 0
                packages = list(base.rpmdb)
            except ImportError:
                try:
                    import dnf

                    pkg_mgr = "dnf"
                    base = dnf.Base()
                    base.conf.debuglevel = 0
                    base.conf.errorlevel = 0
                    packages = list(dnf.sack._rpmdb_sack(base).query())
                except ImportError:
                    pass
            if not pkg_mgr:
                return {}

            if not packages:
                return {}

            ret = []
            for package in packages:
                installtime = datetime.utcfromtimestamp(package.installtime).isoformat()
                if hasattr(package, "from_repo"):
                    installed_from = package.from_repo
                else:
                    installed_from = package.ui_from_repo.replace("@", "")
                ret.append(
                    {
                        "name": package.name,
                        "architecture": package.arch,
                        "source": "rpm",
                        "epoch": None if package.epoch in ["0", 0] else package.epoch,
                        "version": package.version,
                        "release": package.release,
                        "installtime": "%s%s" % (installtime, "+00:00"),
                        "installed_from": installed_from,
                    }
                )
            return ret

        def _deb_package_list():
            def _get_epoch_version(version):
                try:
                    (epoch, version) = version.split(":")
                    return (epoch, version)
                except ValueError:
                    return (None, version)

            dpkg_path = self.module.get_bin_path("dpkg-query")
            if not dpkg_path:
                return None

            (rc, stdout, _) = self.module.run_command(
                dpkg_path + " -f '${binary:Package}||${version}||${Architecture}\n' -W"
            )

            if rc != 0:
                return None

            ret = []
            for name, version, arch in [
                line.split("||") for line in stdout.split("\n") if "||" in line
            ]:
                (epoch, version) = _get_epoch_version(version)
                ret.append(
                    {
                        "name": name,
                        "architecture": arch,
                        "source": "apt",
                        "epoch": epoch,
                        "version": version,
                    }
                )
            return ret

        results = []

        packages = _rpm_package_list()
        if packages:
            results += packages

        packages = _deb_package_list()
        if packages:
            results += packages

        if not results:
            results = None
            self.debug.append(
                {"packages": "Unsupported platform - only DEB and RPM is supported"}
            )

        return results
