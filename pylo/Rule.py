from typing import Optional, List, Union, Dict, Any

from .APIConnector import APIConnector
from .Exception import PyloEx
from .Helpers import nice_json, string_list_to_text
from .IPList import IPList
from .IPListStore import IPListStore
from .policyobjects import Label, LabelGroup
from .stores import LabelStore
from .ReferenceTracker import Referencer
from .SecurityPrincipal import SecurityPrincipal
from .SecurityPrincipalStore import SecurityPrincipalStore
from .Service import Service
from .ServiceStore import ServiceStore
from .tmp import find_connector_or_die
from .Workload import Workload
from .WorkloadStore import WorkloadStore
from .VirtualService import VirtualService
from .VirtualServiceStore import VirtualServiceStore


class RuleApiUpdateStack:
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


class Rule:

    def __init__(self):
        self.description: Optional[str] = None
        self.services: RuleServiceContainer = RuleServiceContainer()
        self.providers: RuleHostContainer = RuleHostContainer('providers')
        self.consumers: RuleHostContainer = RuleHostContainer('consumers')
        self.consuming_principals: RuleSecurityPrincipalContainer = RuleSecurityPrincipalContainer()
        self.href: Optional[str] = None
        self.enabled: bool = True
        self.secure_connect: bool = False
        self.unscoped_consumers: bool = False
        self.stateless: bool = False
        self.machine_auth: bool = False

        self.raw_json: Optional[Dict[str, Any]] = None
        self.batch_update_stack: Optional[RuleApiUpdateStack] = None

    def load_from_json(self, data, service_store: ServiceStore, workload_store: WorkloadStore, label_store: LabelStore,
                    virtual_service_store: VirtualServiceStore, iplist_store: IPListStore, security_principal_store: SecurityPrincipalStore):
        self.raw_json = data

        self.href = data['href']

        self.description = data.get('description')

        services = data.get('ingress_services')
        if services is not None:
            self.services.load_from_json(services, service_store)

        enabled = data.get('enabled')
        if enabled is not None:
            self.enabled = enabled

        stateless = data.get('stateless')
        if stateless is not None:
            self.stateless = stateless

        machine_auth = data.get('machine_auth')
        if machine_auth is not None:
            self.machine_auth = machine_auth

        secure_connect = data.get('sec_connect')
        if secure_connect is not None:
            self.secure_connect = secure_connect

        unscoped_consumers = data.get('unscoped_consumers')
        if unscoped_consumers is not None:
            self.unscoped_consumers = unscoped_consumers

        self.providers.load_from_json(data['providers'], workload_store, label_store, virtual_service_store, iplist_store)
        self.consumers.load_from_json(data['consumers'], workload_store, label_store, virtual_service_store, iplist_store)
        self.consuming_principals.load_from_json(data['consuming_security_principals'], security_principal_store)

    def is_extra_scope(self):
        return self.unscoped_consumers

    def is_intra_scope(self):
        return not self.unscoped_consumers

    def api_set_description(self, new_description: str, connector: APIConnector):
        data = {'description': new_description}
        if self.batch_update_stack is None:
            connector.objects_rule_update(self.href, update_data=data)

        self.raw_json.update(data)
        self.description = new_description

    def api_stacked_updates_start(self):
        """
        Turns on 'updates stacking' mode for this Rule which will not push changes to API as you make them but only
        when you trigger 'api_push_stacked_updates()' function
        """
        self.batch_update_stack = RuleApiUpdateStack()

    def api_stacked_updates_push(self, connector: APIConnector):
        """
        Push all stacked changed to API and turns off 'updates stacking' mode
        """
        if self.batch_update_stack is None:
            raise PyloEx("Workload was not in 'update stacking' mode")

        connector.objects_rule_update(self.href, self.batch_update_stack.get_payload_and_reset())
        self.batch_update_stack = None

    def api_stacked_updates_count(self) -> int:
        """
        Counts the number of stacked changed for this Ruke
        :return:
        """
        if self.batch_update_stack is None:
            raise PyloEx("Workload was not in 'update stacking' mode")
        return self.batch_update_stack.count_payloads()


class RuleSecurityPrincipalContainer(Referencer):
    def __init__(self):
        super().__init__()
        self._items: Dict[SecurityPrincipal, SecurityPrincipal] = {}  # type:

    def load_from_json(self, data, security_principal_store: SecurityPrincipalStore):
        for item_data in data:
            wanted_href = item_data['href']
            found_object = security_principal_store.find_by_href_or_die(wanted_href)
            found_object.add_reference(self)
            self._items[found_object] = found_object


class DirectServiceInRule:
    def __init__(self, proto: int, port: int = None, toport: int = None):
        self.protocol = proto
        self.port = port
        self.to_port = toport

    def is_tcp(self):
        return self.protocol == 6

    def is_udp(self):
        return self.protocol == 17

    def to_string_standard(self, protocol_first=True):
        if self.protocol == 17:
            if self.to_port is None:
                if protocol_first:
                    return 'udp/' + str(self.port)

                return str(self.port) + '/udp'
            if protocol_first:
                return 'udp/' + str(self.port) + '-' + str(self.to_port)

            return str(self.port) + '-' + str(self.to_port) + '/udp'
        elif self.protocol == 6:
            if self.to_port is None:
                if protocol_first:
                    return 'tcp/' + str(self.port)
                return str(self.port) + '/tcp'

            if protocol_first:
                return 'tcp/' + str(self.port) + '-' + str(self.to_port)
            return str(self.port) + '-' + str(self.to_port) + '/tcp'

        if protocol_first:
            return 'proto/' + str(self.protocol)

        return str(self.protocol) + '/proto'

    def get_api_json(self) -> Dict:
        """
        Generates json payload to be included in a rule's service update or creation
        """
        if self.protocol != 17 and self.protocol != 6:
            return {'proto': self.protocol}

        if self.to_port is None:
            return {'proto': self.protocol, 'port': self.port}
        return {'proto': self.protocol, 'port': self.port, 'to_port': self.to_port}

    @staticmethod
    def create_from_text(txt: str, seperator='/', protocol_first=True) -> 'DirectServiceInRule':
        parts = txt.split(seperator)

        if len(parts) != 2:
            lower = txt.lower()
            if lower == 'icmp':
                return DirectServiceInRule(proto=1)
            raise PyloEx("Invalid service syntax '{}'".format(txt))

        if protocol_first:
            proto = parts[0]
            port_input = parts[1]
        else:
            proto = parts[1]
            port_input = parts[0]

        if not proto.isdigit():
            proto_lower = proto.lower()
            if proto_lower == 'tcp':
                protocol_int = 6
            elif proto_lower == 'udp':
                protocol_int = 17
            else:
                raise PyloEx("Invalid protocol provided: {}".format(proto))
        else:
            protocol_int = int(proto)

        port_parts = port_input.split('-')
        if len(port_parts) > 2:
            raise PyloEx("Invalid port provided: '{}' in string '{}'".format(port_input, txt))

        if len(port_parts) == 2:
            if protocol_int != 17 and protocol_int != 6:
                raise PyloEx("Only TCP and UDP support port ranges so this service in invalid: '{}'".format(txt))
            from_port_input = port_parts[0]
            to_port_input = port_parts[1]

            if not from_port_input.isdigit():
                raise PyloEx("Invalid port provided: '{}' in string '{}'".format(from_port_input, txt))
            if not to_port_input.isdigit():
                raise PyloEx("Invalid port provided: '{}' in string '{}'".format(to_port_input, txt))

            return DirectServiceInRule(protocol_int, port=int(from_port_input), toport=int(to_port_input))

        if not port_input.isdigit():
            raise PyloEx("Invalid port provided: '{}' in string '{}'".format(port_input, txt))

        return DirectServiceInRule(protocol_int, port=int(port_input))


class RuleServiceContainer(Referencer):
    def __init__(self):
        super().__init__()
        self._items: Dict[Service, Service] = {}
        self._direct_services: List[DirectServiceInRule] = []

    def load_from_json_legacy_single(self, data, service_store: ServiceStore):
        href = data.get('href')
        if href is None:
            raise Exception('Cannot find service HREF')

        find_service = service_store.items_by_href.get(href)
        if find_service is None:
            raise Exception('Cannot find Service with HREF %s in Rule'.format(href))

        self._items[find_service] = find_service
        find_service.add_reference(self)

    def load_from_json(self, data_list, service_store):
        for data in data_list:
            # print(data)
            href = data.get('href')
            if href is None:
                port = data.get('port')
                if port is None:
                    raise PyloEx("unsupported service type in rule: {}".format(nice_json(data)))
                protocol = data.get('proto')
                if protocol is None:
                    raise PyloEx("Protocol not found in direct service use: {}".format(nice_json(data)))

                to_port = data.get('to_port')
                direct_port = DirectServiceInRule(protocol, port, to_port)
                self._direct_services.append(direct_port)

                continue

            find_service = service_store.items_by_href.get(href)
            if find_service is None:
                raise Exception('Cannot find Service with HREF %s in Rule'.format(href))

            self._items[find_service] = find_service
            find_service.add_reference(self)

    def get_direct_services(self) -> List[DirectServiceInRule]:
        """
        Return a list of services directly included in the Rule
        """
        return self._direct_services.copy()

    def get_services(self) -> List[Service]:
        return list(self._items.values())

    def remove_direct_service(self, service: DirectServiceInRule) -> bool:
        for i in range(0, len(self._direct_services)):
            if self._direct_services[i] is service:
                del(self._direct_services[i])
                return True
        return False

    def add_direct_service(self, service: DirectServiceInRule) -> bool:
        for member in self._direct_services:
            if service is member:
                return False
        self._direct_services.append(service)
        return True

    def members_to_str(self, separator: str = ',') -> str:
        text: str = ''

        for service in self._items.values():
            if len(text) > 0:
                text += separator
            text += service.name + ': ' + string_list_to_text(service.get_entries_str_list())

        for direct in self._direct_services:
            if len(text) > 0:
                text += separator
            text += direct.to_string_standard()

        return text

    def get_api_json_payload(self) -> List[Dict[str, Any]]:
        """
        Generate JSON payload for API update call
        :return:
        """
        data = []
        for service in self._direct_services:
            data.append(service.get_api_json())

        for service in self._items.values():
            data.append({'href': service.href})

        return data

    def api_sync(self, rule: Rule, connector: APIConnector):
        """
        Synchronize a Rule's services after some changes were made
        """
        data = self.get_api_json_payload()
        data = {'ingress_services': data}

        if rule.batch_update_stack is None:
            connector.objects_rule_update(rule.href, update_data=data)
        else:
            rule.batch_update_stack.add_payload(data)

        rule.raw_json.update(data)


class RuleHostContainer(Referencer):
    def __init__(self, name: str):
        super().__init__()
        self._items: Dict[
            Union[Label, LabelGroup, Workload, VirtualService],
            Union[Label, LabelGroup, Workload, VirtualService]
        ] = {}
        self.name = name
        self._hasAllWorkloads = False

    def load_from_json(self, data, workload_store: WorkloadStore, label_store: LabelStore,
                    virtual_service_store: VirtualServiceStore, iplist_store: IPListStore):
        """
        Parse from a JSON payload.
        *For developers only*

        :param data: JSON payload to parse
        """
        for host_data in data:
            find_object = None
            if 'label' in host_data:
                href = host_data['label'].get('href')
                if href is None:
                    PyloEx('Cannot find object HREF ', host_data)
                find_object = label_store.items_by_href.get(href)
                if find_object is None:
                    raise Exception('Cannot find Label with HREF {} in Rule'.format(href))
            elif 'label_group' in host_data:
                href = host_data['label_group'].get('href')
                if href is None:
                    raise PyloEx('Cannot find object HREF ', host_data)
                find_object = label_store.items_by_href.get(href)
                if find_object is None:
                    raise Exception('Cannot find LabelGroup with HREF {} in Rule'.format(href))
            elif 'ip_list' in host_data:
                href = host_data['ip_list'].get('href')
                if href is None:
                    raise PyloEx('Cannot find object HREF ', host_data)
                find_object = iplist_store.items_by_href.get(href)
                if find_object is None:
                    raise Exception('Cannot find IPList with HREF {} in Rule'.format(href))
            elif 'workload' in host_data:
                href = host_data['workload'].get('href')
                if href is None:
                    raise PyloEx('Cannot find object HREF ', host_data)
                # @TODO : better handling of temporary objects
                find_object = workload_store.items_by_href.get(href)
                if find_object is None:
                    # raise Exception("Cannot find Workload with HREF {} in Rule {}. JSON:\n {}".format(href, self.owner.href, nice_json(host_data)))
                    find_object = workload_store.find_by_href_or_create_tmp(href, 'tmp-deleted-wkl-'+href)
            elif 'virtual_service' in host_data:
                href = host_data['virtual_service'].get('href')
                if href is None:
                    raise PyloEx('Cannot find object HREF ', host_data)
                # @TODO : better handling of temporary objects
                find_object = virtual_service_store.items_by_href.get(href)
                if find_object is None:
                    # raise Exception("Cannot find VirtualService with HREF {} in Rule {}. JSON:\n {}".format(href, self.owner.href, nice_json(host_data)))
                    find_object = virtual_service_store.find_by_href_or_create_tmp(href, 'tmp-deleted-wkl-'+href)
            elif 'actors' in host_data:
                actor_value = host_data['actors']
                if actor_value is not None and actor_value == 'ams':
                    self._hasAllWorkloads = True
                    continue
                # TODO implement actors
                raise PyloEx("An actor that is not 'ams' was detected but this library doesn't support it yet", host_data)
            else:
                raise PyloEx("Unsupported reference type", host_data)

            if find_object is not None:
                self._items[find_object] = find_object
                find_object.add_reference(self)

    def has_workloads(self) -> bool:
        """
        Check if this container references at least one Workload
        :return: True if contains at least one Workload
        """
        for item in self._items.values():
            if isinstance(item, Workload):
                return True
        return False

    def has_virtual_services(self) -> bool:
        """
        Check if this container references at least one Virtual Service
        :return: True if contains at least one Virtual Service
        """
        for item in self._items.values():
            if isinstance(item, VirtualService):
                return True
        return False

    def has_labels(self) -> bool:
        """
        Check if this container references at least one Label or LabelGroup
        :return: True if contains at least one Label or LabelGroup
        """
        for item in self._items.values():
            if isinstance(item, Label) or isinstance(item, LabelGroup):
                return True
        return False

    def get_labels(self) -> List[Union[Label, LabelGroup]]:
        """
        Get a list Labels and LabelGroups which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if isinstance(item, Label) or isinstance(item, LabelGroup):
                result.append(item)

        return result

    def get_role_labels(self) -> List[Union[Label, LabelGroup]]:
        """
        Get a list Role Labels and LabelGroups which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if (isinstance(item, Label) or isinstance(item, LabelGroup)) and item.type_is_role():
                result.append(item)

        return result

    def get_app_labels(self) -> List[Union[Label, LabelGroup]]:
        """
        Get a list App Labels and LabelGroups which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if (isinstance(item, Label) or isinstance(item, LabelGroup)) and item.type_is_application():
                result.append(item)

        return result

    def get_env_labels(self) -> List[Union[Label, LabelGroup]]:
        """
        Get a list Env Labels and LabelGroups which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if (isinstance(item, Label) or isinstance(item, LabelGroup)) and item.type_is_environment():
                result.append(item)

        return result

    def get_loc_labels(self) -> List[Union[Label, LabelGroup]]:
        """
        Get a list Loc Labels and LabelGroups which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if (isinstance(item, Label) or isinstance(item, LabelGroup)) and item.type_is_location():
                result.append(item)

        return result

    def members_to_str(self, separator=',') -> str:
        """
        Conveniently creates a string with all members of this container, ordered by Label, IList, Workload,
        and  Virtual Service

        :param separator: string use to separate each member in the lit
        :return:
        """
        text = ''

        if self._hasAllWorkloads:
            text += "All Workloads"

        for label in self.get_labels():
            if len(text) > 0:
                text += separator
            text += label.name

        for item in self.get_iplists():
            if len(text) > 0:
                text += separator
            text += item.name

        for item in self.get_workloads():
            if len(text) > 0:
                text += separator
            text += item.get_name()

        for item in self.get_virtual_services():
            if len(text) > 0:
                text += separator
            text += item.name

        return text

    def contains_iplists(self) -> bool:
        """
        Returns True if at least 1 iplist is part of this container
        """
        for item in self._items.values():
            if isinstance(item, IPList):
                return True
        return False

    def get_iplists(self) -> List[IPList]:
        """
        Get a list of IPLists which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if isinstance(item, IPList):
                result.append(item)

        return result

    def get_workloads(self) -> List[Workload]:
        """
        Get a list of Workloads which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if isinstance(item, Workload):
                result.append(item)

        return result

    def get_virtual_services(self) -> List[VirtualService]:
        """
        Get a list of VirtualServices which are part of this container
        :return:
        """
        result = []

        for item in self._items.values():
            if isinstance(item, VirtualService):
                result.append(item)

        return result

    def contains_all_workloads(self) -> bool:
        """

        :return: True if "All Workloads" is referenced by this container
        """
        return self._hasAllWorkloads
