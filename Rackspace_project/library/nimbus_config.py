#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.monitoring.nimbus.config import NimbusConfig


DOCUMENTATION = '''
module: nimbus_config
short_description: Manages config files in Nimbus format
description:
     - "Manages Nimbus config files. As Nimbus rewrites configs on restart, templating is not
       working properly, this module understands and uses the config semantics instead. To use this
       module, one of the following keys is required: C(update), C(remove), C(load_config) or
       C(diff_from). Both check and diff modes are supported."
options:
  path:
    description:
      - The path to the config file to modify
    required: True
    default: null
  update:
    description:
      - "A dictionary to update the config with. Sections/options already present in the config
        file are updated. Sections/options from the provided dictionary not present in the config
        are added. Nothing is removed."
      - If file does not exist, create it and return OK with changed=True
    required: False
    default: null
  remove:
    description:
      - "List of paths to remove from the config. Each path is a list of components, each component
        is evaluated against the respective level of sections/options' names. All sections/options
        matching the last component are removed from the config."
      - If file does not exist, return OK with changed=False
    required: False
    default: null
  load_config:
    description:
      - "Set this to True to load a Nimbus config file into Ansible facts to be used by subsequent
        tasks"
    required: False
    default: null
  diff_from:
    description:
      - "Compare the nimbus config file to the provided dictionary and return the diff result"
    required: False
    default: null
'''

EXAMPLES = '''
# Load contents of /opt/nimsoft/robot/robot.cfg as a dictionary into nimbus_robot variable
- nimbus_config:
    path: /opt/nimsoft/robot/robot.cfg
    load_config: True
  register: nimbus_robot

# Create /opt/nimsoft/request.cfg to install Nimbus processes probe:
- nimbus_config:
    path: /opt/nimsoft/request.cfg
    update: {"distribution request": {"packages": "processes"}}

# Update /opt/nimsoft/example.cfg:
- nimbus_config:
    path: /opt/nimsoft/example.cfg
    update: {"section1": {"subsection1": {"firstkey": "newvalue"} }, "newsection": {"key": "val" } }
# Before:
# <section1>
#   <subsection1>
#     firstkey = oldvalue
#     secondkey = oldvalue2
#   </subsection1>
#   not = touched
# </section1>
#
# After:
# <section1>
#   <subsection1>
#     firstkey = newvalue
#     secondkey = oldvalue2
#   </subsection1>
# </section1>
# <newsection>
#   key = val
# </newsection>

# Remove sections from the config file:
- nimbus_config:
    path: /opt/nimsoft/example.cfg
    remove:
      - ["section1", "subsection.*"]
# Before:
# <section1>
#   <subsection1>
#     firstkey = oldvalue
#     secondkey = oldvalue2
#   </subsection1>
#   <subsection2>
#     mykey = myval
#   </subsection2>
#   not = touched
# </section1>
#
# After:
# <section1>
#   not = touched
# </section1>
'''

def main():

    global module
    module = AnsibleModule(
        argument_spec={
            'path': {'required': True, 'type': 'str'},
            'update': {'required': False, 'type': 'dict'},
            'remove': {'required': False, 'type': 'list'},
            'load_config': {'required': False, 'type': 'bool'},
            'diff_from': {'required': False, 'type': 'dict'},
        },
        supports_check_mode=True
    )
    available_actions = ('update', 'remove', 'load_config', 'diff_from')

    args = module.params
    actions = [k for k in args.keys() if k in available_actions and args[k] is not None]
    if len(actions) != 1:
        module.fail_json(
            msg="Exactly one of (%s) args must be specified" % '|'.join(available_actions)
        )
    action = actions[0]

    kwargs = {}
    cfg_file = args['path']
    cfg = NimbusConfig()
    if os.path.exists(cfg_file):
        cfg.parse(cfg_file)

    if action == 'diff_from':
        diff = cfg.diff(args['diff_from'])
        if diff:
            kwargs['diff'] = {'prepared': diff}
            kwargs['result'] = diff
            changed = True
        else:
            kwargs['result'] = ''
            changed = False
        module.exit_json(changed=changed, **kwargs)

    if action == 'update':
        changed = cfg.update(args['update'])

    elif action == 'remove':
        changed = cfg.remove(args['remove'])

    elif action == 'load_config':
        changed = False
        kwargs['config'] = cfg.facts()

    if changed and not module.check_mode:
        cfg.write(cfg_file)

    if module._diff:
        diff = cfg.diff()
        if diff is not None:
            kwargs['diff'] = {'prepared': diff}

    module.exit_json(changed=changed, **kwargs)


if __name__ == '__main__':
    main()
