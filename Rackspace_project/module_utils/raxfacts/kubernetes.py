import json

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class K8sFactsCollector(BaseRaxFactsCollector):

    name = "kubernetes"
    aliases = ["kubernetes_facts"]

    def collect(self):
        def _run_command(command):
            (rc, output, stderr) = self.module.run_command(command)
            if rc != 0:
                raise Exception(
                    "Ret: %s\nstdout: %s\nstderr: %s" % (rc, output, stderr)
                )
            return output

        def _get_version():
            version = _run_command("%s version -o json" % (kubernetes_path))
            return json.loads(version)

        def _get_namespaces():
            namespaces = _run_command("%s get namespaces -o json" % (kubernetes_path))
            return json.loads(namespaces).get("items")

        def _get_pods():
            pods = _run_command("%s get pods -A -o json" % (kubernetes_path))
            return json.loads(pods).get("items")

        def _get_services():
            services = _run_command("%s get services -A -o json" % (kubernetes_path))
            return json.loads(services).get("items")

        def _get_nodes():
            nodes = _run_command("%s get nodes -o json" % (kubernetes_path))
            return json.loads(nodes).get("items")

        kubernetes_path = self.module.get_bin_path("kubectl")
        debug = {}

        ret = {
            "version": None,
            "namespaces": None,
            "pods": None,
            "services": None,
            "nodes": None,
        }

        if not kubernetes_path:
            self.debug.append({"kubernetes": "Command kubectl does not exist"})
            return None

        try:
            ret["version"] = _get_version()
        except Exception as ex:
            debug["version"] = str(ex)

        try:
            ret["namespaces"] = _get_namespaces()
        except Exception as ex:
            debug["namespaces"] = str(ex)

        try:
            ret["pods"] = _get_pods()
        except Exception as ex:
            debug["pods"] = str(ex)

        try:
            ret["services"] = _get_services()
        except Exception as ex:
            debug["services"] = str(ex)

        try:
            ret["nodes"] = _get_nodes()
        except Exception as ex:
            debug["nodes"] = str(ex)

        if debug:
            self.debug.append({"kubernetes": debug})

        return ret
