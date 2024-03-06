import os
import re

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class RepoFactsCollector(BaseRaxFactsCollector):

    name = "repositories"

    def collect(self):
        def _get_apt_repositories():

            ret = []

            def _list_source_files():
                """Generate a list of valid apt source files"""
                file_list = []

                apt_config_path = self.module.get_bin_path("apt-config")

                if not apt_config_path:
                    return file_list

                cmd_args = [
                    apt_config_path,
                    "shell",
                    "S_LIST",
                    "Dir::Etc::sourcelist/f",
                    "S_PARTS",
                    "Dir::Etc::sourceparts/d",
                ]

                _, stdout, _ = self.module.run_command(cmd_args)

                if stdout:
                    match = re.findall("S_LIST='(.+)'", stdout)
                    if match and os.path.isfile(match[0]):
                        file_list.append(match[0])

                    match = re.findall("S_PARTS='(.+)'", stdout)
                    if match and os.path.isdir(match[0]):
                        source_parts = match[0]
                        for item in os.listdir(source_parts):
                            if item.endswith(".list"):
                                file_list.append(os.path.join(source_parts, item))

                return file_list

            def _parse_source_file(filename):
                """From input path to source .list file, generate list of repository dicts"""
                sources = []
                try:
                    fp = open(filename, "r")
                    newline = re.compile("\n")
                    apt_arch = re.compile(r"[\(\[].*?[\)\]]")
                    for source in fp:
                        # Removing in-line comments and trailing whitespace
                        intermediate_source = source.split("#", 1)[0].rstrip()
                        # Removing untrustworthy [arch] entries by matching the brackets
                        cleaned_source = re.sub(apt_arch, "", intermediate_source)
                        if cleaned_source and not re.match(newline, cleaned_source):
                            split_source = cleaned_source.split()
                            if "deb" in split_source[0]:
                                uri = split_source[1]
                                repo_type = split_source[0]
                                suite = split_source[2]
                                components = split_source[3:]

                                repo = {
                                    "id": None,
                                    "name": None,
                                    "uri": uri,
                                    "components": components,
                                    "architectures": [None],
                                    "suite": suite,
                                    "file": filename,
                                    "type": repo_type,
                                }
                                sources.append(repo)
                    fp.close()
                except IOError:
                    pass

                return sources

            for i in _list_source_files():
                try:
                    ret += _parse_source_file(i)
                except Exception:
                    pass

            return ret

        def _get_yum_repositories():
            import yum  # pylint: disable=import-error
            import logging

            # Silencing the "Loaded Plugins" output
            logger = logging.getLogger("yum.verbose.YumPlugins")
            logger.setLevel(logging.CRITICAL)
            yb = None
            try:
                # Yum setup
                yb = yum.YumBase()

                ret = []

                for repository in yb.repos.listEnabled():
                    basearch = repository.yumvar.get("basearch")
                    if repository.baseurl:
                        uri = repository.baseurl[0]
                    else:
                        uri = repository.mirrorlist
                    repo = {
                        "id": repository.id,
                        "name": repository.name,
                        "uri": uri,
                        "components": [],
                        "architectures": [basearch],
                        "suite": None,
                        "file": repository.repofile,
                        "type": "rpm",
                    }
                    ret.append(repo)
            finally:
                if yb:
                    yb.close()
                    yb.closeRpmDB()

            return ret

        def _get_dnf_repositories():
            import dnf  # pylint: disable=import-error

            base = None
            try:
                base = dnf.Base()
                base.conf.debuglevel = 0
                base.conf.errorlevel = 0
                base.conf.read()
                base.conf.substitutions.update_from_etc(installroot="/")
                base.read_all_repos()
                ret = []
                basearch = base.conf.substitutions["basearch"]
                for repository in base.repos.iter_enabled():
                    if repository.baseurl:
                        uri = repository.baseurl[0]
                    else:
                        uri = repository.mirrorlist
                    repo = {
                        "id": repository.id,
                        "name": repository.name,
                        "uri": uri,
                        "components": [],
                        "architectures": [basearch],
                        "suite": None,
                        "file": repository.repofile,
                        "type": "rpm",
                    }
                    ret.append(repo)
            finally:
                if base:
                    base.close()
            return ret

        try:
            ret = _get_yum_repositories()
        except Exception:
            ret = None

        if ret is None:
            try:
                ret = _get_dnf_repositories()
            except Exception:
                ret = None

        if ret is None:
            try:
                ret = _get_apt_repositories()
            except Exception:
                ret = None

        return ret
