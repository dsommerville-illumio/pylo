import re
from packaging import version

from .Exception import PyloEx

version_regex = re.compile(r"^(?P<major>[0-9]+)\.(?P<middle>[0-9]+)\.(?P<minor>[0-9]+)(-(?P<build>[0-9]+))?([-]?[uHhcs][0-9]+)?([-]?dev)?$")


class SoftwareVersion:

    def __init__(self, version_string: str):
        self.version_string = version_string

        self.is_unknown = False
        self.major = 0
        self.middle = 0
        self.minor = 0
        self.build = 0

        if version_string.lower() == 'unknown':
            self.is_unknown = True
            self.semantic_version = '0.0.0-0'
            return

        match = version_regex.match(version_string)

        if match is None:
            raise PyloEx("version_string has invalid version format: {}".format(version_string))

        self.major = int(match.group("major"))
        self.middle = int(match.group("middle"))
        self.minor = int(match.group("minor"))
        build = match.group("build")
        if build is None:
            self.build = 0
        else:
            self.build = int(match.group("build"))
        self.semantic_version = '{}.{}.{}-{}'.format(self.major, self.middle, self.minor, self.build)

    def __lt__(self, other):
        return version.parse(self.semantic_version) < version.parse(other.semantic_version)

    def __le__(self, other):
        return version.parse(self.semantic_version) <= version.parse(other.semantic_version)

    def __gt__(self, other):
        return version.parse(self.semantic_version) > version.parse(other.semantic_version)

    def __ge__(self, other):
        return version.parse(self.semantic_version) >= version.parse(other.semantic_version)

    def __eq__(self, other):
        return version.parse(self.semantic_version) == version.parse(other.semantic_version)

    def generate_str_from_numbers(self):
        return "{}.{}.{}-{}".format(self.major, self.middle, self.minor, self.build)
