from pylo.policyobjects import SecurityPrincipal
from pylo.Exception import PyloEx
from pylo.Helpers import nice_json
from pylo.tmp import log

from .store import Store


class SecurityPrincipalStore(Store):

    def load_from_json(self, json_list):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise PyloEx("Cannot find 'value'/name or href for SecurityPrincipal in JSON:\n" + nice_json(json_item))

            name = json_item['name']
            href = json_item['href']
            sid = json_item['sid']
            deleted = json_item['deleted']

            # SecurityPrincipals's name is None when it's provided by VEN through its hostname until it's manually overwritten
            # (eventually) by someone. In such a case, you need to use hostname instead
            if name is None:
                if 'hostname' not in json_item:
                    raise PyloEx("Cannot find 'value'/hostname in JSON:\n" + nice_json(json_item))
                name = json_item['hostname']

            if href in self.items_by_href:
                raise PyloEx("A SecurityPrincipal with href '%s' already exists in the table", href)

            if name in self.items_by_name:
                raise PyloEx(
                    "A SecurityPrincipal with name '%s' already exists in the table. This UID:%s vs other UID:%s" % (
                        name, href, self.items_by_name[name].href))

            new_item = SecurityPrincipal(name=name, href=href, sid=sid, deleted=deleted)

            self.items_by_href[href] = new_item
            self.items_by_name[name] = new_item

            log.debug("Found SecurityPrincipal '%s' with href '%s'", name, href)
