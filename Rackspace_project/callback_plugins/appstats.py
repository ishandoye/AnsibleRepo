#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020 Rackspace US, Inc.
# All rights reserved - Do Not Redistribute

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "GTS Linux",
}

DOCUMENTATION = """
    callback: appstats
    callback_type: notification
    requirements:
      - none
    short_description: Sends notification to appstats
    description:
        - This callback plugin reports ansible role execution to Appstats.
        - The default appstats application profile can be found at U(https://stepladder.rax.io/appstats/app/playbooks).
    author: "Tony Garcia <tony.garcia@rackspace.com>"
    options:
      staging:
        default: "False"
        required: False
        description: Send Appstats events to staging environment if this is set
        env:
          - name: APPSTATS_STAGING
        ini:
          - section: callback_appstats
            key: staging
      url:
        default: "https://stepladder.rax.io/api/appstats/v3/event"
        required: False
        description: Custom URL for appstats events
        env:
          - name: APPSTATS_URL
        ini:
          - section: callback_appstats
            key: url
      appname:
        default: "playbooks"
        required: False
        description: Appstats application name
        env:
          - name: APPSTATS_APPNAME
        ini:
          - section: callback_appstats
            key: appname
      username:
        required: False
        description: Username to report to appstats. This should normally be a SSO username.
        env:
          - name: APPSTATS_USERNAME
        ini:
          - section: callback_appstats
            key: username
"""

EXAMPLES = """
To override defaults either:

Set environment variables:
  export APPSTATS_URL=https://staging.stepladder.rax.io/api/appstats/v3/event
  export APPSTATS_APPNAME=playbooks
  export APPSTATS_USERNAME=racker

Set the ansible.cfg variable in the callback_appstats block
  [callback_appstats]
  url = https://staging.stepladder.rax.io/api/appstats/v3/event
  appname = playbooks
  username = racker
"""

import os
import getpass
import time
import json

from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase

HAS_LIBRACK2 = True
try:
    from librack2 import appstats
except ImportError:
    HAS_LIBRACK2 = False


class CallbackModule(CallbackBase):
    """This is an ansible callback plugin that sends status updates to Appstats
    to report a successful playbook execution.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "appstats"
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self, display=None):

        super(CallbackModule, self).__init__(display=display)

        # This plugin does not send any appstats events when check mode is enabled
        self.check_mode = False

        # This is stores a dictionary with hosts as keys and lists of role names as values
        # This variables was called "roles" in the past
        self.executions = {}

    def get_username(self):
        """Attempts to read the username from raxcfg.json, uses running user
        otherwise"""

        username = getpass.getuser()

        # Read config file, return if there is any error
        config_file = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        config_file += "/rackspace/raxcfg.json"
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            username = config.get("raxcommon", {}).get("rax_sso")
        except (IOError, AttributeError, ValueError) as e:
            self._display.vvv("%s" % e)

        self._display.vvv("rax username: %s" % username)
        return username

    def post_appstats(self, app, function, sso, targets, url):
        """Report to appstats
        The appstats payload is defined here:
        https://github.rackspace.com/GTSLAE/mono/blob/devel/stepladder/doc/api/appstats.md#adding-an-event

        This function is mostly the same as librack2.appstats' submit_event function.
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "app": app,
            "function": function,
            "username": sso,
            "date": int(time.time()),
        }

        # This sends one API call for every execution; no batching is done
        # TODO: consider batching API calls like librack2.appstats.submit_event does
        targets = range(0, targets if targets is not None else 1)
        for _ in targets:
            self._display.vvv("POSTing appstats payload: %s " % json.dumps(payload))
            try:
                # This is a function Ansible provides in its util library for URLs
                open_url(
                    url=url, method="POST", data=json.dumps(payload), headers=headers
                )
            except Exception as e:
                self._display.warning(
                    "Could not submit message to Appstats: %s" % str(e)
                )

    def sort_by_role(self, roles):
        """Inverts a dictionary of hosts to roles to a dictionary of roles to hosts"""
        by_role = {}
        for host, _roles in roles.items():
            for role in _roles:
                # Add hosts per role, avoid duplicates
                by_role[role] = list(set(by_role.get(role, []) + [host]))

        self._display.vvv("sorted by_role: %s" % by_role)
        return by_role

    def v2_playbook_on_play_start(self, play):
        try:
            self.check_mode = play.get_variable_manager().get_vars()[
                "ansible_check_mode"
            ]
        except TypeError:
            # Support for fetching variable manager vars prior to Ansible 2.4
            self.check_mode = play.get_variable_manager().get_vars(play._loader)[
                "ansible_check_mode"
            ]

    def v2_runner_on_ok(self, result):
        """Get the role name"""
        res = result._result
        module = result._task.action
        host = str(result._host)

        # Get role name when included
        if module == "include_role":

            # Get all the roles when a loop is used
            if isinstance(res.get("results"), list):
                for item in res["results"]:
                    role = item.get("_ansible_item_label")
                    # Add role per host, avoid duplicates
                    self.executions[host] = list(
                        set(self.executions.get(host, []) + [role])
                    )

            # Get the role when called individually
            else:
                # Ansible 2.8 renames "include_variables" to "include_args"
                role = res.get("include_variables") or res.get("include_args")
                role = role["name"]
                self.executions[host] = self.executions.get(host, []) + [role]

    def v2_playbook_on_stats(self, stats):
        """Report to appstats hosts that succeeded"""
        if self.check_mode:
            self._display.vvv("Check mode detected, not reporting to appstats")
            return

        if not self.executions:
            self._display.vvv("No roles found to report to appstats")
            return

        try:
            url = self.get_option("url")
            appname = self.get_option("appname")
            username = self.get_option("username") or self.get_username()
            staging = self.get_option("staging")
        except (TypeError, AttributeError):
            url = os.getenv(
                "APPSTATS_URL", "https://stepladder.rax.io/api/appstats/v3/event"
            )
            appname = os.getenv("APPSTATS_APPNAME", "playbooks")
            username = os.getenv("APPSTATS_USERNAME", self.get_username())
            staging = os.getenv("APPSTATS_STAGING", "False")

        if staging.lower() == "true":
            # set staging to boolean; librack2 expects a boolean
            staging = True
            # overwrite url for endpoint if APPSTATS_STAGING is set
            url = "https://staging.stepladder.rax.io/api/appstats/v3/event"
        else:
            staging = False

        self._display.vvv(
            "options: (url: %s, appname: %s, username: %s)" % (url, appname, username)
        )

        # We only want to send stats for succeeded executions; failed executions don't save time
        # NOTE: If any tasks in a playbook that use a role fail, it will count as a role failure
        execution_successes = {}
        for host, roles in self.executions.items():
            # summarize function is provided by ansible
            # see lib/ansible/executor/stats.py#L60-L71
            host_summary = stats.summarize(host)

            # An execution is considered successful if failures and unreachable is non-zero
            failures = (
                host_summary.get("failures")
                - host_summary.get("rescued", 0)
                + host_summary.get("unreachable")
            )

            if not failures:
                execution_successes[host] = roles

        # End execution of function if no roles passed
        if not execution_successes:
            self._display.vvv("No role executions to report to appstats")
            return

        hosts_per_role = self.sort_by_role(execution_successes)

        # Report by role
        for role, hosts in hosts_per_role.items():
            self._display.vvv(
                # pylint: disable=line-too-long
                'payload: {"app": "%s", "function": "%s", "sso": "%s", "targets": "%s", "url": "%s"}'
                % (appname, role, username, len(hosts), url)
            )

            if HAS_LIBRACK2:
                appstats.submit_event(
                    app=appname,
                    function=role,
                    sso=username,
                    targets=len(hosts),
                    staging=staging,
                )
            else:
                self.post_appstats(
                    app=appname,
                    function=role,
                    sso=username,
                    targets=len(hosts),
                    url=url,
                )
