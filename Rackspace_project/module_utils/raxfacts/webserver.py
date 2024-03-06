import glob
import os
import re

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class WebServerFactsCollector(BaseRaxFactsCollector):

    name = 'webservers'

    def collect(self):
        facts = {}
        collector = ApacheFactsCollector(self.module)
        apache_facts = collector.collect()
        if apache_facts:
            facts['apache'] = apache_facts
            self.debug.extend(collector.debug)

        collector = NginxFactsCollector(self.module)
        nginx_facts = collector.collect()
        if nginx_facts:
            facts['nginx'] = nginx_facts
            self.debug.extend(collector.debug)

        return facts


def _strip_line(path, remove=None):
    """ Removes any trailing semicolons, and all quotes from a string """
    if remove is None:
        remove = ['"', "'", ';']
    for c in remove:
        if c in path:
            path = path.replace(c, '')

    return path


def _get_includes_line(line, parent, root):
    """ Reads a config line, starting with 'include', and returns a list of
        files this include corresponds to. Expands relative paths, unglobs globs etc.
    """
    path = _strip_line(line.split()[1])
    orig_path = path
    included_from_dir = os.path.dirname(parent)

    if not os.path.isabs(path):
        """ Path is relative - first check if path is relative to 'current directory' """
        path = os.path.join(included_from_dir, _strip_line(path))
        if not os.path.exists(os.path.dirname(path)) or not os.path.isfile(path):
            """ If not, it might be relative to the root """
            path = os.path.join(root, orig_path)

    """ This covers things like: Include conf.d/  or just: Include conf.d
        Both reprihensible, but legal. Add an asterisk so we can globglob it.
    """
    if os.path.isdir(path):
        path = path.rstrip('/') + "/*"

    return glob.glob(path) or []


def _get_config_test(module, path):
    (rc, out, stderr) = module.run_command(path + ' -t')
    if rc == 0:
        return {'valid': True, 'msg': None}
    else:
        return {'valid': False, 'msg': out + stderr}


class ApacheFactsCollector(BaseRaxFactsCollector):

    name = 'apache'

    def _get_full_path(self, path, root, parent=None):
        """ Returns a potentially relative path and returns an absolute one either relative to
            parent or root, whichever exists in that order
        """

        if path is None:
            return None

        if os.path.isabs(path) and os.path.exists(path):
            return path

        if parent:
            if os.path.isfile(parent):
                parent = os.path.dirname(parent)
            candidate_path = os.path.join(parent, path)
            if os.path.isabs(candidate_path) and os.path.exists(candidate_path):
                return candidate_path

        candidate_path = os.path.join(root, path)
        if os.path.isabs(candidate_path) and os.path.exists(candidate_path):
            return candidate_path

        return path

    def _set_apache(self, compile_settings, apachectl_path):
        a_ret = {}

        def _get_conf_key(key):
            for line in compile_settings.split('\n'):
                if key in line:
                    try:
                        return _strip_line(line.split()[1].split('=')[1])
                    except IndexError:
                        pass
            return None

        def _replace_var(line):
            """ Checks the line to see whether there's an environment variable used, if so,
                    replace it if we can with what we've found from envvars earlier
            """
            search = re.search(r'(.*)(\$\{.*\})(.*)', line)
            if not search or not a_ret['envvars']:
                return line

            ret = ""
            for segment in search.groups():
                if segment.startswith('$'):
                    var_name = _strip_line(segment, ['$', '{', '}'])
                    segment = a_ret['envvars'].get(var_name, segment)

                ret += segment

            return ret

        def _get_all_config(config_file=None, parent_file=None):
            if config_file is None:
                config_file = a_ret['config_file']

            if parent_file is None:
                parent_file = config_file

            ret = ['--NEWFILE-- ' + config_file]

            config_data = open(config_file, 'r').readlines()
            for line in [line.strip() for line in config_data]:
                if line.startswith('#'):
                    continue

                line = line.split('#')[0]
                if line.lower().startswith('include'):
                    includes = _get_includes_line(
                        line, config_file, a_ret['httpd_root'])
                    for include in includes:
                        try:
                            ret += _get_all_config(include, parent_file=config_file)
                        except IOError:
                            pass
                elif line:
                    ret.append(_replace_var(line))

            ret.append('--NEWFILE-- ' + parent_file)

            return ret

        def _get_envvars():
            """ On Ubuntu, the init script sources /etc/apache2/envvars which defines variables
                    which are used throughout the configs. Make an attempt at expanding these if
                    possible using these variables
            """
            ret = {}
            try:
                if os.path.isfile(os.path.join(a_ret['httpd_root'], 'envvars')):
                    command = "/bin/bash -x /etc/apache2/envvars"
                    (rc, out, stderr) = self.module.run_command(command)
                    out += stderr
                    if rc != 0 or not out:
                        return None

                    for line in [line for line in out.split('\n') if re.match(
                            r'.*export.*=.*', line)]:
                        lp = line.split('=')
                        ret[lp[0].split()[2]] = lp[1]

            except IOError:
                return None

            return ret

        def _set_envvar_overrides():
            """ Apache is compiled with defaults, but on certain
                platforms, this can be overridden through environment vars which
                the init script reads (Ubuntu 14.04 for example).
            """
            if a_ret['envvars'] is None:
                return None

            try:
                a_ret['pid_file'] = a_ret['envvars']['APACHE_PID_FILE']
            except KeyError:
                pass

        def _fixup_missing_defaults(vhost):
            """ For things which aren't explicit in the vhost, fit in things inherited from
                    the global scope where applicable.
            """
            if not vhost.get('serveradmin', None):
                vhost['serveradmin'] = a_ret.get('serveradmin', None)

            if not vhost.get('access_logs', []):
                vhost['access_logs'] = a_ret.get('access_logs', [])

            if not vhost.get('error_logs', []):
                vhost['error_logs'] = a_ret.get(
                    'error_logs', None) or [a_ret.get('default_error_log')]

            if not vhost.get('accessfilename', None):
                vhost['accessfilename'] = a_ret.get(
                    'accessfilename', None)

            if not vhost.get('documentroot', None):
                vhost['documentroot'] = a_ret.get('documentroot', None)

            return vhost

        def _check_ignore_block(line):
            """ Some sections should be ignored, if they're conditional on a module being
                loaded. Since blocks can be nested, we keep a counter, and this returns the
                value this counter should be incremented by.

                Modules can be referenced either by their alias (alias_module) or their file name
                (mod_alias.(so|c)) - so we handle this.
            """
            if "ifmodule" not in line.lower():
                return 0

            module_name = line.replace('>', '').strip().split()[1]
            if "." in module_name:
                module_name = module_name.split('.')[0]

            for module in a_ret['loaded_modules']:
                """ Modules can have the suffix .so or .c, and it's irrelevant, so we strip it """
                mod_path_noext = os.path.splitext(
                    os.path.basename(module['module_path']))[0]
                if module_name in (module['module_name'], mod_path_noext):
                    return 0

            return 1

        def _get_vhost_stanza(global_vars=False, line=None):
            ret = {
                'documentroot': None,
                'access_logs': [],
                'error_logs': [],
                'accessfilename': None,
                'ssl': False,
            }

            if line is not None:
                ret['listen'] = _strip_line(
                    line, ['<', '>']).split()[1:]

            if not global_vars:
                ret['server_name'] = None
                ret['aliases'] = []
                ret['transferlogs'] = []

            return ret

        def _get_vhosts():
            lines = _get_all_config()
            ret = []
            in_vhost_block = False
            cur_vhost = None
            """ Indicates the depth of the scope we're in
                (<Directory> <FilesMatch> and that sort of stuff)
            """
            open_sections = 0

            """ If we encounter an ifmodule block for a module which isn't loaded, ignore """
            ignored_sections = 0

            current_file = None

            """ 'islist' indicates that the found value will be .append():ed to the json_kw key
                'aslist' indicates that there are multiple values on the line, such as with
                ServerAlias alias1.com alias2.com
                'ispath' indicates that the value is a path which needs to be checked for relativism

                Below this list is looped over for each line, and when apache_kw matches the
                beginning of a line, the value of that line is added to the corresponding dict under
                the json_kw key.
            """
            std_keywords_global = [
                {'apache_kw': 'startservers', 'json_kw': 'startservers'},
                {'apache_kw': 'minspareservers', 'json_kw': 'minspareservers'},
                {'apache_kw': 'maxspareservers', 'json_kw': 'maxspareservers'},
                {'apache_kw': 'minsparethreads', 'json_kw': 'minsparethreads'},
                {'apache_kw': 'maxsparethreads', 'json_kw': 'maxsparethreads'},
                {'apache_kw': 'startthreads', 'json_kw': 'startthreads'},
                {'apache_kw': 'threadsperchild', 'json_kw': 'threadsperchild'},
                {'apache_kw': 'threadlimit', 'json_kw': 'threadlimit'},
                {'apache_kw': 'maxclients', 'json_kw': 'maxclients'},
                {'apache_kw': 'serverlimit', 'json_kw': 'serverlimit'},
                {'apache_kw': 'maxrequestworkers', 'json_kw': 'maxrequestworkers'},
                {'apache_kw': 'maxrequestsperchild', 'json_kw': 'maxrequestsperchild'},
                {'apache_kw': 'maxconnectionsperchild',
                    'json_kw': 'maxconnectionsperchild'},
                {'apache_kw': 'listen ', 'json_kw': 'ports', 'islist': True},
                {'apache_kw': 'serveradmin', 'json_kw': 'serveradmin'},
                {'apache_kw': 'customlog', 'json_kw': 'access_logs',
                    'islist': True, 'ispath': True},
                {'apache_kw': 'errorlog', 'json_kw': 'error_logs',
                    'islist': True, 'ispath': True},
                {'apache_kw': 'globallog', 'json_kw': 'globallog',
                    'islist': True, 'ispath': True},
                {'apache_kw': 'accessfilename', 'json_kw': 'accessfilename'},
                {'apache_kw': 'documentroot', 'json_kw': 'documentroot', 'ispath': True},
                {'apache_kw': 'user ', 'json_kw': 'user'},
                {'apache_kw': 'group ', 'json_kw': 'group'},

            ]
            std_keywords_vhost = [
                {'apache_kw': 'documentroot', 'json_kw': 'documentroot', 'ispath': True},
                {'apache_kw': 'serveradmin', 'json_kw': 'serveradmin'},
                {'apache_kw': 'sslcertificatefile', 'json_kw': 'ssl_certificate',
                    'ispath': True},
                {'apache_kw': 'sslcertificatekeyfile', 'json_kw': 'ssl_key',
                    'ispath': True},
                {'apache_kw': 'sslcertificatechainfile', 'json_kw': 'ssl_chain',
                    'ispath': True},
                {'apache_kw': 'sslcacertificatepath', 'json_kw': 'ssl_ca_path',
                    'ispath': True},
                {'apache_kw': 'sslcacertificatefile', 'json_kw': 'ssl_ca_file',
                    'ispath': True},
                {'apache_kw': 'errorlog', 'json_kw': 'error_logs', 'islist': True,
                    'ispath': True},
                {'apache_kw': 'customlog', 'json_kw': 'access_logs',
                    'islist': True, 'ispath': True},
                {'apache_kw': 'accessfilename', 'json_kw': 'accessfilename'},
                {'apache_kw': 'servername', 'json_kw': 'server_name'},
                {'apache_kw': 'sslciphersuite', 'json_kw': 'ssl_ciphers'},
                {'apache_kw': 'transferlog', 'json_kw': 'transferlogs',
                    'islist': True, 'ispath': True},
                {'apache_kw': 'sslprotocol', 'json_kw': 'ssl_protocols', 'aslist': True},
                {'apache_kw': 'serveralias', 'json_kw': 'aliases', 'aslist': True},
                # {'apache_kw': '', 'json_kw': ''},

            ]

            for line in [_strip_line(line) for line in lines]:
                lowerline = line.lower()

                if line.startswith('--NEWFILE--'):
                    current_file = line.split()[1]
                    continue

                if re.match(r"<\s?/.*>", line):
                    open_sections -= 1
                    if in_vhost_block and "virtualhost" in lowerline:
                        in_vhost_block = False
                        ret.append(cur_vhost)
                    if ignored_sections > 0 and "ifmodule" in lowerline:
                        ignored_sections -= 1

                elif re.match(r"<.*>", line):
                    open_sections += 1

                    ignored_sections += _check_ignore_block(line)
                    if ignored_sections > 0:
                        continue

                    if "virtualhost" in lowerline:
                        in_vhost_block = True
                        cur_vhost = _get_vhost_stanza(line=line)
                        cur_vhost['config_file'] = current_file

                """ These aren't vhost-specific, but we'll populate them here as we don't want
                    to iterate over the files more than once
                """
                if not in_vhost_block:

                    for kw in std_keywords_global:
                        if lowerline.startswith(kw['apache_kw']):
                            if 'aslist' in kw:
                                value = line.split()[1:]
                            elif 'aslist' not in kw and 'ispath' in kw:
                                value = self._get_full_path(_strip_line(line.split()[1]),
                                                            a_ret['httpd_root'])
                            else:
                                value = line.split()[1]

                            if 'islist' in kw:
                                a_ret[kw['json_kw']].append(value)
                            else:
                                a_ret[kw['json_kw']] = value

                    if lowerline.startswith("loadmodule"):
                        a_ret['loaded_modules'].append({'module_name': line.split()[1],
                                                        'module_path': line.split()[2]})

                """ Start vhost stuff """
                if in_vhost_block:

                    for kw in std_keywords_vhost:
                        if lowerline.startswith(kw['apache_kw']):
                            if 'aslist' in kw:
                                value = line.split()[1:]
                            elif 'aslist' not in kw and 'ispath' in kw:
                                value = self._get_full_path(_strip_line(line.split()[1]),
                                                            a_ret['httpd_root'])
                            else:
                                value = line.split()[1]

                            if 'islist' in kw:
                                cur_vhost[kw['json_kw']].append(value)
                            else:
                                cur_vhost[kw['json_kw']] = value

                    if lowerline.startswith("sslengine") and line.lower().strip().endswith('on'):
                        cur_vhost['ssl'] = True

            return ret

        """ Everything that can be in a virtualhost, can also be in the main config """
        for k, v in _get_vhost_stanza(global_vars=True).items():
            a_ret[k] = v
        root = _get_conf_key('HTTPD_ROOT')
        a_ret['httpd_root'] = root
        a_ret['config_file'] = self._get_full_path(_get_conf_key('SERVER_CONFIG_FILE'), root)
        a_ret['envvars'] = _get_envvars()
        a_ret['ports'] = []
        a_ret['loaded_modules'] = []
        a_ret['vhosts'] = []
        vhosts = _get_vhosts()
        a_ret['pid_file'] = self._get_full_path(_get_conf_key('DEFAULT_PIDLOG'), root)
        a_ret['default_error_log'] = self._get_full_path(_get_conf_key('DEFAULT_ERRORLOG'), root)
        a_ret['config_test'] = _get_config_test(self.module, apachectl_path)
        a_ret['binary'] = apachectl_path

        # Fixups
        for vhost in vhosts:
            a_ret['vhosts'].append(_fixup_missing_defaults(vhost))
        _set_envvar_overrides()
        a_ret['ports'] = list(set(a_ret['ports']))
        a_ret['access_logs'] = list(set(a_ret['access_logs']))
        a_ret['error_logs'] = list(set(a_ret['error_logs']))
        a_ret['loaded_modules'] = list(a_ret['loaded_modules'])

        return a_ret

    def collect(self):
        facts = {}
        apachectl_path = self.module.get_bin_path(
            'apachectl') or self.module.get_bin_path('apache2ctl')

        if apachectl_path:
            (rc, apache_out, stderr) = self.module.run_command(apachectl_path + ' -V')
            apache_out += stderr

            if rc == 0:
                data = self._set_apache(apache_out, apachectl_path)
                if data is not None:
                    facts = data
            else:
                ctest = {
                    'msg': apache_out,
                    'valid': False,
                }
                facts['config_test'] = ctest

        return facts


class NginxFactsCollector(BaseRaxFactsCollector):

    name = 'nginx'

    def _set_nginx(self, conf, nginx_path):
        n_ret = {}
        conf = conf.split('--')

        def _get_all_config(config_file=None, parent_file=None):
            """ Reads all config files, starting from the main one, expands all includes
                and returns all config in the correct order as a list.
            """
            if config_file is None:
                config_file = n_ret['config_file']

            if parent_file is None:
                parent_file = config_file

            ret = ['--NEWFILE-- ' + config_file]

            config_data = open(config_file, 'r').readlines()

            for line in [line.strip().strip(';') for line in config_data]:
                if line.startswith('#'):
                    continue
                line = line.split('#')[0]
                if line.startswith('include'):
                    includes = _get_includes_line(
                        line, config_file, n_ret['nginx_root'])
                    for include in includes:
                        try:
                            ret += _get_all_config(include, parent_file=config_file)
                        except IOError:
                            pass

                else:
                    ret.append(line.strip().strip(';'))

            ret.append('--NEWFILE-- ' + parent_file)

            return ret

        def _get_conf_key(key):
            """ Returns the value for the key as found in `nginx -V` minus the initial -- """
            for c in conf:
                if c.startswith(key):
                    try:
                        return c.split('=')[1].strip()
                    except IndexError:
                        return None

        def _get_vhost_stanza():
            return {
                'listen': [],
                'ssl': False,
                'indexes': [],
                'access_logs': [],
                'error_logs': [],
                'aliases': []

            }

        def _fixup_missing_defaults(vhost):
            """ Some configuration is implicit. If a server block completely lacks an access_log
                directive - it will inherit the global default one.
                Retrofit these if this is the case.
            """
            if isinstance(vhost['access_logs'], list) and not vhost['access_logs']:
                vhost['access_logs'] = [_get_conf_key('http-log-path')]
            if isinstance(vhost['error_logs'], list) and not vhost['error_logs']:
                vhost['error_logs'] = [_get_conf_key('error-log-path')]

            return vhost

        def _get_vhosts():
            """ Iterate over all included files as well as the main config, and look for
                    server {} blocks - return what we can learn from within them.
            """
            ret = []
            lines = _get_all_config()
            in_http_block = False
            in_server_block = False
            open_brackets = 0
            current_file = None

            for ln, line in enumerate(lines):
                if line.startswith('--NEWFILE--'):
                    current_file = line.split()[1]
                    continue

                line = _strip_line(line)

                ln += 1
                if not line:
                    continue

                if re.match(r"server.*{", line):
                    in_server_block = True
                    cur_vhost = _get_vhost_stanza()
                    cur_vhost['config_file'] = current_file

                if re.match(r"http.*{", line):
                    in_http_block = True

                if '{' in line:
                    open_brackets += 1
                if '}' in line:
                    open_brackets -= 1

                if in_http_block:
                    if line.lower().startswith("gzip "):
                        if line.split(' ')[1].lower() == 'on':
                            n_ret['gzip'] = True
                        else:
                            n_ret['gzip'] = False
                    if line.lower().startswith("sendfile"):
                        if line.split(' ')[1].lower() == 'on':
                            n_ret['sendfile'] = True
                        else:
                            n_ret['sendfile'] = False
                    if line.lower().startswith("default_type"):
                        n_ret['default_type'] = line.split()[1]

                if in_http_block and in_server_block:
                    """ Start with case sensitive results (log files, directories) """

                    if open_brackets == 2 and line.lower().startswith("root"):
                        root = line.split()[1]
                        if root[0] != '/':
                            root = _get_conf_key(
                                'prefix') + os.sep + root
                        cur_vhost['root'] = root

                    elif open_brackets == 2 and line.lower().startswith("index"):
                        cur_vhost['indexes'] = line.split()[1:]

                    elif line.lower().startswith("access_log"):
                        al = line.split()[1]
                        if al == 'off' and (open_brackets == 1 and in_server_block):
                            """ We're in a top level config, and access_log is off
                                this overrides everything else. off can be specified
                                in location blocks etc.
                            """
                            cur_vhost['access_logs'] = [None]
                        elif al == 'off':
                            """ We don't care about logging being turned off in other blocks """
                            continue
                        elif None not in cur_vhost['access_logs']:
                            cur_vhost['access_logs'].append(al)

                    elif line.lower().startswith("error_log"):
                        cur_vhost['error_logs'].append(line.split()[1])

                    elif line.lower().startswith('ssl_certificate ') or line.lower().startswith(
                            'ssl_certificate\t'):
                        cert_path = line.split()[1]
                        if cert_path[0] != '/':
                            cert_path = os.path.dirname(
                                n_ret['config_file']) + os.sep + cert_path
                        cur_vhost['ssl_certificate'] = cert_path

                    elif line.lower().startswith('ssl_certificate_key'):
                        cert_key_path = line.split()[1]
                        if cert_key_path[0] != '/':
                            cert_key_path = os.path.dirname(
                                n_ret['config_file']) + os.sep + cert_key_path
                        cur_vhost['ssl_key'] = cert_key_path

                    elif line.lower().startswith('ssl_protocols'):
                        cur_vhost['ssl_protocols'] = line.split()[1:]

                    elif line.lower().startswith('ssl_ciphers'):
                        cur_vhost['ssl_ciphers'] = line.split()[
                            1].strip('"\'')

                    """ Case insensitive stuff """
                    line = line.lower()

                    if re.match(r"^listen.*[0-9]", line):
                        cur_vhost['listen'].append(line.split()[1])
                        if 'ssl' in line:
                            cur_vhost['ssl'] = True

                    elif line.startswith('server_name'):
                        """ Extracts the server_name and any potential aliases.
                        server_name domain1.com domain2.com
                        or
                        server_name domain1.com alias somealias.com
                        """
                        ld = re.match(
                            r'(^server_name.*alias\ )(.*)', line)
                        if ld:
                            cur_vhost['aliases'] = list(
                                ld.groups()[1:])

                        server_names = line.split()[1:]
                        if len(server_names) > 2:
                            for sn in server_names[1:]:
                                if sn == 'alias':
                                    break
                                cur_vhost['aliases'].append(sn)

                        """ It's valid nginx to specify a server_name multiple times. Report

                            the first server_name as server_name, and the rest as aliases.
                        """
                        if 'server_name' in cur_vhost:
                            cur_vhost['aliases'].append(server_names[0])
                        else:
                            cur_vhost['server_name'] = server_names[0]

                    elif re.match(r'^ssl.*on', line):
                        cur_vhost['ssl'] = True

                if open_brackets == 0 and in_http_block:
                    in_http_block = False

                if open_brackets == 1 and in_server_block:
                    in_server_block = False
                    """ We've learned all we can about the server block - store it """
                    cur_vhost = _fixup_missing_defaults(cur_vhost)
                    ret.append(cur_vhost)
                    cur_vhost = _get_vhost_stanza()

            return ret

        n_ret['config_file'] = _get_conf_key('conf-path')
        if not n_ret['config_file']:
            return None
        n_ret['nginx_root'] = os.path.dirname(n_ret['config_file'])
        n_ret['vhosts'] = _get_vhosts()
        n_ret['pid_file'] = _get_conf_key("pid-path")
        n_ret['lock_file'] = _get_conf_key("lock-path")
        n_ret['config_test'] = _get_config_test(self.module, nginx_path)
        n_ret['default_error_log'] = _get_conf_key('error-log-path')
        n_ret['binary'] = nginx_path

        return n_ret

    def collect(self):
        facts = {}
        nginx_path = self.module.get_bin_path('nginx')
        if nginx_path:
            (rc, nginx_out, stderr) = self.module.run_command(nginx_path + ' -V')
            nginx_out += stderr

            if rc == 0:
                data = self._set_nginx(nginx_out, nginx_path)
                if data is not None:
                    facts = data
            else:
                ctest = {
                    'msg': nginx_out,
                    'valid': False,
                }
                facts['config_test'] = ctest

        return facts
