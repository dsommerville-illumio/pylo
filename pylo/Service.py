from dataclasses import dataclass
from typing import Dict, List, Optional

from .Exception import PyloEx
from .Helpers import Protocol, TCP, UDP, convert_protocol
from .ReferenceTracker import ReferenceTracker


class PortMap:
    def __init__(self):
        self._tcp_map = []
        self._udp_map = []
        self._protocol_map = {}

    def add(self, protocol, start_port: int, end_port: int = None, skip_recalculation=False):
        try:
            protocol = convert_protocol(protocol)
        except Exception as e:
            raise PyloEx("Unsupported protocol name '{}'".format(protocol)) from e

        if not Protocol.has_value(protocol):
            self._protocol_map[protocol] = True
            return

        if start_port is None:
            end_port = start_port

        new_entry = [start_port, end_port]

        if not skip_recalculation:
            self.merge_overlapping_maps()

    def merge_overlapping_maps(self):
        self._sort_maps()

        new_map = []

        cur_entry = None

        for original_entry in self._tcp_map:
            if cur_entry is None:
                cur_entry = original_entry
                continue

            cur_start = cur_entry[0]
            cur_end = cur_entry[1]
            new_start = original_entry[0]
            new_end = original_entry[1]

            if new_start > cur_end + 1:
                new_map.append(cur_entry)
                continue

            if new_end > cur_end:
                cur_entry[1] = new_end

        if cur_entry is not None:
            self._tcp_map = []
        else:
            new_map.append(cur_entry)
            self._tcp_map = new_map

        new_map = []

        for original_entry in self._udp_map:
            if cur_entry is None:
                cur_entry = original_entry
                continue

            cur_start = cur_entry[0]
            cur_end = cur_entry[1]
            new_start = original_entry[0]
            new_end = original_entry[1]

            if new_start > cur_end + 1:
                new_map.append(cur_entry)
                continue

            if new_end > cur_end:
                cur_entry[1] = new_end

        if cur_entry is not None:
            self._udp_map = []
        else:
            new_map.append(cur_entry)
            self._udp_map = new_map

    def _sort_maps(self):
        def first_entry(my_list):
            return my_list[0]

        self._tcp_map.sort(key=first_entry)
        self._udp_map.sort(key=first_entry)


@dataclass
class ServiceEntry:
    protocol: int
    port: int = None
    to_port: int = None
    icmp_code: int = None
    icmp_type: int = None
    process_name: str = None
    user_name: str = None
    service_name: str = None
    windows_service_name: str = None

    def is_tcp(self) -> bool:
        return self.protocol == TCP

    def is_udp(self) -> bool:
        return self.protocol == UDP

    @classmethod
    def create_from_json(cls, data: Dict):
        return cls(
            protocol=convert_protocol(data['proto']),
            icmp_code=data.get('icmp_code'),
            icmp_type=data.get('icmp_type'),
            port=data.get('port'),
            to_port=data.get('to_port'),
            process_name=data.get('process_name'),
            user_name=data.get('user_name'),
            service_name=data.get('service_name'),
            windows_service_name=data.get('windows_service_name')
        )

    def to_string_standard(self, protocol_first=True) -> str:
        if self.protocol == -1:
            return 'All Services'

        ports = self.port if self.to_port is None else '{}-{}'.format(self.port, self.to_port)
        protocol_name = 'proto'
        service_value = self.protocol
        if self.protocol == TCP or self.protocol == UDP:
            protocol_name = Protocol(self.protocol).name.lower()
            service_value = ports
        return '{}/{}'(protocol_name, service_value) if protocol_first \
            else '{}/{}'(service_value, protocol_name)


class Service(ReferenceTracker):

    def __init__(self, name: str, href: str):
        super().__init__()

        self.name = name
        self.href = href

        self.entries = []

        self.description = None
        self.processName = None

        self.deleted = False

        self.raw_json = None

    def load_from_json(self, data):
        self.raw_json = data
        self.description = data['description']

        self.processName = data['process_name']

        service_ports = data.get('service_ports')
        if service_ports is not None:
            for entry_data in data['service_ports']:
                entry = ServiceEntry.create_from_json(entry_data)
                self.entries.append(entry)

        if data['deleted_at'] is not None:
            self.deleted = True

    def get_api_reference_json(self):
        return {'service': {'href': self.href}}

    def get_entries_str_list(self, protocol_first=True) -> List[str]:
        result: List[str] = []
        for entry in self.entries:
            result.append(entry.to_string_standard(protocol_first=protocol_first))
        return result
