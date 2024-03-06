# GUIDE TO RUNNING MOLECULE TESTS
=================================

Molecule tests are provided to verify the basic functionality of joining devices
to the Intensive domain - however due to corporate network restrictions, they
cannot normally be run from user workstations (as the Intensive domain is not
accessible)\
Therefore tests will have to be run from a device that does have access to the
Intensive domain (typically, one of the dedicated servers in a test account will
be suitable for this)

## Server setup
In order to run the tests, the following requirements must be met on the test
device:
 - Python 3.8
 - Ansible 2.11
 - Docker

For a test server running some flavour of EL8, the following recipe can be used:

```bash
## Install python 3.8 + a few python libraries
dnf module enable python38
dnf module install python38
dnf install python3-virtualenv python38-devel python38-netaddr \
    python38-pyyaml python38-requests python38-resolvelib python38-six \
    python38-urllib3 python38-wheel

## Install, configure & test docker
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf install docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
docker run hello-world
docker rm $(docker ps -aq)

## Create & activate a virtualenv, install necessary python modules
virtualenv-3 --python=python3.8 ~/venv/playbooks
source ~/venv/playbooks/bin/activate
pip3 install ansible==4.10.0 molecule[docker] dnspython
```

## Running the test scenarios
The molecule tests will actually join the test containers to the Intensive domain
(temporarily), so you need to provide your Intensive username & password to them
to allow them to do this\
That is done via environment variables:
```bash
export INTENSIVE_USERNAME=user@intensive.int
export INTENSIVE_PASSWORD=my_password
```
You can also provide your .cust credentials to test that they have access (as long
as you have granted yourself access to the test account via
https://selfservice.intensive.int/ad/customeraccess), and credentials of a user
account within the joined domain to test the customer will have access too\
This is also done via environment variables - however you can provide a file for
molecule to read all of the environment variables from\
Create the file `.env.yml` in the root directory of the role (i.e. the same place
as where this file is located):
```
---
INTENSIVE_USERNAME: user@intensive.int
INTENSIVE_PASSWORD: <intensive_password>
INTENSIVE_CUST_USERNAME: user.cust@intensive.int
INTENSIVE_CUST_PASSWORD: <intensive.cust_password>
DOMAIN_TEST_USERNAME: 957072-testuser
DOMAIN_TEST_PASSWORD: <testuser_password>
...
```

Note that the `cleanup` molecule playbook will delete the devices from the domain
again (and thus also requires the username & password to be set)

The default scenario will join to the lon.intensive.int domain on account 957072\
If you want to use a different account and site for some reason, you can override
the defaults when running molecule (or you can set the values in your `.env.yml`
file):
```bash
DC=ORD rs_customer=27329 molecule test
```

You can also test joining the GlobalRS.rack.space domain by setting the
`JOINTYPE` environmental variable:
```bash
JOINTYPE=globalrs molecule test
```

The 'customer' join type can also be tested in a similar fashion:
```bash
JOINTYPE=customer molecule test
```
Note that by default, this test works by joining to the GlobalRS.rack.space domain,
but doesn't configure the hosts to allow login by Intensive credentials (so only the
test user account will be able to login).\
It also can't set `/etc/resolv.conf` up (because that file cannot be changed in a
docker container, due to the fundamentals of how docker works), so it will be written
as `/etc/resolv.conf.molecule` instead
