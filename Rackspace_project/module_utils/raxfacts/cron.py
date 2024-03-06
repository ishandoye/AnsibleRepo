import os
import re

from ansible.module_utils.facts.utils import get_file_lines
from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector


excludes = "#|SHELL|PATH|MAILTO|HOME"


class CronFactsCollector(BaseRaxFactsCollector):

    name = "cron"

    def collect(self):
        facts = {}

        # Files are direct, directories are listed (recursively)
        KNOWN_LOCATIONS = [
            (UserSpool, "/var/spool/cron/crontabs/"),
            (UserSpool, "/var/spool/cron/"),
            (SystemTab, "/etc/crontab"),
            (SystemTab, "/etc/cron.d/"),
            (RunParts, "/etc/cron.hourly"),
            (RunParts, "/etc/cron.daily"),
            (RunParts, "/etc/cron.weekly"),
            (RunParts, "/etc/cron.monthly"),
        ]

        for cron_path in KNOWN_LOCATIONS:
            (cls, location) = cron_path
            for key, value in cls(location).crons.items():
                facts.setdefault(key, []).extend(value)

        return facts


class UserSpool:
    """Generates all user crontabs"""

    def __init__(self, loc):
        self.loc = loc
        self.crons = {}
        self.all()

    def all(self):
        """Obtain all crons for a given location"""
        self.crons["user_spool"] = []
        for username in listdir(self.loc):
            self.crons["user_spool"].append(generate(os.path.join(self.loc, username)))


class SystemTab:
    """Generates system tabs"""

    def __init__(self, loc):
        self.loc = loc
        self.crons = {}
        self.all()

    def all(self):
        """Obtain all crons for a given location"""
        self.crons["system_tab"] = []
        if os.path.isdir(self.loc):
            for item in listdir(self.loc):
                if item[0] == ".":
                    continue
                self.crons["system_tab"].append(generate(os.path.join(self.loc, item)))
        elif os.path.isfile(self.loc):
            self.crons["system_tab"].append(generate(self.loc))


class RunParts:
    """Generates run-parts file locations"""

    def __init__(self, loc):
        self.loc = loc
        self.crons = {}
        self.all()

    def all(self):
        """Obtain all crons for a given location"""
        self.crons["run_parts"] = []
        if os.path.isdir(self.loc):
            for item in listdir(self.loc):
                if item[0] == ".":
                    continue
                self.crons["run_parts"].append(
                    {"filename": os.path.join(self.loc, item)}
                )
        elif os.path.isfile(self.loc):
            self.crons["run_parts"].append({"filename": self.loc})


def listdir(loc):
    """Returns a list of files in a given directory"""
    try:
        return os.listdir(loc)
    except OSError:
        return []


def generate(path):
    """Generates a dict containing all crons for a specified path"""
    item = {}
    item["filename"] = path
    item["jobs"] = []

    for line in get_file_lines(path):
        line = line.strip()
        if line and not re.match(excludes, line):
            item["jobs"].append(line.rstrip("\n"))

    return item
