from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class CrowdstrikeFactsCollector(BaseRaxFactsCollector):

    name = "crowdstrike"

    def collect(self):
        def _get_command(binary):
            """
            Returns the docker command to execute to get data.
            """
            try:
                return self.module.get_bin_path(binary)
            except IOError:
                pass

        def _run_command(command):
            (rc, output, stderr) = self.module.run_command(command)
            if rc != 0:
                raise Exception(
                    "Ret: %s\nstdout: %s\nstderr: %s" % (rc, output, stderr)
                )
            return output

        def _get_version():
            version = _run_command("%s -g --version" % (falconctl_path))
            return version.split("=")[1].strip()

        def _rfm_state():
            state = _run_command("%s -g --rfm-state" % (falconctl_path))
            return state.strip()

        def _rfm_reason():
            reason = _run_command("%s -g --rfm-reason" % (falconctl_path))
            return reason.strip()

        def _agent_id():
            agent = _run_command("%s -g --aid" % (falconctl_path))
            return agent.strip()

        def _customer_id():
            cid = _run_command("%s -g --cid" % (falconctl_path))
            return cid.strip()

        def _tags():
            tags = _run_command("%s -g --tags" % (falconctl_path))
            return tags.strip()

        debug = {}

        ret = {
            "version": None,
            "rfm_state": None,
            "rfm_reason": None,
            "agent_id": None,
            "customer_id": None,
            "tags": None,
        }

        falconctl_path = _get_command("/opt/CrowdStrike/falconctl")

        if not falconctl_path:
            self.debug.append({"crowdstrike": "Command falconctl does not exist"})
            return ret

        try:
            ret["version"] = _get_version()
        except Exception as ex:
            ret["version"] = None
            debug["version"] = str(ex)

        try:
            ret["rfm_state"] = _rfm_state()
        except Exception as ex:
            ret["rfm_state"] = None
            debug["rfm_state"] = str(ex)

        try:
            ret["rfm_reason"] = _rfm_reason()
        except Exception as ex:
            ret["rfm_reason"] = None
            debug["rfm_reason"] = str(ex)

        try:
            ret["agent_id"] = _agent_id()
        except Exception as ex:
            ret["agent_id"] = None
            debug["agent_id"] = str(ex)

        try:
            ret["customer_id"] = _customer_id()
        except Exception as ex:
            ret["customer_id"] = None
            debug["customer_id"] = str(ex)

        try:
            ret["tags"] = _tags()
        except Exception as ex:
            ret["tags"] = None
            debug["tags"] = str(ex)

        if debug:
            self.debug.append({"crowdstrike": debug})

        return ret
