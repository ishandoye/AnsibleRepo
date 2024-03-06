#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.raxfacts.collectors import (
    collector_classes,
    get_collector_info,
)

DOCUMENTATION = """
---
module: raxfacts
short_description: Gather extended facts for server
description:
     - Gather requested facts for a server
options:
    facts:
        description:
            - List of raxfacts modules to run. Use list_modules to find modules and groupings.
    list_modules:
        description:
            - Whether to return a list of available raxfacts modules and groupings.
    namespace:
        description:
            - String to namespace top level keys with
        required: false
        default: ''
"""

EXAMPLES = """
- name: Gather patching facts for servers
  raxfacts:
    facts:
      - packages
      - hardware
"""


def uniq_with_order(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]


def main():
    module = AnsibleModule(
        argument_spec=dict(
            facts=dict(type="list"),
            list_modules=dict(type="bool"),
            namespace=dict(type="str", default=""),
            debug=dict(type="bool", default=False),
            metadata=dict(type="dict", default={}),
        ),
        supports_check_mode=True,
        required_one_of=[["facts", "list_modules"]],
        mutually_exclusive=[["facts", "list_modules"]],
    )
    metadata = module.params["metadata"]
    facts = module.params["facts"] or []
    debug = module.params["debug"]
    list_modules = module.params["list_modules"]
    namespace = module.params["namespace"]
    collector_names, collector_group_map = get_collector_info()

    if list_modules:
        module.exit_json(
            ansible_facts=dict(modules=collector_names, groups=collector_group_map)
        )

    facts = uniq_with_order(facts)
    selected_collectors = []
    for fact in facts:
        for collector_class in [
            cc for cc in collector_classes if fact == cc.name or fact in cc.aliases
        ]:
            selected_collectors.append(
                collector_class(
                    module,
                    facts_key=fact,
                    namespace=namespace,
                    metadata=metadata,
                )
            )
            break
        else:
            if fact in collector_group_map:
                selected_collectors.extend(
                    [
                        collector_class(
                            module, namespace=namespace, metadata=metadata)
                        for collector_class in collector_classes
                        if not collector_class.hidden and fact in collector_class.groups
                    ]
                )
            else:
                module.fail_json(
                    msg=(
                        "'%s' is not a valid module name or group. Use 'list_modules' "
                        "for a list of valid module names and group names." % fact
                    )
                )

    ansible_facts = {}
    ansible_facts.update(
        [item for sc in selected_collectors for item in sc.collect_raxfacts().items()]
    )

    if debug:
        ansible_facts["debug"] = [
            item for sc in selected_collectors for item in sc.debug
        ]
        ansible_facts["debug"].append(dict(options=module.params))

    module.exit_json(ansible_facts=ansible_facts)


if __name__ == "__main__":
    main()
