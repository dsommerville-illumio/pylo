from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from .APIConnector import APIConnector
from .Exception import PyloEx
from .Helpers import LabelType, nice_json, string_list_to_text
from .IPMap import IP4Map
from .policyobjects import Label
from .ReferenceTracker import Referencer, ReferenceTracker
from .stores import LabelStore
from .VENAgent import VENAgent
from .VENAgentStore import VENAgentStore


class WorkloadInterface:
    def __init__(self, name: str, ip: str, network: str, gateway: str, ignored: bool):
        self.name: str = name
        self.ip: str = ip
        self.network: str = network
        self.gateway: str = gateway
        self.is_ignored: bool = ignored


class WorkloadApiUpdateStack:
    def __init__(self):
        self.json_payload = {}

    def add_payload(self, data: Dict[str, Any]):
        for prop_name, prop_value in data.items():
            self.json_payload[prop_name] = prop_value

    def get_payload_and_reset(self) -> Dict[str, Any]:
        data = self.json_payload
        self.json_payload = {}
        return data

    def count_payloads(self) -> int:
        return len(self.json_payload)


@dataclass
class Workload(ReferenceTracker, Referencer):
    name: str
    href: str
    forced_name: str = None
    hostname: str = None
    description: str = None
    interfaces: List[WorkloadInterface] = field(default_factory=list)
    online: bool = False
    os_id: str = None
    os_detail: str = None
    labels: Dict[LabelType, Label] = field(default_factory=dict)
    ven_agent: VENAgent = None
    unmanaged: bool = True
    temporary: bool = False
    deleted: bool = False
    raw_json: Dict[str, Any] = None
    _batch_update_stack: WorkloadApiUpdateStack = None

    def __post_init__(self):
        Referencer.__init__(self)
        ReferenceTracker.__init__(self)
        self.labels = OrderedDict({
            LabelType.ROLE: None,
            LabelType.APP: None,
            LabelType.ENV: None,
            LabelType.LOC: None
        })

    def load_from_json(self, data, label_store: LabelStore, ven_agent_store: VENAgentStore):
        """
        Parse and build workload properties from a PCE API JSON payload. Should be used internally by this library only.
        """
        self.raw_json = data
        self.forced_name = data['name']
        self.hostname = data['hostname']
        agent_json = data.get('agent')

        if agent_json is None:
            raise PyloEx("Workload named '{}' has no Agent record:\n{}".format(self.name, nice_json(data)))

        agent_href = agent_json.get('href')
        if agent_href is None:
            self.unmanaged = True
        else:
            self.unmanaged = False
            self.ven_agent = ven_agent_store.create_ven_agent_from_workload_record(agent_json)
            self.online = data['online']
            self.os_id = data.get('os_id')
            if self.os_id is None:
                raise PyloEx("Workload named '{}' has no os_id record:\n{}".format(self.name, data))
            self.os_detail = data.get('os_detail')
            if self.os_detail is None:
                raise PyloEx("Workload named '{}' has no os_detail record:\n{}".format(self.name, data))

        self.description = data.get('description')

        ignored_interfaces_index = {}
        ignored_interfaces_json = data.get('ignored_interface_names')

        if ignored_interfaces_json is not None:
            for interface_name in ignored_interfaces_json:
                ignored_interfaces_index[interface_name] = True

        interfaces_json = data.get('interfaces')
        if interfaces_json is not None:
            for interface_json in interfaces_json:
                if_object = WorkloadInterface(interface_json.get('name'), interface_json.get('address'),
                                              interface_json.get('cidr_block'), interface_json.get('default_gateway_address'),
                                              ignored=interface_json.get('name') in ignored_interfaces_index)
                self.interfaces.append(if_object)

        self.deleted = data['deleted']

        if 'labels' in data:
            labels = data['labels']
            for label in labels:
                if 'href' not in label:
                    raise PyloEx("Workload named '{}' has labels in JSON but without any HREF:\n{}".format(
                        self.get_name(), nice_json(labels)
                    ))
                href = label['href']
                label_object = label_store.find_by_href_or_die(href)
                if self.labels[label_object.label_type]:
                    raise PyloEx("Workload '{}' found 2 labels of the same type while parsing JSON, labels are '{}' and '{}':\n".format(
                        self.get_name(), self.labels[label_object.label_type].name, label_object.name
                    ))
                self.labels[label_object.label_type] = label_object
                label_object.add_reference(self)

    def interfaces_to_string(self, separator: str = ',', show_ignored: bool = True) -> str:
        """
        Conveniently outputs all interface of this Workload to a string.

        :param separator: string used to separate each interface in the string
        :param show_ignored: whether or not ignored interfaces should be showing
        :return: string with interfaces split by specified separator
        """
        tmp = []

        for interface in self.interfaces:
            if not show_ignored and interface.is_ignored:
                continue
            tmp.append('{}:{}'.format(interface.name, interface.ip))

        return string_list_to_text(tmp, separator)

    def get_ip4map_from_interfaces(self) -> IP4Map:
        """
        Calculate and return a map of all IP4 covered by the Workload interfaces
        """
        result = IP4Map()

        for interface in self.interfaces:
            result.add_from_text(interface.ip)

        return result

    def is_using_label(self, label: Label) -> bool:
        """
        Check if a label is used by this Workload
        :param label: label to check for usage
        :return: true if label is used by this workload
        """
        return self.labels[label.label_type] == label

    def api_update_description(self, new_description: str, connector: APIConnector):
        data = {'description': new_description}
        if self._batch_update_stack is None:
            connector.objects_workload_update(self.href, data=data)
        else:
            self._batch_update_stack.add_payload(data)
        self.description = new_description

    def api_update_hostname(self, new_hostname: str, connector: APIConnector):
        data = {'hostname': new_hostname}
        if self._batch_update_stack is None:
            connector.objects_workload_update(self.href, data=data)
        else:
            self._batch_update_stack.add_payload(data)

        self.raw_json.update(data)
        self.hostname = new_hostname

    def api_update_forced_name(self, name: str, connector: APIConnector):

        data = {'name': name}
        if self._batch_update_stack is None:
            connector.objects_workload_update(self.href, data=data)
        else:
            self._batch_update_stack.add_payload(data)

        self.raw_json.update(data)
        self.forced_name = name

    def api_update_labels(self, connector: APIConnector, list_of_labels: Optional[List[Label]] = None, missing_label_type_means_no_change=False):
        """
        Push Workload's assigned Labels to the PCE.

        :param list_of_labels: labels to replace currently assigned ones. If not specified it will push current labels instead.
        :param missing_label_type_means_no_change: if a label type is missing and this is False then existing label of type in the Workload will be removed
        :return:
        """

        if list_of_labels is not None:
            # a list of labels were specified so are first going to change
            if not self.update_labels(list_of_labels, missing_label_type_means_no_change):
                return

        data = {'labels': [{'href': label.href for label in self.labels.values()}]}

        if self._batch_update_stack is None:
            connector.objects_workload_update(self.href, data)
        else:
            self._batch_update_stack.add_payload(data)

        self.raw_json.update(data)

    def api_stacked_updates_start(self):
        """
        Turns on 'updates stacking' mode for this Worklaod which will not push changes to API as you make them but only
        when you trigger 'api_push_stacked_updates()' function
        """
        self._batch_update_stack = WorkloadApiUpdateStack()

    def api_stacked_updates_push(self, connector: APIConnector):
        """
        Push all stacked changed to API and turns off 'updates stacking' mode
        """
        if self._batch_update_stack is None:
            raise PyloEx("Workload was not in 'update stacking' mode")

        connector.objects_workload_update(self.href, self._batch_update_stack.get_payload_and_reset())
        self._batch_update_stack = None

    def api_stacked_updates_count(self) -> int:
        """
        Counts the number of stacked changed for this Workload
        :return:
        """
        if self._batch_update_stack is None:
            raise PyloEx("Workload was not in 'update stacking' mode")
        return self._batch_update_stack.count_payloads()

    def get_labels_str(self, separator: str = '|') -> str:
        """
        Conveniently returns a string with all labels names in RAEL order
        :param separator: default separator is |
        :return: example: *None*|AppA|EnvC|LocZ
        """
        return separator.join([label.name if label else '*None*' for label in self.labels.values()])

    def get_label_str_by_type(self, label_type: LabelType, none_str='') -> str:
        return self.labels[label_type].name or none_str

    def get_label_href_by_type(self, label_type: LabelType, none_str='') -> str:
        return self.labels[label_type].href or none_str

    def get_appgroup_str(self, separator: str = '|') -> str:
        appgroup_labels = list(self.labels.values())[1:]  # app group excludes Role label
        return separator.join([label.name if label else '*None*' for label in appgroup_labels])

    def get_labels_str_list(self, missing_str: Optional[str] = '') -> List[str]:
        """
        Conveniently returns the list of Workload labels as a list of strings
        :param missing_str: if a label type is missing then missing_str will be used to represent it
        :return:
        """
        return [label.name if label else missing_str for label in self.labels.values()]

    def get_label_by_type(self, label_type: LabelType) -> Label:
        """
        Return the label of specified type assigned to this Workload
        :rtype: type of label (as a string: role, app, env or loc)
        """
        return self.labels[label_type]

    def get_name(self) -> str:
        """
        Return forced name if it exists, hostname otherwise

        :return:
        """
        if self.forced_name is not None:
            return self.forced_name
        if self.hostname is None:
            raise PyloEx("Cannot find workload name!")
        return self.hostname

    def get_name_stripped_fqdn(self):
        name_split = self.get_name().split('.')
        return name_split[0]

    @staticmethod
    def static_name_stripped_fqdn(name: str):
        name_split = name.split('.')
        return name_split[0]

    def get_status_string(self) -> str:
        if self.ven_agent is None:
            return 'not-applicable'
        return self.ven_agent.mode

    def update_labels(self, labels: List[Label]) -> None:
        """
        WARNING: this will not send updates to PCE API, use the 'api_' prefixed function for that

        :param list_of_labels: labels to replace currently assigned ones
        :return:
        """
        for label in self.labels.values():
            label.remove_reference(self)
            self.labels[label.label_type] = None

        for label in labels:
            existing_label = self.labels[label.label_type]
            if existing_label:
                raise PyloEx("{} label specified more than once ('{}' vs '{}')".format(
                    label.label_type.name, existing_label.name, label.name
                ))
            self.labels[label.label_type] = label
            label.add_reference(self)

    def __hash__(self):
        return hash(self.href)
