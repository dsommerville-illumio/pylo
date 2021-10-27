from typing import Dict

from .Exception import PyloEx
from .Helpers import nice_json
from .tmp import log
from .VirtualService import VirtualService


class VirtualServiceStore:

    def __init__(self):
        self.items_by_href: Dict[str, VirtualService] = {}
        self.items_by_name: Dict[str, VirtualService] = {}

    def load_virtualservices_from_json(self, json_list):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise PyloEx(
                    "Cannot find 'value'/name or href for VirtualService in JSON:\n" + nice_json(json_item))

            new_item_name = json_item['name']
            new_item_href = json_item['href']

            new_item = VirtualService(new_item_name, new_item_href, self)
            new_item.load_from_json(json_item)

            if new_item_href in self.items_by_href:
                raise PyloEx("A VirtualService with href '%s' already exists in the table", new_item_href)

            if new_item_name in self.items_by_name:
                raise PyloEx(
                    "A VirtualService with name '%s' already exists in the table. This UID:%s vs other UID:%s" % (
                        new_item_name, new_item_href, self.items_by_name[new_item_name].href)
                )

            self.items_by_href[new_item_href] = new_item
            self.items_by_name[new_item_name] = new_item

            log.debug("Found VirtualService '%s' with href '%s'", new_item_name, new_item_href)

    def find_by_href_or_create_tmp(self, href: str, tmp_name: str) -> VirtualService:
        find_object = self.items_by_href.get(href)
        if find_object is not None:
            return find_object

        new_tmp_item = VirtualService(tmp_name, href, self)
        new_tmp_item.deleted = True
        new_tmp_item.temporary = True

        self.items_by_href[href] = new_tmp_item
        self.items_by_name[tmp_name] = new_tmp_item

        return new_tmp_item
