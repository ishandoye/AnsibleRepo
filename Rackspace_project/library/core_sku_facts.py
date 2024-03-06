#!/usr/bin/python
from __future__ import absolute_import, division, print_function

DOCUMENTATION = '''
---
module: core_sku_facts
short_description: Gather core skus for a device
description:
    - Gather core skus for a device. The module attempts to fetch rackertoken via
      hammertime. If hammertime is not available you can provide an identity
      rackertoken via the rackertoken parameter
version_added: "2.6"
options:
  device_id:
    description:
      - Core device ID
    required: True
  rackertoken:
    description:
      - Identity racker token
    required: True
author:
    - Ed Velez
    - Tony Garcia
'''

EXAMPLES = '''
- name: Get core sku facts for device
  core_sku_facts:
    device_id: "{{ rs_server }}"

- debug: var=ansible_facts.core_sku_facts
'''

RETURN = '''
ansible_facts:
  description: add core_sku_facts to ansible_facts
    returned:
    type: complex
    contains:
      core_sku_facts:
        description: dictionary of sku data returned from librack
        type: dict
'''
