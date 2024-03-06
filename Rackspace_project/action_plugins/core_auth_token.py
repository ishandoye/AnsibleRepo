from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.module_utils.urls import open_url
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six.moves.urllib.error import HTTPError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    CTKAPI = "https://ws.core.rackspace.com/ctkapi"

    def _prompt(self, task_vars, prompt, echo=True):
        prompt_task = self._task.copy()
        prompt_task.name = "prompt"
        prompt_task.args = dict(prompt=prompt, echo=echo)
        pause_action = self._shared_loader_obj.action_loader.get(
            'pause',
            task=prompt_task,
            connection=self._connection,
            play_context=self._play_context,
            loader=self._loader,
            templar=self._templar,
            shared_loader_obj=self._shared_loader_obj)
        return pause_action.run(task_vars=task_vars)['user_input']

    # Python on macOS High Sierra and newer can have issues with forking
    # processes with active threads. This issue is discussed on github at
    # https://github.com/ansible/ansible/issues/32499
    def _platform_check(self):
        if (
            # 0th element returned by os.uname() should be the sysname in both
            # py2 and py3 i.e. "Darwin", "Linux", etc.
            os.uname()[0].startswith('Darwin')
            and os.getenv('OBJC_DISABLE_INITIALIZE_FORK_SAFETY') is None
        ):
            raise AnsibleError(
                'Error: Set environment variable '
                'OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES to run on macOS.'
            )

    def _core_request(self, url, data=None):
        try:
            resp = open_url(url, data=json.dumps(data))
        except HTTPError as error:
            if error.code == 403:
                raise AnsibleError(
                    'Error: Authentication to core failed: %s' % str(error))
            raise AnsibleError('Error: %s' % str(error))
        except Exception as error:
            raise AnsibleError(str(error))
        data = json.loads(resp.read())
        return data

    def _get_core_token(self, username, password):
        url = '%s/login/%s' % (self.CTKAPI, username)
        data = {'password': password}
        auth_token = self._core_request(url, data)['authtoken']
        return auth_token

    def _is_token_valid(self, token):
        url = '%s/session/%s' % (self.CTKAPI, token)
        token_valid = boolean(self._core_request(url)['valid'])
        return token_valid

    def _read_token_from_cache(self, cache_file):
        try:
            with open(cache_file, 'r+') as fh:
                token = fh.readlines()[0].rstrip()
        except Exception as error:
            display.vvv('Error reading token from cache file: %s' % str(error))
            token = ''

        if token:
            if self._is_token_valid(token):
                display.vvv('Using valid token found in %s' % cache_file)
            else:
                display.vvv('Token found in %s is invalid' % cache_file)
                token = ''
        return token

    def _write_token_to_cache(self, cache_file, token):
        try:
            with open(cache_file, 'w') as fh:
                os.chmod(cache_file, 0o600)
                fh.write(token + '\n')
        except Exception as error:
            display.vvv('Error writing token to cache file: %s' % str(error))

    def run(self, tmp=None, task_vars=None):
        self._platform_check()
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        use_token_cache = boolean(
            self._task.args.get('use_token_cache', True), strict=False)
        cache_file = os.path.expanduser(
            self._task.args.get('cache_file', '~/.core_token'))

        # Skip task if `core_token` is already defined. Prevents us
        # from having to worry about whether or not we can override
        # core_token due to variable precedence.
        if task_vars.get('core_token'):
            if self._is_token_valid(task_vars.get('core_token')):
                result['skipped'] = True
                result['skip_reason'] = 'A valid core_token is already defined'
            else:
                result['failed'] = True
                result['msg'] = 'The core_token provided is invalid'
            return result

        if use_token_cache:
            token = self._read_token_from_cache(cache_file)
        else:
            token = ''

        if not token:
            username = self._prompt(task_vars, 'username(SSO)')
            password = self._prompt(task_vars, 'PIN+RSA', echo=False)
            token = self._get_core_token(username, password)

            if use_token_cache:
                self._write_token_to_cache(cache_file, token)

        result['ansible_facts'] = dict(core_token=token)
        return result
