import socket
import sys
import xml.dom.minidom

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class ClusterFactsCollector(BaseRaxFactsCollector):

    name = 'cluster'

    def collect(self):
        cluster = None
        try:
            if self.module.get_bin_path('clustat'):
                cluster = RHCSClusterStatus(self.module).facts()
            elif self.module.get_bin_path('pcs'):
                cluster = PCSClusterStatus(self.module).facts()
        except ClusterStatus.Error:
            _, ex = sys.exc_info()[:2]
            self.debug.append({"cluster": "Error getting cluster info: %s" % ex})
        return cluster


class ClusterStatus(object):
    """
    Superclass for the cluster types
    """
    class Error(Exception):
        pass

    @staticmethod
    def _get_elements(root, final, *path):
        element = root
        for name in path:
            tmp = element.getElementsByTagName(name)
            if not tmp:
                return []
            element = tmp[0]
        return element.getElementsByTagName(final)

    def __init__(self, module, cluster_type):
        super(ClusterStatus, self).__init__()
        self._module = module
        self._type = cluster_type
        self._nodes = []
        self._services = []

    def cluster_name(self):
        """
        Get the name of the cluster (from cluster.conf)
        """
        raise NotImplementedError

    def local_node(self):
        """
        Get the name of the node we are currently connected to
        """
        raise NotImplementedError

    def nodes(self):
        """
        Get a list of all cluster nodes
        """
        return self._nodes

    def first_node(self):
        """
        Get a 'first' cluster node. Such term does not actually exists in RHCS, but we still
        need a single 'template' node to configure other nodes. As node names are (hopefully)
        unique, first node in alphabetical order should do.
        """
        return sorted([node['name'] for node in self._nodes])[0]

    def services(self):
        """
        Get all cluster services
        """
        return self._services

    def local_services(self):
        """
        Get all cluster services currently running on the local node
        """
        lnode = self.local_node()
        return [service for service in self._services if service['owner'] == lnode]

    def cluster_type(self):
        """
        Returns the type of the cluster
        """
        return self._type

    def facts(self):
        """
        Returns the facts about the cluster
        """
        return {
            'name': self.cluster_name(),
            'type': self.cluster_type(),
            'members': self.nodes(),
            'first_node': self.first_node(),
            'local_node': self.local_node(),
            'services': self.services(),
            'local_services': self.local_services(),
        }

class RHCSClusterStatus(ClusterStatus):

    MYSQL_BINARY = '/usr/(libexec|sbin)/mysqld'
    POSTGRES_BINARY = '/usr/bin/postmaster'
    REDIS_BINARY = '/usr/bin/redis-server'
    JAVA_BINARY = '/usr/bin/java'
    MEMCACHED_BINARY = 'memcached'

    def __init__(self, module):
        super(RHCSClusterStatus, self).__init__(module, 'RHCS')
        self._clustat = xml.dom.minidom.parseString(self._clustat_output()).childNodes[0]
        try:
            self._conf = xml.dom.minidom.parse('/etc/cluster/cluster.conf').childNodes[0]
        except IOError:
            raise self.Error('cannot read cluster.conf')
        self._parse_nodes()
        self._parse_services()

    def _clustat_output(self):
        clustat_bin = self._module.get_bin_path('clustat')
        if not clustat_bin:
            raise self.Error('clustat binary not found')

        rc, out, err = self._module.run_command([clustat_bin, '-x'])

        if rc != 0:
            raise self.Error('clustat returned %d, stderr: %s' % (rc, err))

        return out

    def _parse_nodes(self):
        nodes = self._clustat.getElementsByTagName('nodes')[0].getElementsByTagName('node')
        self._nodes = [{'name': node.attributes['name'].value,
                        'ip': socket.gethostbyname(node.attributes['name'].value),
                        'id': int(node.attributes['nodeid'].value[2:], 16),
                        'state': ('offline', 'online')[node.attributes['state'].value == '1'],
                        'local': node.attributes['local'].value == '1',
                        'rgmanager': node.attributes['rgmanager'].value == '1',
                        } for node in nodes]

    def _service_info(self, svc_name, owner, state):

        def re_esc(s):
            return s.replace('.', r'\.').replace('/', r'\/').replace('=', '.')

        def build_re(*args):
            return '/%s/' % '.*'.join([re_esc(a) for a in args])

        ret = {'name': svc_name, 'owner': owner, 'state': state, 'type': 'other'}
        rm = self._conf.getElementsByTagName('rm')[0]
        res = rm.getElementsByTagName('resources')[0]
        service = [x for x in rm.getElementsByTagName('service')
                   if x.attributes['name'].value == svc_name][0]

        mysqlcfg = service.getElementsByTagName('mysql')
        if mysqlcfg:
            ret['type'] = 'mysql'
            if 'config_file' in mysqlcfg[0].attributes.keys():
                cfg_file = mysqlcfg[0].attributes['config_file'].value
            else:
                srv = mysqlcfg[0].attributes['ref'].value
                cfg_file = [x.attributes['config_file'].value
                            for x in res.getElementsByTagName('mysql')
                            if x.attributes['name'].value == srv][0]
            ret['cmdline_re'] = build_re(self.MYSQL_BINARY, '--defaults-file='+cfg_file)

        postgrescfg = service.getElementsByTagName('postgres-8')
        if postgrescfg:
            ret['type'] = 'postgres'
            if 'postmaster_options' in postgrescfg[0].attributes.keys():
                pg_opts = postgrescfg[0].attributes['postmaster_options'].value
            else:
                srv = postgrescfg[0].attributes['ref'].value
                pg_opts = [x.attributes['postmaster_options'].value
                           for x in res.getElementsByTagName('postgres-8')
                           if x.attributes['name'].value == srv][0]
            ret['cmdline_re'] = build_re(self.POSTGRES_BINARY, pg_opts)

        scripts = service.getElementsByTagName('script')
        if scripts:
            if 'name' in scripts[0].attributes.keys():
                scriptname = scripts[0].attributes['name'].value
                scriptfile = scripts[0].attributes['file'].value
            else:
                scriptname = scripts[0].attributes['ref'].value
                scriptfile = [x.attributes['file'].value
                              for x in res.getElementsByTagName('script')
                              if x.attributes['name'].value == scriptname][0]
            iptag = service.getElementsByTagName('ip')[0]
            if 'address' in iptag.attributes.keys():
                ip = iptag.attributes['address'].value
            else:
                ip = iptag.attributes['ref'].value

            # Suboptimal heuristics!!!
            if 'redis' in scriptname.lower():
                ret['type'] = 'redis'
                ret['cmdline_re'] = build_re(self.REDIS_BINARY, ip+':')
            elif 'memcache' in scriptname.lower():
                ret['type'] = 'memcached'
                ret['cmdline_re'] = build_re(self.MEMCACHED_BINARY, '-l ' + ip + '( |$)')
            elif 'solr' in scriptname.lower():
                ret['type'] = 'solr'
                f = open(scriptfile)
                java_opts = [line for line in f if line.strip().startswith('JAVA_OPTIONS=')][0]
                f.close()
                java_opts = java_opts.strip().split('=', 1)[1].strip().strip('"\'')
                ret['cmdline_re'] = build_re(self.JAVA_BINARY, java_opts)

        if service.getElementsByTagName('nfsserver') or service.getElementsByTagName('nfsexport'):
            ret['type'] = 'nfs'

        ret['fs'] = []
        ret['fs_detail'] = []
        fscfg = service.getElementsByTagName('fs')
        for fs in fscfg:
            if 'mountpoint' in fs.attributes.keys():
                elem = fs
            else:
                fsref = fs.attributes['ref'].value
                elem = [x for x in res.getElementsByTagName('fs')
                        if x.attributes['name'].value == fsref][0]
            mntpoint = elem.attributes['mountpoint'].value.rstrip('/')
            detail = {'directory': mntpoint, 'device': elem.attributes['device'].value}
            for item in ['fstype', 'options']:
                if item in elem.attributes.keys():
                    detail[item] = elem.attributes[item].value

            ret['fs'].append(mntpoint)
            ret['fs_detail'].append(detail)

        return ret

    def _parse_services(self):
        self._services = []
        groups = self._clustat.getElementsByTagName('groups')

        if not groups:
            return

        groups = groups[0].getElementsByTagName('group')
        svcs = [(grp.attributes['name'].value[8:], grp.attributes['owner'].value,
                 grp.attributes['state_str'].value)
                for grp in groups
                if grp.attributes['name'].value.startswith('service:')]

        for svc, owner, state in svcs:
            self._services.append(self._service_info(svc, owner, state))

    def cluster_name(self):
        """
        Get the name of the cluster (from cluster.conf)
        """
        return self._conf.attributes['name'].value

    def local_node(self):
        """
        Get the name of the node we are currently connected to
        """
        return [node['name'] for node in self._nodes if node['local']][0]


class PCSClusterStatus(ClusterStatus):

    IGNORE_SVCS = ["cluster_lvm"]

    def __init__(self, module):
        super(PCSClusterStatus, self).__init__(module, 'PCS')
        self._local_node = self._crm_node_output().strip()
        self._clustat = xml.dom.minidom.parseString(self._crm_mon_output()).childNodes[0]
        self._config = xml.dom.minidom.parseString(self._cibadmin_output()).childNodes[0]
        self._resources = {}
        self._parse_resources()
        self._parse_nodes()
        self._parse_services()

    def _crm_node_output(self):
        crm_node_bin = self._module.get_bin_path('crm_node')
        if not crm_node_bin:
            raise self.Error('crm_node binary not found')

        rc, out, err = self._module.run_command([crm_node_bin, '-n'])

        if rc != 0:
            raise self.Error('crm_node returned %d, stderr: %s' % (rc, err))

        return out

    def _crm_mon_output(self):
        crm_mon_bin = self._module.get_bin_path('crm_mon')
        if not crm_mon_bin:
            raise self.Error('crm_mon binary not found')

        rc, out, err = self._module.run_command(
            [crm_mon_bin, '--one-shot', '--as-xml', '--inactive'])

        if rc != 0:
            raise self.Error('crm_mon returned %d, stderr: %s' % (rc, err))

        return out

    def _cibadmin_output(self):
        cibadmin_bin = self._module.get_bin_path('cibadmin')
        if not cibadmin_bin:
            raise self.Error('cibadmin binary not found')

        rc, out, err = self._module.run_command(
            [cibadmin_bin, '--xpath', '/cib/configuration', '--query']
        )
        if rc != 0:
            raise self.Error('cibadmin returned %d, stderr: %s' % (rc, err))

        return out

    def _parse_nodes(self):
        nodes = self._get_elements(self._clustat, 'node', 'nodes')
        def _node_state(node):
            if not node.attributes['online'].value == 'true':
                return 'Offline'
            if node.attributes['standby'].value == 'true':
                return 'Standby'
            if node.attributes['maintenance'].value == 'true':
                return 'Maintenance'
            return 'Online'

        self._nodes = [{
            'name': node.attributes['name'].value,
            'ip': socket.gethostbyname(node.attributes['name'].value),
            'id': int(node.attributes['id'].value),
            'state': _node_state(node),
            'status': [_node_state(node)],
            'dc': node.attributes['is_dc'].value,
            'resource_count': int(node.attributes['resources_running'].value),
            'local': node.attributes['name'].value == self._local_node,
        } for node in nodes]

    def _parse_resources(self):
        for group in self._get_elements(self._config, 'group', 'resources'):
            svc = {}
            for resource in group.getElementsByTagName('primitive'):
                res = {
                    'type': '%s::%s:%s' % (
                        resource.attributes['class'].value,
                        resource.attributes['provider'].value,
                        resource.attributes['type'].value),
                    'attributes': {}
                }
                for attr in self._get_elements(resource, 'nvpair', 'instance_attributes'):
                    res['attributes'][attr.attributes['name'].value] = attr.attributes['value'].value
                svc[resource.attributes['id'].value] = res
            self._resources[group.attributes['id'].value] = svc

    def _service_info(self, service):
        svc = {'name': service.attributes['id'].value, 'state': 'unknown',
               'type': 'other', 'fs': [], 'fs_detail': [], 'owner': 'none'}
        res_states = [
            {'attr': 'failure_ignored', 'state': 'failed (ignored)', 'cnt': 0},
            {'attr': 'failed', 'state': 'failed', 'cnt': 0},
            {'attr': 'blocked', 'state': 'blocked', 'cnt': 0},
            {'attr': 'target_role', 'value': 'Stopped', 'state': 'disabled', 'cnt': 0},
            {'attr': 'active', 'state': 'started', 'cnt': 0}
        ]
        services = {
            'ocf::heartbeat:mysql': 'mysql',
            'ocf::heartbeat:nfsserver': 'nfs',
            'ocf::heartbeat:redis': 'redis',
            'ocf::pacemaker:controld': 'cluster_lvm',
            'ocf::heartbeat:lvmlockd': 'cluster_lvm',
        }
        res_cnt = int(service.attributes['number_resources'].value)
        for res in service.getElementsByTagName('resource'):
            for state in res_states:
                if (res.attributes.get(state['attr']) and
                        res.attributes[state['attr']].value == state.get('value', 'true')):
                    state['cnt'] += 1
                    break
            if res.attributes['resource_agent'].value in services:
                svc['type'] = services[res.attributes['resource_agent'].value]
            if res.attributes['resource_agent'].value == 'ocf::heartbeat:Filesystem':
                fs_def = self._resources[service.attributes['id'].value][res.attributes['id'].value]
                svc['fs'].append(fs_def['attributes']['directory'])
                svc['fs_detail'].append(fs_def['attributes'])
            if res.attributes['nodes_running_on'].value != '0':
                svc['owner'] = res.getElementsByTagName('node')[0].attributes['name'].value
        for state in res_states:
            if state['cnt'] == res_cnt:
                svc['state'] = state['state']
                break
        else:
            for state in res_states:
                if state['cnt'] > 0:
                    svc['state'] = 'partially %s' % state['state']
                    break
        return svc

    def _parse_services(self):
        self._services = []
        groups = self._get_elements(self._clustat, 'group', 'resources')

        if not groups:
            return

        for group in groups:
            svc = self._service_info(group)
            if svc["type"] not in self.IGNORE_SVCS:
                self._services.append(self._service_info(group))

    def cluster_name(self):
        """
        Get the name of the cluster
        """
        return [x.attributes['value'].value for x in
                self._get_elements(self._config, 'nvpair', 'cluster_property_set')
                if x.attributes['name'].value == 'cluster-name'][0]

    def local_node(self):
        """
        Get the name of the node we are currently connected to
        """
        return self._local_node
