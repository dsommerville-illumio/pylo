from typing import Dict, Optional

import pylo


class IPList(pylo.ReferenceTracker):

    """
    :type owner: IPListStore
    :type description: str|None
    :type raw_entries: dict[str,str]
    """
    name: str
    href: str

    def __init__(self, name: str, href: str, owner: 'pylo.IPListStore', description=None):
        """
        :type name: str
        :type href: str
        :type owner: IPListStore
        """
        pylo.ReferenceTracker.__init__(self)
        self.owner = owner
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
            raise pylo.PyloEx("cannot find 'ip_ranges' in IPList JSON:\n" + pylo.nice_json(json_input))

        for ip_range in ip_ranges_array:
            from_ip = ip_range.get("from_ip")
            if from_ip is None:
                raise pylo.PyloEx("cannot find 'from_ip' in IPList JSON:\n" + pylo.nice_json(ip_range))

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

    def get_ip4map(self) -> pylo.IP4Map:
        map = pylo.IP4Map()

        for entry in self.raw_entries:
            if entry[0] == '!':
                map.substract_from_text(entry[1:], ignore_ipv6=True)
            else:
                map.add_from_text(entry, ignore_ipv6=True)

        return map

    def get_raw_entries_as_string_list(self, separator=',') -> str:
        return pylo.string_list_to_text(self.raw_entries.values(), separator=separator)

    def get_api_reference_json(self):
        return {'iplist': {'href': self.href}}


class IPListStore:

    itemsByName: Dict[str, 'pylo.IPList']
    itemsByHRef: Dict[str, 'pylo.IPList']

    def __init__(self, owner: 'pylo.Organization'):
        self.owner = owner
        self.itemsByHRef = {}
        self.itemsByName = {}


    def count(self):
        return len(self.itemsByHRef)

    def load_iplists_from_json(self, json_list):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise Exception("Cannot find 'value'/name or href for iplist in JSON:\n" + pylo.nice_json(json_item))
            new_iplist_name = json_item['name']
            new_iplist_href = json_item['href']
            new_iplist_desc = json_item.get('description')

            new_iplist = pylo.IPList(new_iplist_name, new_iplist_href, self, new_iplist_desc)
            new_iplist.load_from_json(json_item)

            if new_iplist_href in self.itemsByHRef:
                raise Exception("A iplist with href '%s' already exists in the table", new_iplist_href)

            self.itemsByHRef[new_iplist_href] = new_iplist
            self.itemsByName[new_iplist_name] = new_iplist

            pylo.log.debug("Found iplist '%s' with href '%s'", new_iplist_name, new_iplist_href)

    def find_by_href(self, href: str) -> 'pylo.IPList':
        return self.itemsByHRef.get(href)

    def find_by_name(self, name: str) -> Optional['pylo.IPList']:
        return self.itemsByName.get(name)

