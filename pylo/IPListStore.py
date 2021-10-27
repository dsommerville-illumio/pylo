from typing import Dict

from .Helpers import nice_json
from .IPList import IPList
from .tmp import log

class IPListStore:

    items_by_name: Dict[str, IPList]
    items_by_href: Dict[str, IPList]

    def __init__(self):
        self.items_by_href = {}
        self.items_by_name = {}


    def count(self):
        return len(self.items_by_href)

    def load_iplists_from_json(self, json_list):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise Exception("Cannot find 'value'/name or href for iplist in JSON:\n" + nice_json(json_item))
            new_iplist_name = json_item['name']
            new_iplist_href = json_item['href']
            new_iplist_desc = json_item.get('description')

            new_iplist = IPList(new_iplist_name, new_iplist_href, self, new_iplist_desc)
            new_iplist.load_from_json(json_item)

            if new_iplist_href in self.items_by_href:
                raise Exception("A iplist with href '%s' already exists in the table", new_iplist_href)

            self.items_by_href[new_iplist_href] = new_iplist
            self.items_by_name[new_iplist_name] = new_iplist

            log.debug("Found iplist '%s' with href '%s'", new_iplist_name, new_iplist_href)

    def find_by_href(self, href: str) -> IPList:
        return self.items_by_href.get(href)

    def find_by_name(self, name: str) -> IPList:
        return self.items_by_name.get(name)
