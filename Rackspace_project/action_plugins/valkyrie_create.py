from __future__ import absolute_import, division, print_function

import copy
import sys
from datetime import datetime
from distutils.spawn import find_executable

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.plugins.loader import connection_loader

__metaclass__ = type


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()

try:
    from librack2.auth import Auth
    from librack2.core.server import CoreServer
    from librack2.core.account import CoreAccount

    HAS_LIBRACK2 = True
except ImportError:
    HAS_LIBRACK2 = False


class ActionModule(ActionBase):
    """Interacts with valkyrie API using LR2 functionality"""

    def run(self, tmp=None, task_vars=None):

        self._supports_check_mode = True
        if not HAS_LIBRACK2:
            raise AnsibleError("Librack2 is required for this plugin")

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if task_vars["ansible_facts"].get("valkyrie"):
            result["skipped"] = True
            result["skip_reason"] = "valkyrie already loaded"
            return result

        # Override connection to force it execute modules from localhost
        if self._task._delegate_to is None or self._task.delegate_to != "localhost":
            new_connection = connection_loader.get(
                "local", self._play_context, self._connection._new_stdin,
            )
            self._connection = new_connection
            self._connection._remote_is_local = True

        # Get plugin args
        device_id = self._task.args.get("device_id")
        account = self._task.args.get("account")
        file_name = self._task.args.get("name") or "%s.txt" % datetime.now().isoformat()
        content = self._task.args.get("content")

        rackertoken = self._task.args.get("rackertoken") or task_vars.get("rackertoken")

        try:
            auth = Auth("valkyrie", rackertoken=str(rackertoken))
        except Exception:
            _, ex = sys.exc_info()[:2]
            raise AnsibleError("%s" % str(ex))

        # Check to see if some content has been specified
        if not content:
            raise AnsibleError("'content' is required but nothing has been provided.")

        # account and device_id are mutually exclusive.
        if bool(account) == bool(device_id):
            raise AnsibleError(
                '"account" and "device_id" are mutually exclusive. '
                "Please choose one or the other."
            )

        # Instantiate CoreServer or CoreAccount
        try:
            if device_id:
                target_object = CoreServer(auth, device_id)
                account = target_object.account
            else:
                target_object = CoreAccount(auth, account)
                account = target_object
        except Exception:
            _, ex = sys.exc_info()[:2]
            raise AnsibleError("%s" % str(ex))

        # Make the module idempotent
        # Loop through all MyRackFile's for an account and compare the
        # MyRackFile.name to playbook var "name".
        for myrack_file in account.myrack_file_list():
            if myrack_file.name == file_name:
                # If the file names match we then load and compare the content
                # (which is lazy loaded by default)
                if myrack_file.contents == content:
                    return result

        # If check_mode is specified
        if self._task.check_mode:
            result["msg"] = {
                "success": True,
                "name": file_name,
                "permissions": device_id
                if device_id
                else None,
            }
            result["changed"] = True
            return result

        try:
            # Create the MyRackFile using (CoreServer/CoreAccount).myrack_create_file()
            myrack_file = target_object.myrack_create_file(content, file_name)
        except Exception:
            _, ex = sys.exc_info()[:2]
            raise AnsibleError("Error creating file: %s" % str(ex))

        if myrack_file:
            result["msg"] = {
                "success": True,
                "name": myrack_file.name,
                "permissions": myrack_file.device.id
                if myrack_file.device
                else None,
                "size": myrack_file.bytes,
                "links": myrack_file.links,
            }
            result["changed"] = True

        return result
