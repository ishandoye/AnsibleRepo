# THIS PROJECT HAS BEEN MOVED INTO STEPLADDER

This project is now archived, and is being maintained as part of [Stepladder](https://github.rackspace.com/GTSLAE/mono/tree/devel/stepladder/wrappers/playbooks)

Please [report](https://github.rackspace.com/GTSLAE/mono/issues/new/choose) any new issues in that repository

---

# Ansible Playbooks

A bunch of peer reviewed playbooks, useful to Linux Techs for Rackspace customers. Stuff here is considered generic enough to be useful to be repeatedly used. Nothing here should contain anything customer specific.

A tar archive of this repo updated hourly is available at: https://iaw.rax.io/tar/iaw-playbooks.tar.gz

## How to use

### Quick and easy

Please be aware that these instructions don't follow best practices but will get you started in less than 5 min.

1. [Add a new ssh-key into your GitHub account](https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account)

1. Add your new ssh-key to your ssh-agent
    ```
    ssh-add /path/to/your/new/ssh-private-key
    ```

1. Connect to your favorite [Bastion server](https://one.rackspace.com/display/rackertools/Next+Gen+Bastions)

1. Clone the repository and get into the directory:
    ```
    git clone git@github.rackspace.com:SupportTools/playbooks.git
    cd playbooks
    ```

1. Use any of the provided playbooks to execute it against some devices. Example:
    ```
    TARGETS=200001,200002 \
      ansible-playbook -i $(which ht) \
        nimbus.yml
    ```

There is a README.md in each role's directory with further details regarding functionality and how to use it.


### Incorporating roles

To use these playbooks or roles within your own work, follow these examples:

To incorporate these roles, your playbook must be able to find them. Assuming you have this repo in location /home/myuser/playbooks, you have two options:

1. #### Run your playbook from the playbook directory

1. #### Modify roles_path in your ansible.cfg
    ```ini
    roles_path = /home/myuser/playbooks/roles
    ```
    and then reference these roles directly

    ```yaml
    # Single role
    tasks:
    - include_role:
        name: nimbus

    # Multiple roles
    tasks:
    - include_role:
        name: "{{ item }}"
      loop:
      - rhn
      - nimbus
      - sophos
    ```

### Incorporating playbooks in your playbook

```
- include: /home/myuser/playbooks/example.playbook.yml
```

## Using Ansible playbooks on Rackspace devices
See [Using Ansible with Hammertime](https://github.rackspace.com/GTSLAE/mono/blob/devel/hammertime/ANSIBLE.md) for more information.

## Contributing

Pull Requests welcome, any changes must be reviewed by another contributor.

See [CONTRIBUTING](.github/CONTRIBUTING.md) for Ansible coding standards to adhere to.


## Maintainers
  - [GTS Linux Automation Engineers]( mailto:gts-linux-automation-engineers@rackspace.com )
  - [GTS Linux Systems Engineers]( mailto:gts-linux-systems-engineers@rackspace.com )
