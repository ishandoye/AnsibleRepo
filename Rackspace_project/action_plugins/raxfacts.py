from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase


def generate_metadata(task_vars):
    hostvar_mapping = {
        'rs_customer': 'rs_customer',
        'rs_server': 'rs_server',
        'rs_login_ip': 'ansible_host',
        'rs_region': 'rs_region',
    }
    return dict([(k, task_vars.get(v)) for k, v in hostvar_mapping.items()])


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        metadata = self._task.args.get('metadata') or generate_metadata(task_vars)
        new_module_args = self._task.args.copy()
        new_module_args['metadata'] = metadata
        result.update(
            self._execute_module(module_args=new_module_args, task_vars=task_vars)
        )
        return result
