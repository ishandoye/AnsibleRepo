from ansible.module_utils.facts import get_all_facts
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class SetupFactsCollector(BaseRaxFactsCollector):

    name = 'setup'
    timeout = 60

    def collect(self):
        data = None

        # Use the timeout command if available to avoid leaving an orphaned process
        timeout_cmd = self.module.get_bin_path('timeout')
        if timeout_cmd:
            cmd = (
                "awk '$1 ~ /.*:.*/ { print $2}' /proc/mounts | "
                "while read mount; do timeout --signal=KILL 1 ls -d $mount > /dev/null "
                "|| echo $mount; done")
        else:
            cmd = (
                "awk '$1 ~ /.*:.*/ { print $2}' /proc/mounts | "
                "while read mount; do read -t1 < <(ls -d $mount)> /dev/null "
                "|| echo $mount; done")

        _, out, _ = self.module.run_command(
            cmd,
            use_unsafe_shell=True,
            executable='/bin/bash'
        )

        if out:
            self.debug.append({'setup': 'stale mounts detected - setup execution aborted'})
            return data

        # The structure of the data returned by get_all_facts changed
        # in a newer version of ansible. When 'ansible_facts' is not in the
        # top level dict, we need to massage the data slightly to have
        # the appropriate `ansible_` prefix where applicable.
        module_params = self.module.params
        self.module.params = {
            'gather_subset': ['all'],
            'gather_timeout': 10,
            'filter': '*',
            'fact_path': '/etc/ansible/facts.d'
        }
        setup_facts = get_all_facts(self.module)
        self.module.params = module_params
        if setup_facts.get('ansible_facts'):
            data = setup_facts['ansible_facts']
        else:
            preserve_keys = ['module_setup', 'gather_subset']
            renamed = {}
            for key in preserve_keys:
                if key in setup_facts:
                    renamed[key] = setup_facts.pop(key)
            for (k, v) in setup_facts.items():
                renamed['ansible_%s' % k] = v
            if renamed:
                data = renamed

        return data
