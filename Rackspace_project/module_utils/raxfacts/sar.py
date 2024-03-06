import glob
import os

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


class SarFactsCollector(BaseRaxFactsCollector):

    name = 'sar'

    def collect(self):
        sar_exe = self.module.get_bin_path('sar')
        sa_dir = '/var/log/sa'  # RedHat Location
        if os.path.isdir('/var/log/sysstat'):
            sa_dir = '/var/log/sysstat'  # Debian Location

        sar_files = glob.glob(sa_dir + '/sa??')

        cpu_sar = []
        mem_sar = []

        grep_filter = '"user|^$|Average|RESTART|kbmemfree"'
        lc_time_old = os.environ.get('LC_TIME')
        s_time_format_old = os.environ.get('S_TIME_FORMAT')
        os.environ['LC_TIME'] = 'C'
        os.environ['S_TIME_FORMAT'] = 'ISO'

        for sar_file in sar_files:
            ccmd = sar_exe + ' -f ' + sar_file + ' | egrep -v ' + grep_filter
            cpu_sar_tmp = self.module.run_command(ccmd,
                                                  use_unsafe_shell=True)[1].strip().split('\n')
            sardate = cpu_sar_tmp[0].split()[3]
            cpu_sar += [sardate + "T" + line for line in cpu_sar_tmp[1:]]
            mcmd = sar_exe + ' -r -f ' + sar_file + ' | egrep -v ' + grep_filter
            mem_sar_tmp = self.module.run_command(mcmd,
                                                  use_unsafe_shell=True)[1].strip().split('\n')
            mem_sar += [sardate + "T" + line for line in mem_sar_tmp[1:]]

        if lc_time_old is None:
            del os.environ['LC_TIME']
        else:
            os.environ['LC_TIME'] = lc_time_old

        if s_time_format_old is None:
            del os.environ['S_TIME_FORMAT']
        else:
            os.environ['S_TIME_FORMAT'] = s_time_format_old

        cpu_vals = []
        for line in sorted(cpu_sar):
            vals = line.split()
            cpu_vals.append(float(vals[2]))

        mem_vals = []
        for line in sorted(mem_sar):
            vals = line.split()
            mem_pct = 100 * ((float(vals[2]) - float(vals[4]) - float(
                vals[5])) / (float(vals[1]) + float(vals[2])))
            mem_vals.append(mem_pct)

        cpu_max_pct = round(max(cpu_vals), 2)
        cpu_min_pct = round(min(cpu_vals), 2)
        cpu_avg_pct = round(sum(cpu_vals) / len(cpu_vals), 2)
        mem_max_pct = round(max(mem_vals), 2)
        mem_min_pct = round(min(mem_vals), 2)
        mem_avg_pct = round(sum(mem_vals) / len(mem_vals), 2)

        return {
            'cpu_max_pct': cpu_max_pct,
            'cpu_min_pct': cpu_min_pct,
            'cpu_avg_pct': cpu_avg_pct,
            'mem_max_pct': mem_max_pct,
            'mem_min_pct': mem_min_pct,
            'mem_avg_pct': mem_avg_pct,
        }
