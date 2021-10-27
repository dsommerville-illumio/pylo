from .Exception import PyloEx
from .Helpers import nice_json, string_list_to_text
from .IPMap import IP4Map
from .ReferenceTracker import ReferenceTracker


class IPList(ReferenceTracker):

    def __init__(self, name: str, href: str, description=None):
        super().__init__(self)
        self.name = name
        self.href = href
        self.description = description
        self.raw_json = None
        self.raw_entries = {}

    def count_entries(self):
        return len(self.raw_entries)

    def load_from_json(self, json_input):
        self.raw_json = json_input

        ip_ranges_array = json_input.get("ip_ranges")
        if ip_ranges_array is None:
            raise PyloEx("cannot find 'ip_ranges' in IPList JSON:\n" + nice_json(json_input))

        for ip_range in ip_ranges_array:
            from_ip = ip_range.get("from_ip")
            if from_ip is None:
                raise PyloEx("cannot find 'from_ip' in IPList JSON:\n" + nice_json(ip_range))

            slash_pos = from_ip.find('/')
            if slash_pos < 0:
                to_ip = ip_range.get("to_ip")
                if to_ip is None:
                    entry = from_ip
                else:
                    if len(to_ip) < 4:
                        entry = from_ip + "/" + to_ip
                    else:
                        entry = from_ip + '-' + to_ip
            else:
                entry = from_ip

            exclusion = ip_range.get('exclusion')
            if exclusion is not None and exclusion:
                entry = '!' + entry

            self.raw_entries[entry] = entry

    def get_ip4map(self) -> IP4Map:
        map = IP4Map()

        for entry in self.raw_entries:
            if entry[0] == '!':
                map.substract_from_text(entry[1:], ignore_ipv6=True)
            else:
                map.add_from_text(entry, ignore_ipv6=True)

        return map

    def get_raw_entries_as_string_list(self, separator=',') -> str:
        return string_list_to_text(self.raw_entries.values(), separator=separator)

    def get_api_reference_json(self):
        return {'iplist': {'href': self.href}}
