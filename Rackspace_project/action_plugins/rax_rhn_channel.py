from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.plugins.loader import connection_loader


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        device_id = self._task.args.get('device_id') or task_vars.get(
            'rs_server') or task_vars.get('core_device_number')
        core_token = self._task.args.get('core_token') or task_vars.get(
            'core_token')

        if device_id is None:
            raise AnsibleError(
                'Unable to find device_id in host_vars for device. '
                'Use device_id parameter to specify core device number.')

        if core_token is None:
            raise AnsibleError(
                'Unable to find core_token in host_vars for device. '
                'Use core_token parameter to specify a core auth token. '
                'Or use the core_auth_token module prior to this module.')

        new_module_args = self._task.args.copy()
        new_module_args['device_id'] = device_id
        new_module_args['core_token'] = core_token

        if self._task._delegate_to is None or self._task.delegate_to != 'localhost':
            new_connection = connection_loader.get(
                'local',
                self._play_context,
                self._connection._new_stdin,
            )
            self._connection = new_connection
            self._connection._remote_is_local = True

        result.update(
            self._execute_module(
                module_args=new_module_args,
                task_vars=task_vars,
            ))
        return result
