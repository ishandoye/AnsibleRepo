from __future__ import absolute_import, division, print_function

import subprocess
from distutils.spawn import find_executable

DOCUMENTATION = """
lookup: rax_secret
author:
  - Ed Velez <ed.velez@rackspace.com>
requirements:
  - hammertime

short_description: Look up Rackspace related secrets.
description:
  - Lookup rax related secrets. Currently supports rackertoken and coretokens
options:
  _terms:
    description: Name of secret to return
    choices: ['rackertoken', 'coretoken']
    required: True
  batch:
    description: Whether to set --batch on any hammertime commands run by rax_secret.
    type: boolean
    default: true
"""
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)
        ht_path = find_executable("ht")
        if not ht_path:
            raise AnsibleError(
                "Unable to find Hammertime. Hammertime is required for rax_secret."
            )
        display.vvv("Hammertime executable found at: %s" % ht_path)

        cmd = "%s --majorversion" % ht_path
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, _ = p.communicate()
        if p.returncode == 0 and int(stdout.decode("utf-8").rstrip()) >= 6:
            ht_cmd_args = {
                "rackertoken": "credentials --identity",
                "coretoken": "credentials --core",
            }
        elif p.returncode == 2:
            ht_cmd_args = {
                "rackertoken": "--get-token",
                "coretoken": "--get-core-token",
            }
        else:
            raise AnsibleError("Unknow error encountered running hammetime.")

        secrets = []
        batch = self.get_option("batch")
        for term in terms:
            if term not in ht_cmd_args:
                raise AnsibleError("rax_secret does not support %s option" % term)
            if batch:
                cmd = "%s --batch %s" % (ht_path, ht_cmd_args[term])
            else:
                cmd = "%s %s" % (ht_path, ht_cmd_args[term])
            display.vvv("Executing the following hammertime command: %s" % cmd)
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = p.communicate()
            if p.returncode == 0:
                secrets.append(stdout.decode("utf-8").rstrip())
            else:
                error_msg = "rax_secret(%s) returned with error code %d" % (
                    term,
                    p.returncode,
                )
                if stderr:
                    error_msg = "%s: %s" % (error_msg, stderr.decode("utf-8").rstrip())
                raise AnsibleError(error_msg)
        return secrets
