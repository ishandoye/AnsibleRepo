import os
import re

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class PleskFactsCollector(BaseRaxFactsCollector):

    name = 'plesk'

    def collect(self):
        ret = {'php_versions': None}
        try:
            if not os.path.isdir('/etc/psa'):
                self.debug.append({'plesk': '/etc/psa does not exist'})
                raise Exception()

            product_root = '/usr/local/psa'
            psa_conf = open('/etc/psa/psa.conf').readlines()
            for line in [line.strip() for line in psa_conf]:
                if line.startswith('PRODUCT_ROOT_D'):
                    product_root = line.split()[1]

            full_version = open(os.path.join(
                product_root, 'version'), 'r').read().strip('\n')

            # Overwrite later if we find a license key
            license_number = None
            if os.path.isdir('/etc/sw/keys/keys/'):
                if os.path.isfile('/usr/local/psa/bin/keyinfo'):
                    _, out, _ = self.module.run_command(
                        '/usr/local/psa/bin/keyinfo -l',
                        use_unsafe_shell=True,
                        executable='/bin/bash',
                        )

                    keyinfo = {}
                    pattern = re.compile('(.*): (.*)')
                    for line in out.split('\n'):
                        if line:
                            match = pattern.match(line)
                            if match:
                                keyinfo[match.group(1).rstrip()] = match.group(2)

                    ret['keyinfo'] = keyinfo
                    plesk_key_id = keyinfo.get('plesk_key_id', '')
                    match = re.match('PLSK([0-9]{8})', plesk_key_id)
                    if match:
                        license_number = 'PLSK.%s' % match.group(1)
                    else:
                        # Try to find license number from key files using the lim_date when
                        # plesk_key_id does not contain a proper license number.
                        if len(keyinfo.get('lim_date', '')) == 8:
                            year = keyinfo['lim_date'][0:4]
                            month = keyinfo['lim_date'][4:6]
                            day = keyinfo['lim_date'][6:8]
                            expiration = '%s-%s-%s' % (year, month, day)
                            # Get license key files that have the applicable expiration date
                            _, out, _ = self.module.run_command(
                                'grep -l expiration-date.*%s /etc/sw/keys/keys/key*' % expiration,
                                use_unsafe_shell=True,
                                executable='/bin/bash',
                            )
                            if out:
                                _, out, _ = self.module.run_command(
                                    r'grep -Eohm 1 "PLSK\.[0-9]{8}" %s' % out.replace('\n', ' '),
                                    use_unsafe_shell=True,
                                    executable='/bin/bash',
                                )
                                if out:
                                    if len(set(out.splitlines())) == 1:
                                        license_number = list(set(out.splitlines()))[0]
                                    else:
                                        ret['error'] = (
                                            'Multiple Plesk license numbers found in '
                                            '/etc/sw/keys/keys/'
                                        )
                                        self.debug.append({'plesk': ret['error']})
            elif os.path.isfile('/etc/psa/psa.key'):
                # Method for finding key on older plesk versions
                _, out, _ = self.module.run_command(
                    r'grep -Eohm 1 "PLSK\.[0-9]{8}" /etc/psa/psa.key',
                    use_unsafe_shell=True,
                    executable='/bin/bash',
                )
                if out:
                    license_number = out.rstrip()

            ret['license_number'] = license_number
            ret['installed'] = True
            ret['full_version'] = full_version
            ret['version'] = full_version.split()[0]

        except Exception:
            ret = None

        try:
            import json
            if ret is not None:
                ret['php_versions'] = json.load(
                    open('/etc/psa/php_versions.json', 'r'))['php']
        except ImportError:
            self.debug.append({'plesk': ('Plesk PHP versions detection is not available on this'
                                         ' platform. (missing json support)')})

        except Exception:
            pass

        return ret
