from ansible.errors import AnsibleError
from librack2.auth import Auth
from librack2.server import get_servers

# We do not want to inspect these attributes by default.
BLACKLIST_ATTRS = ["server", "account"]


class RSServer(object):
    def __init__(self, rackertoken, device_id):
        self._rackertoken = rackertoken
        self._device_id = [device_id]

    def get_attributes(self, attributes):
        auth = Auth("attribute_getter", rackertoken=self._rackertoken)
        server = get_servers(auth, self._device_id, attributes=attributes)[0]
        attrs = {}
        try:
            for attribute in attributes:
                if attribute in BLACKLIST_ATTRS:
                    continue
                if not isinstance(attribute, str):
                    raise Exception("Please provide a valid attribute type!")
                attrs[attribute] = getattr(server, attribute)
        except Exception as ex:
            raise AnsibleError(str(ex))
        return attrs
