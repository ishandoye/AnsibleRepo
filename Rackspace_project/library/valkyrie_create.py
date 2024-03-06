#!/usr/bin/python
from __future__ import absolute_import, division, print_function

DOCUMENTATION = """
---
module: valkyrie_create
short_description: Create MyRackPortal files using valkyrie API
description:
    - Provides functionality using LR2 and the valkyrie API to create MyRackFiles
      associated with a server or available to the whole account.
    - This module may require OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES set in the
      environment on macOS High Sierra and newer.
requirements:
    - "ansible 2.6+"
    - librack2
options:
    device_id:
        description:
            - Core device number the newly created file will be associated with.
              The file permissions will match that of the device permissions.
              "device_id" and "account" are mutually exclusive.
    account:
        description:
            - An account the new file is to be associated with.
              The file will not be restricted, all users will have access.
              "account" and "device_id" are mutually exclusive.
    name:
        description:
            - Name of the file to be created
        required: false
        default: "datetime.now().isoformat().txt"
    content:
        description:
            - Content (string) for the new file to be created.
    rackertoken:
      description:
        - Identity racker token
    required: True
author:
    - Luke Shirnia
"""

EXAMPLES = """
- name: Create a MyRackFile WITH an associated device
  valkyrie_create:
    device_id: 431848
    name: "example.txt"
    content: "string content goes here"

- name: Create a MyRackFile WITHOUT an associated device
  valkyrie_create:
    account: 957072
    name: "example.txt"
    content: "string content goes here"
"""
