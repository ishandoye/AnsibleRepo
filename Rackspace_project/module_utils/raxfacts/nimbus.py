import os

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector
from ansible.module_utils.monitoring.nimbus.config import NimbusConfig
from ansible.module_utils.six import iteritems


class NimbusFactsCollector(BaseRaxFactsCollector):

    name = 'nimbus'

    def read_cfg_file(self, filename):
        if os.path.exists(filename):
            cfg = NimbusConfig()
            cfg.parse(filename)
            return cfg.facts()
        return None

    def _get_health_facts(self, robot_facts):
        if not robot_facts:
            return None
        facts = {
            'robotname_correct': False,
            'robotip_alias_correct': False,
            'os_user1_correct': False,
        }
        account_number = self.metadata.get('rs_customer')
        device_number = self.metadata.get('rs_server')
        public_ip = self.metadata.get('rs_login_ip')
        robotname = robot_facts.get('robotname')
        robotip_alias = robot_facts.get('robotip_alias')
        os_user1 = robot_facts.get('os_user1')

        if robotname and account_number and device_number:
            facts['robotname_correct'] = robotname == '%s-%s' % (
                account_number,
                device_number,
            )
        if robotip_alias and public_ip:
            facts['robotip_alias_correct'] = robotip_alias == public_ip
        if os_user1 and account_number:
            facts['os_user1_correct'] = os_user1 == account_number
        return facts

    def _get_robot_facts(self, robot_cfg):
        if not robot_cfg:
            return None
        controller = robot_cfg.get('controller', {})
        keys = [
            'domain',
            'hub',
            'hubip',
            'hubport',
            'hubrobotname',
            'secondary_domain',
            'secondary_hub',
            'secondary_hubip',
            'secondary_hubport',
            'secondary_hubrobotname',
            'os_user1',
            'robotname',
            'robotip_alias'
        ]
        return dict([(key, controller.get(key)) for key in keys])

    def _get_probe_versions(self, nim_version_cfg):
        if not nim_version_cfg:
            return None
        facts = {}
        keys = {
            'robot_update': 'robot_update',
            'cdm': 'cdm',
            'processes': 'processes',
            'logmon': 'logmon',
            'snmptd': 'snmptd',
            'mysql': 'database',
            'cluster': 'cluster',
            'oracle': 'oracle',
        }
        for probe_friendly, probe_name in keys.items():
            version = nim_version_cfg.get(probe_name, {}).get("version")
            if version:
                facts[probe_friendly] = version
        return facts

    def _get_cdm_facts(self, cdm_cfg):
        if not cdm_cfg:
            return None
        cpu_alarms = {}
        cpu_alarm_keys = ['alarm', 'specific']
        for key in [k for k in cpu_alarm_keys if cdm_cfg['cpu'][k].get('active') != 'no']:
            for k, v in [
                item
                for item in iteritems(cdm_cfg['cpu'][key])
                if isinstance(item[1], dict) and item[1].get('active') == 'yes'
            ]:
                units = ''
                if key == 'alarm':
                    units = '%'
                cpu_alarms['cpu_%s' % k] = ('%s %s' % (v['threshold'], units)).rstrip()

        mem_alarms = {}
        for k, v in [
            item for item in iteritems(cdm_cfg['memory']['alarm'])
            if isinstance(item[1], dict) and item[1].get('active') == 'yes'
        ]:
            units = '%'
            if 'paging' in k:
                if cdm_cfg['setup']['paging_in_kilobytes'] == 'yes':
                    units = 'KB/s'
                else:
                    units = 'pages/s'
            mem_alarms[k.replace(' ', '_')] = '%s %s' % (v['threshold'], units)

        disk_alarms = []
        disk_configs = cdm_cfg['disk']['alarm']['fixed']
        for key, config in [
            item
            for item in iteritems(disk_configs)
            if item[1].get('active') == 'yes'
        ]:
            alarms = {}
            for k, v in [
                item
                for item in iteritems(config)
                if isinstance(item[1], dict) and item[1].get('active') == 'yes'
            ]:
                if k == 'missing':
                    alarms['disk_missing'] = True
                else:
                    units = 'MB'
                    if 'inode' in k:
                        if 'inode_percent' in config and config['inode_percent'] == 'yes':
                            units = '%'
                    elif 'delta' in k:
                        if 'delta_percent' in config and config['delta_percent'] == 'yes':
                            units = '%'
                    elif 'percent' in config and config['percent'] == 'yes':
                        units = '%'
                    alarms['disk_%s' % k] = '%s %s' % (v['threshold'], units)
            if alarms:
                alarms['mount_point'] = key.replace('#', '/')
                disk_alarms.append(alarms)

        facts = {
            'cpu_alarms': cpu_alarms,
            'disk_alarms': disk_alarms,
            'memory_alarms': mem_alarms,
        }
        return facts

    def collect(self):
        if os.path.exists('/opt/nimsoft'):
            base_path = '/opt/nimsoft'
        elif os.path.exists('/opt/nimbus'):
            base_path = '/opt/nimbus'
        else:
            return None

        robot_facts = self._get_robot_facts(
            self.read_cfg_file('%s/robot/robot.cfg' % base_path)
        )
        health_facts = self._get_health_facts(robot_facts)
        probe_versions = self._get_probe_versions(
            self.read_cfg_file('%s/robot/pkg/inst/installed.pkg' % base_path)
        )
        cdm_facts = self._get_cdm_facts(
            self.read_cfg_file('%s/probes/system/cdm/cdm.cfg' % base_path)
        )
        facts = {
            'cdm': cdm_facts,
            'robot': robot_facts,
            'health': health_facts,
            'versions': probe_versions,
        }
        return facts
