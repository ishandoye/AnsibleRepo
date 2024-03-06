import sys
import traceback
from ansible.module_utils.facts.timeout import timeout


class BaseRaxFactsCollector(object):
    name = None
    aliases = set()
    hidden = False
    groups = ["all"]
    timeout = 300

    def __init__(self, module, facts_key=None, namespace=None, metadata=None):
        self.debug = []
        self.facts_key = facts_key or self.name
        self.module = module
        self.namespace = namespace or ""
        self.metadata = metadata or {}

    def collect(self):
        raise NotImplementedError

    def collect_raxfacts(self):
        facts = {}
        try:
            if self.timeout is None or self.timeout == 0:
                facts[self.namespace + self.facts_key] = self.collect()
            else:
                facts[self.namespace + self.facts_key] = timeout(seconds=self.timeout)(self.collect)()
        except SystemExit:  # pylint: disable=try-except-raise
            raise
        except Exception:
            self.debug.append(
                {self.name: traceback.format_exception(*(sys.exc_info()))}
            )
            facts[self.namespace + self.facts_key] = None
        return facts
