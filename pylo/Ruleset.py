import re
from typing import List, Union, Dict, Set

from .APIConnector import APIConnector
from .Helpers import LabelType
from .Exception import PyloEx
from .Helpers import nice_json
from .IPList import IPList
from .IPListStore import IPListStore
from .policyobjects import Label, LabelGroup
from .Rule import Rule, DirectServiceInRule
from .SecurityPrincipalStore import SecurityPrincipalStore
from .Service import Service
from .ServiceStore import ServiceStore
from .stores import LabelStore
from .VirtualServiceStore import VirtualServiceStore
from .WorkloadStore import WorkloadStore

ruleset_id_extraction_regex = re.compile(r"^/orgs/([0-9]+)/sec_policy/([0-9]+)?(draft)?/rule_sets/(?P<id>[0-9]+)$")


class RulesetScope:

    def __init__(self):
        self.scope_entries: Set[RulesetScopeEntry] = set()

    def load_from_json(self, data, label_store: LabelStore):
        for scope_json in data:
            scope_entry = RulesetScopeEntry()
            scope_entry.load_from_json(scope_json, label_store)
            self.scope_entries.add(scope_entry)

    def get_all_scopes_str(self, label_separator='|', scope_separator="\n", use_href: bool = False):
        return scope_separator.join([scope.to_string(label_separator, use_href=use_href) for scope in self.scope_entries])


class RulesetScopeEntry:

    def __init__(self):
        self.labels: Dict[LabelType, Label] = {
            LabelType.APP: None,
            LabelType.ENV: None,
            LabelType.LOC: None
        }

    def load_from_json(self, data, label_store: LabelStore):
        self.loc_label = None
        for label_json in data:
            label_entry = label_json.get('label')
            if label_entry is None:
                label_entry = label_json.get('label_group')
                if label_entry is None:
                    raise PyloEx("Cannot find 'label' or 'label_group' entry in scope: {}".format(nice_json(label_json)))
            href_entry = label_entry.get('href')
            if href_entry is None:
                raise PyloEx("Cannot find 'href' entry in scope: {}".format(nice_json(data)))

            label = label_store.find_by_href_or_die(href_entry)
            self.labels[label.label_type] = label

    def to_string(self, label_separator = '|', use_href=False):
        return label_separator.join(['All' if not label else label.href if use_href else label.name for label in self.labels])

    def is_all_all_all(self):
        return self.labels[LabelType.APP] is None and self.labels[LabelType.ENV] is None and self.labels[LabelType.LOC] is None


class Ruleset:

    def __init__(self):
        self.href = ''
        self.name = ''
        self.description = ''
        self.scopes = RulesetScope()
        self.rules_by_href: Dict[str, Rule] = {}

    def load_from_json(self, data: dict, service_store: ServiceStore, workload_store: WorkloadStore, label_store: LabelStore,
                    virtual_service_store: VirtualServiceStore, iplist_store: IPListStore, security_principal_store: SecurityPrincipalStore):
        if 'name' not in data:
            raise PyloEx("Cannot find Ruleset name in JSON data: \n" + nice_json(data))
        self.name = data['name']

        if 'href' not in data:
            raise PyloEx("Cannot find Ruleset href in JSON data: \n" + nice_json(data))
        self.href = data['href']

        if 'scopes' not in data:
            raise PyloEx("Cannot find Ruleset scope in JSON data: \n" + nice_json(data))

        self.description = data.get('description', '')
        self.scopes.load_from_json(data['scopes'], label_store)

        if 'rules' in data:
            for rule_data in data['rules']:
                self.load_single_rule_from_json(rule_data, service_store, workload_store, label_store, virtual_service_store, iplist_store, security_principal_store)

    def load_single_rule_from_json(self, rule_data, service_store: ServiceStore, workload_store: WorkloadStore, label_store: LabelStore,
                    virtual_service_store: VirtualServiceStore, iplist_store: IPListStore, security_principal_store: SecurityPrincipalStore) -> Rule:
        new_rule = Rule()
        new_rule.load_from_json(rule_data, service_store, workload_store, label_store, virtual_service_store, iplist_store, security_principal_store)
        self.rules_by_href[new_rule.href] = new_rule
        return new_rule

    def api_delete_rule(self, rule: Union[str, Rule], connector: APIConnector):
        """

        :param rule: should be href string or a Rule object
        """
        href = rule
        if isinstance(rule, Rule):
            href = rule.href

        find_object = self.rules_by_href.get(href)
        if find_object is None:
            raise PyloEx("Cannot delete a Rule with href={} which is not part of ruleset {}/{}".format(href, self.name, self.href))

        connector.objects_rule_delete(href)
        del self.rules_by_href[href]

    def api_create_rule(self, intra_scope: bool,
                        consumers: List[Union[IPList, Label, LabelGroup, Dict]],
                        providers: List[Union[IPList, Label, LabelGroup, Dict]],
                        services: List[Union[Service, DirectServiceInRule, Dict]],
                        connector: APIConnector,
                        description='', machine_auth=False, secure_connect=False, enabled=True,
                        stateless=False, consuming_security_principals=[],
                        resolve_consumers_as_virtual_services=True, resolve_consumers_as_workloads=True,
                        resolve_providers_as_virtual_services=True, resolve_providers_as_workloads=True) -> Rule:
        new_rule_json = connector.objects_rule_create(
            intra_scope=intra_scope, ruleset_href=self.href,
            consumers=consumers, providers=providers, services=services,
            description=description, machine_auth=machine_auth, secure_connect=secure_connect, enabled=enabled,
            stateless=stateless, consuming_security_principals=consuming_security_principals,
            resolve_consumers_as_virtual_services=resolve_consumers_as_virtual_services,
            resolve_consumers_as_workloads=resolve_consumers_as_workloads,
            resolve_providers_as_virtual_services=resolve_providers_as_virtual_services,
            resolve_providers_as_workloads=resolve_providers_as_workloads
        )
        return self.load_single_rule_from_json(new_rule_json)

    def count_rules(self):
        return len(self.rules_by_href)

    def extract_id_from_href(self):
        match = ruleset_id_extraction_regex.match(self.href)
        if match is None:
            raise PyloEx("Cannot extract ruleset_id from href '{}'".format(self.href))

        return match.group("id")

    def get_ruleset_url(self, connector: APIConnector, pce_hostname: str = None, pce_port: int = None):
        if pce_hostname is None:
            pce_hostname = connector.hostname
        if pce_port is None:
            pce_port = connector.port

        return 'https://{}:{}/#/rulesets/{}/draft/rules/'.format(pce_hostname, pce_port, self.extract_id_from_href())

    def api_set_name(self, new_name: str, connector: APIConnector):
        connector.objects_ruleset_update(self.href, update_data={'name': new_name})
        self.name = new_name

    def api_set_description(self, new_description: str, connector: APIConnector):
        connector.objects_ruleset_update(self.href, update_data={'description': new_description})
        self.description = new_description
