import os
import sys

PY2 = sys.version_info.major == 2
PY3 = sys.version_info.major == 3

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ["MOLECULE_INVENTORY_FILE"]
).get_hosts("all")


def test_hosts_file(host):
    f = host.file("/etc/hosts")
    assert f.exists
    assert f.user == "root"
    assert f.group == "root"


def test_user(host):
    user = host.user("molecule_user")
    assert user.exists
    assert user.shell == "/sbin/nologin"
    assert user.home == "/home/chroot/molecule_user"


def test_group(host):
    group = host.group("sftponly")
    assert group.exists


def test_chroot_permissions(host):
    chroot_dir = host.file("/home/chroot")
    assert chroot_dir.exists
    assert chroot_dir.user == "root"
    assert chroot_dir.group == "root"
    if PY2:
        assert oct(chroot_dir.mode) == "0755"
    elif PY3:
        assert oct(chroot_dir.mode) == "0o755"


def test_homedir_permissions(host):
    homedir = host.file("/home/chroot/molecule_user")
    assert homedir.exists
    assert homedir.user == "root"
    assert homedir.group == "root"
    if PY2:
        assert oct(homedir.mode) == "0755"
    elif PY3:
        assert oct(homedir.mode) == "0o755"


def test_mountdir(host):
    mountdir = "/home/chroot/molecule_user/sftp_upload"
    assert host.mount_point(mountdir).exists
    mountdir_permissions = host.file(mountdir)
    assert mountdir_permissions.user == "root"
    assert mountdir_permissions.group == "sftponly"
    if PY2:
        assert oct(mountdir_permissions.mode) == "02775"
    elif PY3:
        assert oct(mountdir_permissions.mode) == "0o2775"


def test_webdir(host):
    webdir = host.file("/var/www/vhosts/example.com")
    assert webdir.exists
    assert webdir.user == "root"
    assert webdir.group == "sftponly"
    if PY2:
        assert oct(webdir.mode) == "02775"
    elif PY3:
        assert oct(webdir.mode) == "0o2775"
