from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
from distutils.spawn import find_executable
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.plugins.loader import connection_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

try:
    from librack2.auth import Auth
    from librack2.server import get_servers
    HAS_LIBRACK2 = True
except ImportError:
    HAS_LIBRACK2 = False


class ActionModule(ActionBase):
    '''Creates facts based on core sku data by using librack.'''

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        self._supports_check_mode = True
        if not HAS_LIBRACK2:
            raise AnsibleError("Librack2 is required for this plugin")

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if task_vars['ansible_facts'].get('core_sku_facts'):
            result['skipped'] = True
            result['skip_reason'] = 'core_sku_facts already loaded'
            return result

        # Override connection to force it execute modules from localhost
        if self._task._delegate_to is None or self._task.delegate_to != 'localhost':
            new_connection = connection_loader.get(
                'local',
                self._play_context,
                self._connection._new_stdin,
            )
            self._connection = new_connection
            self._connection._remote_is_local = True

        # Get plugin args
        device_id = self._task.args.get("device_id") or task_vars.get(
            "rs_server") or task_vars.get("core_device_number")
        rackertoken = self._task.args.get("rackertoken") or task_vars.get("rackertoken")

        # Get SKU info from librack
        try:
            auth = Auth('core_sku_facts', rackertoken=str(rackertoken))
            servers = get_servers(auth, [device_id], attributes=['parts'])
        except Exception:
            _, ex = sys.exc_info()[:2]
            raise AnsibleError("%s" % str(ex))

        if not servers:
            raise AnsibleError("Unable to return skus for device %s" % device_id)

        # Return sku info as facts
        labels = {}
        for part in servers[0].parts:
            labels[part.label] = {
                "desc": part.description,
                "subattrs": part.subattrs,
                "sku_number": part.sku_number
            }
        ansible_facts = {'core_sku_facts': labels}

        result['ansible_facts'] = ansible_facts

        return result
