import os

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class ProcessFactsCollector(BaseRaxFactsCollector):

    name = 'running_processes'

    def collect(self):
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        ret = {}
        for pid in pids:
            name = None
            try:
                fp = open(os.path.join('/proc', pid, 'comm'), 'r')
                name = fp.read().strip('\n')
                fp.close()
            except IOError:
                """ Process has vanished since we got PIDs """
                if not os.path.isdir('/proc/' + pid):
                    continue
                """ Not all kernels supports everything, so if the process is still around,
                we continue and return what we can. """

            try:
                fp = open(os.path.join('/proc', pid, 'cmdline'), 'r')
                b_cmdline = fp.read()
                fp.close()
                cmdline = ''
                if b_cmdline:
                    for c in b_cmdline:
                        if ord(c) > 31 or ord(c) == 9:
                            cmdline += c
                        else:
                            cmdline += ' '

                if cmdline:
                    cmdline = cmdline.strip(' ')
                else:
                    cmdline = None

            except IOError:
                if not os.path.isdir('/proc/' + pid):
                    continue

            try:
                exe = os.readlink(os.path.join('/proc', pid, 'exe'))
            except OSError:
                exe = None

            rss = None
            try:
                fp = open(os.path.join('/proc', pid, 'status'), 'r')
                for line in fp.readlines():
                    if line.lower().startswith('vmrss'):
                        rss = int(line.split()[1])
                fp.close()
            except IOError:
                if not os.path.isdir('/proc/' + pid):
                    continue
            except ValueError:
                rss = None

            owner = None
            try:
                st = os.stat(os.path.join('/proc', pid))
                owner = st.st_uid

            except IOError:
                if not os.path.isdir('/proc/' + pid):
                    continue

            ret[pid] = {
                'name': name,
                'pid': int(pid),
                'cmdline': cmdline,
                'exe': exe,
                'rss': rss,
                'owner': owner,
            }

        return ret
