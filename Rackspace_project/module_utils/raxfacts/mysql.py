import os
import sys

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class MySQLFactsCollector(BaseRaxFactsCollector):

    name = 'mysql'
    aliases = ['mysql_facts']

    def collect(self):
        def _get_command(binary):
            """ Returns the mysql command to execute to get data. Mainly detects and uses
                plesk credentials
            """

            binary_path = self.module.get_bin_path(binary)
            try:
                fp = open('/etc/psa/.psa.shadow', 'r')
                admin_pw = fp.read()
                fp.close()
                return binary_path + ' -uadmin -p' + admin_pw
            except IOError:
                pass

            return binary_path

        mysqladmin_path = _get_command('mysqladmin')
        mysql_path = _get_command('mysql')
        debug = {}

        ret = {
            'variables': None,
            'datadir_size': None,
            'config_file_locations': None,
            'status': None,
            'replication_slave': None,
            'replication_master': None,
            'databases': None,
            'users': None,
            'version': {'major': None, 'minor': None, 'full': None, 'vendor': None},
        }

        def _get_lines(output):
            for line in output.split('\n'):
                parts = line.replace('|', '').replace("'", '').strip().split()
                try:
                    if line.startswith('***') or line.startswith('+--') or parts[0] == (
                            "Variable_name"):
                        continue

                    if len(parts) == 1:
                        yield(parts[0], None)

                    yield (parts[0], parts[1])
                except Exception:
                    pass

        def _run_command(command):

            (rc, output, stderr) = self.module.run_command(command)

            if rc != 0:
                raise Exception("Ret: %s\nstdout: %s\nstderr: %s" % (rc, output, stderr))

            return output

        def _get_val(val):
            try:
                if "." in val:
                    return float(val)
            except Exception:
                pass

            try:
                return int(val)
            except Exception:
                pass

            return val

        def _get_users():

            def _get_grant_command(user):
                user_parts = user.split('@')
                quoted_user = '"%s"@"%s"' % (user_parts[0], user_parts[1])
                return (mysql_path + (
                    r" -e 'show grants for %s\G'") % quoted_user)

            ret = {}

            output = _run_command(mysql_path + (
                r""" -e 'select concat(User, "@", Host) as user from user\G' mysql"""))
            for (_, user) in _get_lines(output):
                if user not in ret:
                    ret[user] = []

                grant_output = _run_command(_get_grant_command(user))
                for line in [
                        line for line in grant_output.split('\n') if not line.startswith("***")]:
                    grant = "".join(line.split(":")[1:])
                    grant = grant.split("IDENTIFIED BY")[0].strip()
                    if grant:
                        ret[user].append(grant.lstrip())

            return ret

        def _get_databases():
            ret = []

            output = _run_command(mysql_path + r" -e 'show databases\G'")
            for (_, database) in _get_lines(output):
                ret.append(database)

            return ret

        def _get_replication(role):
            ret = {}

            output = _run_command(mysql_path + r" -e 'show %s status\G'" % role)

            for (key, value) in _get_lines(output):
                ret[key] = _get_val(value)

            return ret or None

        def _get_status():
            ret = {}

            output = _run_command(mysqladmin_path + " extended-status")

            for (key, value) in _get_lines(output):
                ret[key] = _get_val(value)

            return ret or None

        def _get_variables():
            ret = {}

            output = _run_command(mysqladmin_path + " variables")

            for (variable, value) in _get_lines(output):
                if not variable or not value:
                    continue

                ret[variable] = _get_val(value)

            return ret or None

        def _get_datadir_size(datadir):
            if not datadir:
                return None

            total_size = 0
            for dirpath, _, filenames in os.walk(datadir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)

            return total_size

        def _get_config_files():
            output = _run_command(mysql_path + " --help").split('\n')

            for lineno, line in enumerate(output):
                if line.startswith("Default options are read from the following"):
                    return output[lineno + 1].split()

            return None

        def _get_engine_stats():
            query = ('SELECT ENGINE,SUM(DATA_LENGTH+INDEX_LENGTH),COUNT(ENGINE),SUM(DATA_LENGTH),'
                     'SUM(INDEX_LENGTH) FROM information_schema.TABLES WHERE ENGINE IS NOT NULL '
                     'AND TABLE_SCHEMA NOT IN ("information_schema", "performance_schema")'
                     'GROUP BY ENGINE ORDER BY ENGINE ASC;')
            output = _run_command(mysql_path + " -sNe '" + query + "'")
            output_lines = output.strip().split('\n')
            ret = {}

            for line in output_lines:
                vals = line.strip().split('\t')
                ret[vals[0]] = {'total_size': vals[1], 'table_count': vals[2], 'data_size': vals[3],
                                'index_size': vals[4]}

            return ret

        if mysqladmin_path:
            try:
                ret['variables'] = _get_variables()
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['variables'] = None
                debug['variables'] = str(ex)

            try:
                ret['datadir_size'] = _get_datadir_size(
                    ret['variables'].get('datadir'))
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['datadir_size'] = None
                debug['datadir_size'] = str(ex)

            try:
                ret['status'] = _get_status()
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['status'] = None
                debug['status'] = str(ex)

            try:
                full_version = ret['variables'].get('version').split('.')
                comment = ret['variables'].get('version_comment').lower()
                vendors = ('mysql', 'mariadb', 'percona')
                vendor = 'unknown'
                for v in vendors:
                    if v in comment:
                        vendor = v
                # Lets check if a vendor appears in the "full_version" string if "vendor" is
                # currently "unknown"
                if vendor == 'unknown':
                    for v in vendors:
                        if v in ret['variables'].get('version').lower():
                            vendor = v
                ret['version']['full'] = '.'.join(full_version)
                ret['version']['major'] = int(full_version[0])
                ret['version']['minor'] = int(full_version[1])
                ret['version']['release'] = full_version[2].split('-')[0]
                ret['version']['vendor'] = vendor
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['version'] = {'major': None, 'minor': None, 'full': None, 'vendor': None}
                debug['status'] = str(ex)
        else:
            debug['mysqladmin'] = "Command mysqladmin does not exist"

        if mysql_path:
            try:
                ret['databases'] = _get_databases()
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['databases'] = None
                debug['databases'] = str(ex)

            try:
                ret['users'] = _get_users()
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['users'] = None
                debug['users'] = str(ex)

            try:
                ret['config_file_locations'] = _get_config_files()
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['config_file_locations'] = None
                debug['config_file_locations'] = str(ex)

            try:
                ret['replication_slave'] = _get_replication('slave')
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['replication_slave'] = None
                debug['replication_slave'] = str(ex)

            try:
                ret['replication_master'] = _get_replication('master')
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['replication_master'] = None
                debug['replication_slave'] = str(ex)

            try:
                ret['engine_stats'] = _get_engine_stats()
            except Exception:
                _, ex = sys.exc_info()[:2]
                ret['engine_stats'] = None
                debug['engine_stats'] = str(ex)
        else:
            debug['mysql'] = "Command mysql does not exist"

        if debug:
            self.debug.append({'mysql': debug})

        return ret
