from dataclasses import dataclass
from typing import Dict, List, Optional

import pylo


class PortMap:
    def __init__(self):
        self._tcp_map = []
        self._udp_map = []
        self._protocol_map = {}

    def add(self, protocol, start_port: int, end_port: int = None, skip_recalculation=False):
        try:
            protocol = pylo.convert_protocol(protocol)
        except Exception as e:
            raise pylo.PyloEx("Unsupported protocol name '{}'".format(protocol)) from e

        if not pylo.Protocol.has_value(protocol):
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
        return self.protocol == pylo.TCP

    def is_udp(self) -> bool:
        return self.protocol == pylo.UDP

    @classmethod
    def create_from_json(cls, data: Dict):
        return cls(
            protocol=pylo.convert_protocol(data['proto']),
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
        if self.protocol == pylo.TCP or self.protocol == pylo.UDP:
            protocol_name = pylo.Protocol(self.protocol).name.lower()
            service_value = ports
        return '{}/{}'(protocol_name, service_value) if protocol_first \
            else '{}/{}'(service_value, protocol_name)


class Service(pylo.ReferenceTracker):

    def __init__(self, name: str, href: str, owner: 'pylo.ServiceStore'):
        pylo.ReferenceTracker.__init__(self)

        self.owner: 'pylo.ServiceStore' = owner
        self.name: str = name
        self.href: str = href

        self.entries: List['pylo.Service'] = []

        self.description: Optional[str] = None
        self.processName: Optional[str] = None

        self.deleted: bool = False

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


class ServiceStore(pylo.Referencer):
    itemsByName: Dict[str, Service]
    itemsByHRef: Dict[str, Service]

    def __init__(self, owner):
        """:type owner: pylo.Organization"""
        pylo.Referencer.__init__(self)
        self.owner = owner
        self.itemsByHRef = {}
        self.itemsByName = {}

        self.special_allservices = pylo.Service('All Services', '/api/v1/orgs/1/sec_policy/draft/services/1', self)

    def load_services_from_json(self, json_list):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise Exception("Cannot find 'value'/name or href for service in JSON:\n" + pylo.nice_json(json_item))
            new_item_name = json_item['name']
            new_item_href = json_item['href']

            new_item = pylo.Service(new_item_name, new_item_href, self)
            new_item.load_from_json(json_item)

            if new_item_href in self.itemsByHRef:
                raise Exception("A service with href '%s' already exists in the table", new_item_href)

            self.itemsByHRef[new_item_href] = new_item
            self.itemsByName[new_item_name] = new_item

            pylo.log.debug("Found service '%s' with href '%s'", new_item_name, new_item_href)
