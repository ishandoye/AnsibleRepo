import grp
import pwd
import spwd
from datetime import date, datetime, timedelta

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector
from ansible.module_utils.six import PY3


class UserGroupFactsCollector(BaseRaxFactsCollector):

    name = 'users_groups'
    aliases = ['users', 'groups']

    def sudo_privileges_exist(self, username):
        priv_exists = False
        sudo_path = self.module.get_bin_path("sudo")
        if sudo_path:
            args = [sudo_path, "-l", "-U", username]
            rc, stdout, _ = self.module.run_command(args)
            if rc == 0 and stdout:
                if "is not allowed to run sudo" not in stdout:
                    priv_exists = True
        return priv_exists

    def collect(self):
        ret = {
            'users': [],
            'groups': []
        }

        for user in pwd.getpwall():
            spwd_data = spwd.getspnam(user.pw_name)
            if PY3:
                pw_locked = spwd_data.sp_pwdp and spwd_data.sp_pwdp.startswith('!')
            else:
                pw_locked = spwd_data.sp_pwd and spwd_data.sp_pwd.startswith('!')

            acct_expired = False
            expire_date = 'Never'
            if spwd_data.sp_expire != -1:
                expire_date = (datetime(1970,1,1,0,0) + timedelta(spwd_data.sp_expire)).date()
                if datetime.today().date() >= expire_date:
                    acct_expired = True

            ret['users'].append({
                'name': user.pw_name,
                'uid': user.pw_uid,
                'gid': user.pw_gid,
                'info': user.pw_gecos,
                'home': user.pw_dir,
                'shell': user.pw_shell,
                'account_expired': acct_expired,
                "account_expire_date": expire_date.strftime("%Y-%m-%d")
                if isinstance(expire_date, date)
                else expire_date,
                'password_locked': pw_locked,
                'sudo_privileges_detected': self.sudo_privileges_exist(user.pw_name),
            })

        for group in grp.getgrall():
            members = group.gr_mem
            for user in [user for user in ret['users'] if user['gid'] == group.gr_gid]:
                members.append(user['name'])

            ret['groups'].append({
                'name': group.gr_name,
                'gid': group.gr_gid,
                'members': group.gr_mem
            })

        return ret
