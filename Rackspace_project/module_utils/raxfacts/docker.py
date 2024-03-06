import json
import sys

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class DockerFactsCollector(BaseRaxFactsCollector):

    name = "docker"
    aliases = ["docker_facts"]

    def collect(self):
        def _get_command(binary):
            """
            Returns the docker command to execute to get data.
            """
            try:
                return self.module.get_bin_path(binary)
            except IOError:
                pass

        docker_path = _get_command("docker")
        debug = {}

        ret = {
            "containers": None,
            "images": None,
            "info": None,
            "networks": None,
        }

        def _run_command(command):
            (rc, output, stderr) = self.module.run_command(command)
            if rc != 0:
                raise Exception(
                    "Ret: %s\nstdout: %s\nstderr: %s" % (rc, output, stderr)
                )
            return output

        def _get_info():
            info = _run_command("%s info --format '{{json .}}'" % (docker_path))
            return json.loads(info)

        def _get_containers():
            containers = []
            raw_data = _run_command(
                "%s container ls --format '{{json .}}'" % (docker_path)
            )
            for line in filter(None, raw_data.split("\n")):
                containers.append(json.loads(line))
            return containers

        def _get_networks():
            networks = []
            raw_data = _run_command(
                "%s network ls --format '{{json .}}'" % (docker_path)
            )
            for network in filter(None, raw_data.split("\n")):
                networks.append(json.loads(network))
            return networks

        def _get_images():
            images = []
            render = {
                "id": "{{.ID}}",
                "repository": "{{.Repository}}",
                "tag": "{{.Tag}}",
                "digest": "{{.Digest}}",
                "created_since": "{{.CreatedSince}}",
                "created_at": "{{.CreatedAt}}",
                "size": "{{.Size}}",
            }
            raw_data = _run_command(
                "%s images --format '%s'" % (docker_path, json.dumps(render))
            )
            for image in filter(None, raw_data.split("\n")):
                images.append(json.loads(image))
            return images

        if not docker_path:
            self.debug.append({"docker": "Command Docker does not exist"})
            return ret

        try:
            ret["info"] = _get_info()
        except Exception as ex:
            ret["info"] = None
            debug["info"] = str(ex)

        try:
            ret["containers"] = _get_containers()
        except Exception as ex:
            ret["containers"] = None
            debug["containers"] = str(ex)

        try:
            ret["networks"] = _get_networks()
        except Exception as ex:
            ret["networks"] = None
            debug["networks"] = str(ex)

        try:
            ret["images"] = _get_images()
        except Exception as ex:
            ret["images"] = None
            debug["images"] = str(ex)

        if debug:
            self.debug.append({"docker": debug})

        return ret
