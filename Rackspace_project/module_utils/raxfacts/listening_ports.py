import os
import re
import socket

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector

SOCKET_FD_PAT = re.compile(r"socket:\[(\d+)\]")

class ListeningPortFactsCollector(BaseRaxFactsCollector):
    name = "listening_ports"


    def __init__(self, *args, **kwargs):
        super(ListeningPortFactsCollector, self).__init__(*args, **kwargs)
        self.pid_by_inode = {}
        self.pid_list = None
        self.all_pids_scanned = False

    def all_pids(self):
        # Generator function to loop through list of pids on the device
        for pid in os.listdir("/proc"):
            if pid.isdigit():
                yield pid
        self.all_pids_scanned = True

    def get_pid_of_inode(self, inode):
        # Only build the mapping of socket inodes->pids once, in case we
        # have a lot of sockets to look for
        if self.all_pids_scanned or inode in self.pid_by_inode:
            return self.pid_by_inode.get(inode)
        # Initialize the pid generator once
        self.pid_list = self.pid_list or self.all_pids()
        found_pid = None
        try:
            while True:
                # This will pick up from the last pid we got to on a previous
                # call of this function
                pid = next(self.pid_list)
                path = os.path.join("/proc", pid)
                try:
                    for fd in os.listdir(os.path.join(path, "fd")):
                        try:
                            mtch = SOCKET_FD_PAT.match(os.readlink(os.path.join(path, "fd", fd)))
                            if mtch:
                                self.pid_by_inode[mtch.group(1)] = int(pid)
                                if mtch.group(1) == inode:
                                    # We still need to finish looping through all fds for this pid
                                    # in case it has other sockets we want to find later
                                    found_pid = pid
                        except (OSError, ValueError):
                            pass
                except OSError:
                    pass
                if found_pid:
                    return found_pid
        except StopIteration:
            # We got to the end of the pid list, and haven't found the inode we
            # were looking for (which usually means it was owned by the kernel)
            return None

    def collect(self):
        def _ip(s):
            if len(s) == 32:
                """IPv6"""
                ret = ""
                for ip_block in [s[i : i + 8] for i in range(0, len(s), 8)]:
                    for j in range(len(ip_block) - 1, 0, -2):
                        ret += ip_block[j - 1 : j + 1]
                        if j == 5:
                            ret += ":"
                    ret += ":"

                ret = ret[:-1]
                packed = socket.inet_pton(socket.AF_INET6, ret)
                return socket.inet_ntop(socket.AF_INET6, packed)

            else:
                """IPv4"""
                ip = [
                    (str(int(s[6:8], 16))),
                    (str(int(s[4:6], 16))),
                    (str(int(s[2:4], 16))),
                    (str(int(s[0:2], 16))),
                ]
                return ".".join(ip)

        def _convertip_port(array):
            host, port = array.split(":")
            return _ip(host), int(port, 16)


        def _is_local_addr(s):
            host, _ = _convertip_port(s)
            """ This could probably be refined a tad - if only netifaces was in stdlib
                or interface names weren't so varied today..
            """
            return host in ["0.0.0.0", "::", "::1"] or host.startswith("127.0.0")

        listen_state = "0A"
        ret = []
        for proto in ["tcp", "udp", "tcp6", "udp6"]:
            try:
                with open(os.path.join("/proc/net/", proto), "r") as fp:
                    lines = fp.readlines()
                    lines.pop(0)
                    for line in lines:
                        line_segments = [s for s in line.split() if s]
                        if "tcp" in proto and line_segments[3] != listen_state:
                            continue

                        if "udp" in proto and not _is_local_addr(line_segments[2]):
                            """Only care about UDP sockets where remote addr is local (listening)"""
                            continue

                        host, port = _convertip_port(line_segments[1])
                        pid = self.get_pid_of_inode(line_segments[9])
                        ret.append({"port": port, "host": host, "protocol": proto, "pid": pid})
            except IOError:
                continue

        return ret
