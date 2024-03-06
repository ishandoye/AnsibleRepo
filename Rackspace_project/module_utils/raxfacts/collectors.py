from ansible.module_utils.raxfacts.antivirus import AntiVirusFactsCollector
from ansible.module_utils.raxfacts.cluster import ClusterFactsCollector
from ansible.module_utils.raxfacts.configured_mountpoints import \
    ConfiguredMountpointsCollector
from ansible.module_utils.raxfacts.cron import CronFactsCollector
from ansible.module_utils.raxfacts.crowdstrike import CrowdstrikeFactsCollector
from ansible.module_utils.raxfacts.docker import DockerFactsCollector
from ansible.module_utils.raxfacts.endpoints import EndpointFactsCollector
from ansible.module_utils.raxfacts.hardware import HardwareFactsCollector
from ansible.module_utils.raxfacts.kubernetes import K8sFactsCollector
from ansible.module_utils.raxfacts.listening_ports import \
    ListeningPortFactsCollector
from ansible.module_utils.raxfacts.mysql import MySQLFactsCollector
from ansible.module_utils.raxfacts.nimbus import NimbusFactsCollector
from ansible.module_utils.raxfacts.oracle import OracleFactsCollector
from ansible.module_utils.raxfacts.packages import PackageFactsCollector
from ansible.module_utils.raxfacts.patching import (AuterFactsCollector,
                                                    PatchingFactsCollector)
from ansible.module_utils.raxfacts.php import PhpFactsCollector
from ansible.module_utils.raxfacts.plesk import PleskFactsCollector
from ansible.module_utils.raxfacts.process import ProcessFactsCollector
from ansible.module_utils.raxfacts.repos import RepoFactsCollector
from ansible.module_utils.raxfacts.sap import SAPFactsCollector
from ansible.module_utils.raxfacts.sar import SarFactsCollector
from ansible.module_utils.raxfacts.service import ServiceFactsCollector
from ansible.module_utils.raxfacts.setup import SetupFactsCollector
from ansible.module_utils.raxfacts.storage import StorageFactsCollector
from ansible.module_utils.raxfacts.user_group import UserGroupFactsCollector
from ansible.module_utils.raxfacts.webserver import WebServerFactsCollector

collector_classes = [
    AntiVirusFactsCollector,
    CronFactsCollector,
    ClusterFactsCollector,
    HardwareFactsCollector,
    ListeningPortFactsCollector,
    MySQLFactsCollector,
    PackageFactsCollector,
    AuterFactsCollector,
    PleskFactsCollector,
    ProcessFactsCollector,
    SarFactsCollector,
    ServiceFactsCollector,
    SetupFactsCollector,
    UserGroupFactsCollector,
    WebServerFactsCollector,
    RepoFactsCollector,
    PatchingFactsCollector,
    NimbusFactsCollector,
    StorageFactsCollector,
    DockerFactsCollector,
    K8sFactsCollector,
    PhpFactsCollector,
    OracleFactsCollector,
    SAPFactsCollector,
    ConfiguredMountpointsCollector,
    CrowdstrikeFactsCollector,
    EndpointFactsCollector
]


def get_collector_info():
    names = []
    group_map = {}
    for collector_class in [cc for cc in collector_classes if not cc.hidden]:
        names.append(collector_class.name)
        for group in collector_class.groups:
            if group not in group_map:
                group_map[group] = []
            group_map[group].append(collector_class.name)

    for key in group_map:
        group_map[key] = sorted(group_map[key])

    return sorted(names), group_map
