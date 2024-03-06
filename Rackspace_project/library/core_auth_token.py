#!/usr/bin/env python

DOCUMENTATION = '''
---
module: core_auth_token
short_description: Retrieve an authentication token from core
description:
    - Retrieve an authentication token from core. Supports interactive authentication and caching to filesystem.
    - Returns token as core_token ansible fact.
    - If a core_token variable is already defined this task will be skipped if the token
      is valid or fail if is invalid.
    - This module may require OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES set in the
      environment on macOS High Sierra and newer.
requirements:
    - "ansible 2.5+"
options:
    use_token_cache:
        description:
            - Whether or not to read/write token from cache_file.
        default: True
    cache_file:
        description:
            - Location to use to use for read/writing token retrieved from core.
        default: '~/.core_token'
author: Ed Velez
'''

EXAMPLES = '''
- name: Retreive authentication token from core
  core_auth_token:
  run_once: True
  become: False
'''
