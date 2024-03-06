#!/usr/bin/env python3
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.server_attributes import RSServer

DOCUMENTATION = """
---
module: server_attributes
short_description: Obtain attributes about a device
description:
    - Uses Librack2 to obtain attributes about a given device.
version_added: "2.6"
options:
  device_id:
    description:
      - Device ID
    required: True
  rackertoken:
    description:
      - Identity rackertoken
    required: True
  attributes:
    description:
      - A list of the attributes to obtain about a server
author:
    - Dan Hand
"""

EXAMPLES = """
- name: Get attributes for a device
  server_attributes:
    device_id: "{{ rs_server }}"
    rackertoken: "{{ rackertoken|default(lookup('env', 'RACKERTOKEN')) }}"
    attributes:
      - is_eol
      - powered_on

- debug: var=ansible_facts.server_attributes
"""


def main():
    argument_spec = dict(
        argument_spec=dict(
            rackertoken=dict(required=True, type="str"),
            device_id=dict(required=True, type="str"),
            attributes=dict(type="list"),
        ),
        required_one_of=[["attributes"]],
        mutually_exclusive=[["attributes"]],
        supports_check_mode=True,
    )

    module = AnsibleModule(**argument_spec)
    attributes = module.params.get("attributes")
    device_id = module.params.get("device_id")
    rackertoken = module.params.get("rackertoken")

    server = RSServer(rackertoken, device_id)
    server.get_attributes(attributes)
    ansible_facts = {"server_attributes": server.get_attributes(attributes)}
    module.exit_json(changed=False, ansible_facts=ansible_facts, failed=False)


if __name__ == "__main__":
    main()
