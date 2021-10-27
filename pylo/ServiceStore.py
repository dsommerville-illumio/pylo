from typing import Dict

from .Helpers import nice_json
from .ReferenceTracker import Referencer
from .Service import Service
from .tmp import log


class ServiceStore(Referencer):
    items_by_name: Dict[str, Service]
    items_by_href: Dict[str, Service]

    def __init__(self, owner):
        super().__init__(self)
        self.owner = owner
        self.items_by_href = {}
        self.items_by_name = {}

        self.special_allservices = Service('All Services', '/api/v1/orgs/1/sec_policy/draft/services/1', self)

    def load_services_from_json(self, json_list):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise Exception("Cannot find 'value'/name or href for service in JSON:\n" + nice_json(json_item))
            new_item_name = json_item['name']
            new_item_href = json_item['href']

            new_item = Service(new_item_name, new_item_href, self)
            new_item.load_from_json(json_item)

            if new_item_href in self.items_by_href:
                raise Exception("A service with href '%s' already exists in the table", new_item_href)

            self.items_by_href[new_item_href] = new_item
            self.items_by_name[new_item_name] = new_item

            log.debug("Found service '%s' with href '%s'", new_item_name, new_item_href)
