from datetime import datetime

from .Exception import PyloEx
from .ReferenceTracker import ReferenceTracker
from .SoftwareVersion import SoftwareVersion
from .tmp import log


class VENAgent(ReferenceTracker):

    def __init__(self, href: str):
        super().__init__()
        self.href = href

        self.software_version = None
        self._last_heartbeat = None

        self._status_security_policy_sync_state = None
        self._status_security_policy_applied_at = None
        self._status_rule_count = None

        self.mode = None

        self.raw_json = None

    def _get_date_from_json(self, prop_name_in_json: str) -> datetime:
        status_json = self.raw_json.get('status')
        if status_json is None:
            return None

        prop_value = status_json.get(prop_name_in_json)
        if prop_value is None:
            return None

        return datetime.strptime(prop_value, "%Y-%m-%dT%H:%M:%S.%fZ")

    def load_from_json(self, data):
        self.raw_json = data

        status_json = data.get('status')
        if status_json is None:
            raise PyloEx("Cannot find VENAgent status in JSON from '{}'".format(self.href))

        version_string = status_json.get('agent_version')
        if version_string is None:
            raise PyloEx("Cannot find VENAgent version from '{}'".format(self.href))
        self.software_version = SoftwareVersion(version_string)
        if self.software_version.is_unknown:
            log.warn("Agent {} has unknown software version: {}".format(
                self.href,
                self.software_version.version_string)
            )

        self._status_security_policy_sync_state = status_json.get('security_policy_sync_state')

        self._status_rule_count = status_json.get('firewall_rule_count')

        config_json = data.get('config')
        if config_json is None:
            raise PyloEx("Cannot find Agent's config in JSON", data)

        self.mode = config_json.get('mode')
        if self.mode is None:
            raise PyloEx("Cannot find Agent's mode in config JSON", config_json)

        if self.mode == 'illuminated':
            log_traffic = config_json.get('log_traffic')
            if log_traffic:
                self.mode = "test"
            else:
                self.mode = "build"

    def get_last_heartbeat_date(self) -> datetime:
        if self._last_heartbeat is None:
            self._last_heartbeat = self._get_date_from_json('last_heartbeat_on')
        return self._last_heartbeat

    def get_status_security_policy_applied_at(self):
        if self._status_security_policy_applied_at is None:
            self._status_security_policy_applied_at = self._get_date_from_json('security_policy_applied_at')
        return self._status_security_policy_applied_at

    def get_status_security_policy_sync_state(self):
        return self._status_security_policy_sync_state
