from typing import Optional, List, Dict

from .stores import LabelStore
from .VENAgentStore import VENAgentStore

from .Exception import PyloEx
from .Helpers import nice_json
from .policyobjects import Label
from .tmp import log
from .Workload import Workload


class WorkloadStore:

    def __init__(self):
        self.items_by_href: Dict[str, Workload] = {}

    def load_workloads_from_json(self, json_list, label_store: LabelStore, ven_agent_store: VENAgentStore):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise PyloEx("Cannot find 'value'/name or href for Workload in JSON:\n" + nice_json(json_item))

            new_item_name = json_item['name']
            new_item_href = json_item['href']

            # Workload's name is None when it's provided by VEN through its hostname until it's manually overwritten
            # (eventually) by someone. In such a case, you need to use hostname instead
            if new_item_name is None:
                if 'hostname' not in json_item:
                    raise PyloEx("Cannot find 'value'/hostname in JSON:\n" + nice_json(json_item))
                new_item_name = json_item['hostname']

            new_item = Workload(new_item_name, new_item_href)
            new_item.load_from_json(json_item, label_store, ven_agent_store)

            if new_item_href in self.items_by_href:
                raise PyloEx("A Workload with href '%s' already exists in the table", new_item_href)

            self.items_by_href[new_item_href] = new_item

            log.debug("Found Workload '%s' with href '%s'", new_item_name, new_item_href)

    def find_by_href_or_die(self, href: str) -> Workload:
        """
        Find a Workload from its HREF, throw an Exception if not found

        :param href: the HREF you are looking for
        :return:
        :raises:
            PyloEx: if no Workload matching provided HREF
        """
        find_object = self.items_by_href.get(href)
        if find_object is None:
            raise PyloEx("Workload with HREF '%s' was not found" % href)

        return find_object

    def find_by_href_or_create_tmp(self, href: str, tmp_wkl_name: str) -> Workload:
        """
        Find a Workload from its HREF, creates a fake temporary one if not found. *Reserved for developers*

        :param href: the HREF you are looking for
        :return:
        """
        find_object = self.items_by_href.get(href)
        if find_object is not None:
            return find_object

        new_tmp_item = Workload(tmp_wkl_name, href)
        new_tmp_item.deleted = True
        new_tmp_item.temporary = True

        self.items_by_href[href] = new_tmp_item

        return new_tmp_item

    def find_workloads_matching_label(self, label: Label) -> Dict[str, Workload]:
        """
        Find all Workloads which are using a specific Label.

        :param label: Label you want to match on
        :return: a dictionary of all matching Workloads using their HREF as key
        """
        result = {}

        for href, workload in self.items_by_href.items():
            if workload.is_using_label(label):
                result[href] = workload

        return result

    def find_workloads_matching_all_labels(self, labels: List[Label]) -> Dict[str, Workload]:
        """
        Find all Workloads which are using all the Labels from a specified list.

        :param labels: list of Labels you want to match on
        :return: a dictionary of all matching Workloads using their HREF as key
        """
        result = {}

        for href, workload in self.items_by_href.items():
            matched = True
            for label in labels:
                if label is None:
                    continue
                if not workload.is_using_label(label):
                    matched = False
                    break
            if matched:
                result[href] = workload

        return result

    def find_workload_matching_forced_name(self, name: str, case_sensitive: bool = True, strip_fqdn: bool = False) -> Optional[Workload]:
        """
        Find a Workload based on its name (case sensitive). Beware that if several are matching, only the first one will be returned

        :param name: the name string you are looking for
        :param case_sensitive: make it a case sensitive search or not
        :param strip_fqdn: remove the fqdn part of the hostname
        :return: the Workload it found, None otherwise
        """
        if case_sensitive:
            name = name.lower()

        for workload in self.items_by_href.values():
            wkl_name = workload.forced_name
            if strip_fqdn:
                wkl_name = Workload.static_name_stripped_fqdn(wkl_name)
            if case_sensitive:
                if wkl_name == name:
                    return workload
            else:
                if wkl_name.lower() == name:
                    return workload

        return None

    def find_workload_matching_hostname(self, name: str, case_sensitive: bool = True, strip_fqdn: bool = False) -> Optional[Workload]:
        """
        Find a workload based on its hostname.Beware that if several are matching, only the first one will be returned

        :param name: the name string you are looking for
        :param case_sensitive: make it a case sensitive search or not
        :param strip_fqdn: remove the fqdn part of the hostname
        :return: the Workload it found, None otherwise
        """
        if case_sensitive:
            name = name.lower()

        for workload in self.items_by_href.values():
            wkl_name = workload.hostname
            if strip_fqdn:
                wkl_name = Workload.static_name_stripped_fqdn(wkl_name)
            if case_sensitive:
                if wkl_name == name:
                    return workload
            else:
                if wkl_name.lower() == name:
                    return workload

        return None

    def find_all_workloads_matching_hostname(self, name: str, case_sensitive: bool = True, strip_fqdn: bool = False) -> List[Workload]:
        """
        Find all workloads based on their hostnames.
        :param name: the name string you are looking for
        :param case_sensitive: make it a case sensitive search or not
        :param strip_fqdn: remove the fqdn part of the hostname
        :return: list of matching Workloads
        """
        result = []

        if case_sensitive:
            name = name.lower()

        for workload in self.items_by_href.values():
            wkl_name = workload.hostname
            if strip_fqdn:
                wkl_name = Workload.static_name_stripped_fqdn(wkl_name)
            if case_sensitive:
                if wkl_name == name:
                    result.append(workload)
            else:
                if wkl_name.lower() == name:
                    result.append(workload)

        return result

    def count_workloads(self) -> int:
        return len(self.items_by_href)

    def count_managed_workloads(self) -> int:
        count = 0

        for item in self.items_by_href.values():
            if not item.unmanaged and not item.deleted:
                count += 1

        return count

    def get_managed_workloads_list(self) -> List[Workload]:
        """
        Get a list of all managed workloads
        :return:
        """
        results = []
        for item in self.items_by_href.values():
            if not item.unmanaged:
                results.append(item)

        return results

    def get_managed_workloads_dict_href(self) -> Dict[str, Workload]:
        """
        Get a dictionary of all managed workloads using their HREF as key
        :return:
        """
        results = {}
        for item in self.items_by_href.values():
            if not item.unmanaged:
                results[item.href] = item

        return results

    def count_deleted_workloads(self) -> int:
        count = 0
        for item in self.items_by_href.values():
            if item.deleted:
                count += 1

        return count

    def count_unmanaged_workloads(self, if_not_deleted=False) -> int:
        count = 0

        for item in self.items_by_href.values():
            if item.unmanaged and (not if_not_deleted or (if_not_deleted and not item.deleted)):
                count += 1

        return count
