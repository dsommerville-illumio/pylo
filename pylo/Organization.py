import json
import os
import datetime
import getpass
from typing import Optional, List

from .Helpers import LABEL_SEPARATOR
from .policyobjects import Label
from .stores import LabelStore, SecurityPrincipalStore
from .IPListStore import IPListStore
from .WorkloadStore import WorkloadStore
from .VirtualServiceStore import VirtualServiceStore
from .VENAgentStore import VENAgentStore
from .ServiceStore import ServiceStore
from .RulesetStore import RulesetStore
from .SoftwareVersion import SoftwareVersion
from .Exception import PyloEx
from .APIConnector import APIConnector


class Organization:

    def __init__(self, org_id):
        self.id: int = org_id
        self.connector = None
        self.LabelStore = LabelStore()
        self.IPListStore = IPListStore()
        self.WorkloadStore = WorkloadStore()
        self.VirtualServiceStore = VirtualServiceStore()
        self.VENAgentStore = VENAgentStore()
        self.ServiceStore = ServiceStore()
        self.RulesetStore = RulesetStore()
        self.SecurityPrincipalStore = SecurityPrincipalStore()
        self.pce_version = None
        self.label_resolution_cache = {}

    def load_from_cached_file(self, hostname: str, no_exception_if_file_does_not_exist=False) -> bool:
        # filename should be like 'cache_xxx.yyy.zzz.json'
        filename = 'cache_' + hostname + '.json'

        if os.path.isfile(filename):
            # now we try to open that JSON file
            with open(filename) as json_file:
                data = json.load(json_file)
                if 'pce_version' not in data:
                    raise PyloEx("Cannot find PCE version in cache file")
                self.pce_version = SoftwareVersion(data['pce_version'])
                if 'data' not in data:
                    raise PyloEx("Cache file '%s' was found and successfully loaded but no 'data' object could be found" % filename)
                self.load_from_json(data['data'])
                return True

        if no_exception_if_file_does_not_exist:
            return False

        raise PyloEx("Cache file '%s' was not found!" % filename)

    def load_from_cache_or_saved_credentials(self, hostname: str, include_deleted_workloads=False, prompt_for_api_key_if_missing=True):
        # filename should be like 'cache_xxx.yyy.zzz.json'
        filename = 'cache_' + hostname + '.json'

        if os.path.isfile(filename):
            # now we try to open that JSON file
            with open(filename) as json_file:
                data = json.load(json_file)
                if 'pce_version' not in data:
                    raise PyloEx("Cannot find PCE version in cache file")
                self.pce_version = SoftwareVersion(data['pce_version'])
                if 'data' not in data:
                    raise PyloEx("Cache file '%s' was found and successfully loaded but no 'data' object could be found" % filename)
                self.load_from_json(data['data'])
            self.connector = APIConnector.create_from_credentials_in_file(hostname)
        else:
            self.load_from_saved_credentials(hostname, include_deleted_workloads=include_deleted_workloads, prompt_for_api_key=prompt_for_api_key_if_missing)

    def make_cache_file_from_api(self, con: APIConnector, include_deleted_workloads=False):
        # filename should be like 'cache_xxx.yyy.zzz.json'
        filename = 'cache_' + con.hostname + '.json'

        data = self.get_config_from_api(con, include_deleted_workloads=include_deleted_workloads)
        self.pce_version = con.version

        timestamp = datetime.datetime.now(datetime.timezone.utc)

        json_content = {'generation_date': timestamp.isoformat(),
                        'pce_version': self.pce_version.generate_str_from_numbers(),
                       'data': data
                        }

        with open(filename, 'w') as outfile:
            json.dump(json_content, outfile)

        size = os.path.getsize(filename)

        return filename, size

    def load_from_saved_credentials(self, hostname: str, include_deleted_workloads=False, prompt_for_api_key=False,
                                    list_of_objects_to_load: Optional[List[str]] = None):
        separator_pos = hostname.find(':')
        port = 8443

        if separator_pos > 0:
            port = hostname[separator_pos+1:]
            hostname = hostname[0:separator_pos]

        connector = APIConnector.create_from_credentials_in_file(hostname)
        if connector is None:
            if not prompt_for_api_key:
                raise PyloEx('Cannot find credentials for host {}'.format(hostname))
            print('Cannot find credentials for host "{}".\nPlease input an API user:'.format(hostname), end='')
            user = input()
            password = getpass.getpass()

            connector = APIConnector(hostname, port, user, password, skip_ssl_cert_check=True, orgID=self.id)

        self.load_from_api(connector, include_deleted_workloads=include_deleted_workloads, list_of_objects_to_load=list_of_objects_to_load)

    def load_from_json(self, data, list_of_objects_to_load: List[str] = None):
        if self.pce_version is None:
            raise PyloEx('Organization has no "version" specified')

        object_to_load = {}
        all_types = APIConnector.get_all_object_types()
        if list_of_objects_to_load is not None:
            for object_type in list_of_objects_to_load:
                if object_type not in all_types:
                    raise PyloEx("Unknown object type '{}'".format(object_type))
                object_to_load[object_type] = True
        else:
            object_to_load = all_types

        if 'labels' in object_to_load:
            if 'labels' not in data:
                raise Exception("'labels' was not found in json data")
            self.LabelStore.load_from_json(data['labels'])

        if 'labelgroups' in object_to_load:
            if 'labelgroups' not in data:
                raise Exception("'labelgroups' was not found in json data")
            self.LabelStore.load_from_json(data['labelgroups'])

        if 'iplists' in object_to_load:
            if 'iplists' not in data:
                raise Exception("'iplists' was not found in json data")
            self.IPListStore.load_iplists_from_json(data['iplists'])

        if 'services' in object_to_load:
            if 'services' not in data:
                raise Exception("'services' was not found in json data")
            self.ServiceStore.load_services_from_json(data['services'])

        if 'workloads' in object_to_load:
            if 'workloads' not in data:
                raise Exception("'workloads' was not found in json data")
            self.WorkloadStore.load_workloads_from_json(data['workloads'], self.LabelStore, self.VENAgentStore)

        if 'virtual_services' in object_to_load:
            if 'virtual_services' not in data:
                raise Exception("'virtual_services' was not found in json data")
            self.VirtualServiceStore.load_virtualservices_from_json(data['virtual_services'])

        if 'security_principals' in object_to_load:
            if 'security_principals' not in data:
                raise Exception("'security_principals' was not found in json data")
            self.SecurityPrincipalStore.load_from_json(data['security_principals'])

        if 'rulesets' in object_to_load:
            if 'rulesets' not in data:
                raise Exception("'rulesets' was not found in json data")
            self.RulesetStore.load_rulesets_from_json(data['rulesets'], self.ServiceStore, self.WorkloadStore,
                self.LabelStore, self.VirtualServiceStore, self.IPListStore, self.SecurityPrincipalStore)

    def load_from_api(self, con: APIConnector, include_deleted_workloads=False, list_of_objects_to_load: Optional[List[str]] = None):
        self.pce_version = con.getSoftwareVersion()
        return self.load_from_json(self.get_config_from_api(con, include_deleted_workloads=include_deleted_workloads,
                                                            list_of_objects_to_load=list_of_objects_to_load))

    @staticmethod
    def create_fake_empty_config():
        data = {}
        for object_type in APIConnector.get_all_object_types().values():
            data[object_type] = []
        return data

    def get_config_from_api(self, con: APIConnector, include_deleted_workloads=False, list_of_objects_to_load: Optional[List[str]] = None):
        self.connector = con

        return con.get_pce_objects(include_deleted_workloads=include_deleted_workloads, list_of_objects_to_load=list_of_objects_to_load)

    def stats_to_str(self, padding=''):
        stats = ""
        stats += "{}- Version {}\n".format(padding, self.pce_version.generate_str_from_numbers())
        stats += "{}- {} Labels in total. Loc: {} / Env: {} / App: {} / Role: {}".\
            format(padding,
                   self.LabelStore.count_labels(),
                   self.LabelStore.count_location_labels(),
                   self.LabelStore.count_environment_labels(),
                   self.LabelStore.count_application_labels(),
                   self.LabelStore.count_role_labels())

        stats += "\n{}- Workloads: Managed: {} / Unmanaged: {} / Deleted: {}". \
            format(padding,
                   self.WorkloadStore.count_managed_workloads(),
                   self.WorkloadStore.count_unmanaged_workloads(True),
                   self.WorkloadStore.count_deleted_workloads())

        stats += "\n{}- {} IPlists in total.". \
            format(padding,
                   self.IPListStore.count())

        stats += "\n{}- {} RuleSets and {} Rules.". \
            format(padding, self.RulesetStore.count_rulesets(), self.RulesetStore.count_rules())

        return stats

    def get_workloads_by_label_scope(self, role: Label, app: Label, env: Label, loc: Label):
        if self.label_resolution_cache is None:
            self._generate_label_resolution_cache()

        group_name = ''
        for label in [role, app, env, loc]:
            group_name += label.name if label else self.LabelStore.CACHE_LABEL_ALL_STRING
        return self.label_resolution_cache[group_name]

    def _generate_label_resolution_cache(self):
        from itertools import product
        self.label_resolution_cache = {}

        def label_cartesian_product():
            # generate the cartesian product of all label names for all types
            for item in product(*[list(label_map.keys()) for label_map in self.LabelStore.labels.values()]):
                yield LABEL_SEPARATOR.join(item)

        for group_name in label_cartesian_product():
            self.label_resolution_cache[group_name] = []

        masks = product([True, False], repeat=4)

        for workload in self.WorkloadStore.items_by_href.values():
            if workload.deleted:
                continue

            workload_labels = [workload.role_label, workload.app_label, workload.env_label, workload.loc_label]
            already_processed = {}

            for mask in masks:
                for i, label in enumerate(workload_labels):
                    group_name = ''
                    if label and mask[i]:
                        group_name += label.name + LABEL_SEPARATOR
                    else:
                        group_name += self.LabelStore.CACHE_LABEL_ALL_STRING + LABEL_SEPARATOR
                if group_name not in already_processed:
                    self.label_resolution_cache[group_name].append(workload)
                already_processed[group_name] = True
