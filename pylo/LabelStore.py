import random
from hashlib import md5
from typing import Optional, Union, Dict

import pylo


class LabelStore:

    def __init__(self, owner: 'pylo.Organization'):
        self.owner: "pylo.Organization" = owner
        self.itemsByHRef: Dict[str, Union[pylo.Label, pylo.LabelGroup]] = {}
        self.locationLabels: Dict[str, Union[pylo.Label, pylo.LabelGroup]] = {}
        self.environmentLabels: Dict[str, Union[pylo.Label, pylo.LabelGroup]] = {}
        self.roleLabels: Dict[str, Union[pylo.Label, pylo.LabelGroup]] = {}
        self.applicationLabels: Dict[str, Union[pylo.Label, pylo.LabelGroup]] = {}

        self.label_resolution_cache: Optional[Dict[str, Union[pylo.Label, pylo.LabelGroup]]] = None

    @staticmethod
    def label_type_str_to_int(label_type: str):
        if label_type == 'role':
            return pylo.ROLE_LABEL_TYPE
        if label_type == 'app':
            return pylo.APP_LABEL_TYPE
        if label_type == 'env':
            return pylo.ENV_LABEL_TYPE
        if label_type == 'loc':
            return pylo.LOC_LABEL_TYPE

        raise pylo.PyloEx("Unsupported Label/LabelGroup type '{}'".format(label_type))

    def loadLabelsFromJson(self, json_list):
        for json_label in json_list:
            if 'value' not in json_label or 'href' not in json_label or 'key' not in json_label:
                raise Exception("Cannot find 'value'/name or href for Label in JSON:\n" + pylo.nice_json(json_label))
            new_label_name = json_label['value']
            new_label_href = json_label['href']
            new_label_type = json_label['key']

            new_label = pylo.Label(new_label_name, new_label_href, new_label_type, self)

            if new_label_href in self.itemsByHRef:
                raise Exception("A Label with href '%s' already exists in the table", new_label_href)

            self.itemsByHRef[new_label_href] = new_label

            if new_label.type_is_location():
                self.locationLabels[new_label_name] = new_label
            elif new_label.type_is_environment():
                self.environmentLabels[new_label_name] = new_label
            elif new_label.type_is_application():
                self.applicationLabels[new_label_name] = new_label
            elif new_label.type_is_role():
                self.roleLabels[new_label_name] = new_label

            pylo.log.debug("Found Label '%s' with href '%s' and type '%s'", new_label_name, new_label_href, new_label_type)

    def loadLabelGroupsFromJson(self, json_list):

        created_groups = []

        for json_label in json_list:
            if 'name' not in json_label or 'href' not in json_label or 'key' not in json_label:
                raise Exception("Cannot find 'value'/name or href for Label in JSON:\n" + pylo.nice_json(json_label))
            new_label_name = json_label['name']
            newLabelHref = json_label['href']
            newLabelType_str = json_label['key']
            newLabelType = pylo.LabelStore.label_type_str_to_int(newLabelType_str)

            new_label = pylo.LabelGroup(new_label_name, newLabelHref, newLabelType, self)
            created_groups.append(new_label)

            if newLabelHref in self.itemsByHRef:
                raise Exception("A Label with href '%s' already exists in the table", newLabelHref)

            self.itemsByHRef[newLabelHref] = new_label

            if newLabelType == pylo.LOC_LABEL_TYPE:
                self.locationLabels[new_label_name] = new_label
            elif newLabelType == pylo.ENV_LABEL_TYPE:
                self.environmentLabels[new_label_name] = new_label
            elif newLabelType == pylo.APP_LABEL_TYPE:
                self.applicationLabels[new_label_name] = new_label
            elif newLabelType == pylo.ROLE_LABEL_TYPE:
                self.roleLabels[new_label_name] = new_label
            else:
                raise pylo.PyloEx("Unsupported LabelGroup type '{}' from json data".format(newLabelType), json_label)

            new_label.raw_json = json_label

            pylo.log.info("Found LabelGroup '%s' with href '%s' and type '%s'", new_label_name, newLabelHref, newLabelType)

        for group in created_groups:
            group.load_from_json()

    def count_labels(self):
        return len(self.itemsByHRef)

    def count_location_labels(self):
        return len(self.locationLabels)

    def count_environment_labels(self):
        return len(self.environmentLabels)

    def count_application_labels(self):
        return len(self.applicationLabels)

    def count_role_labels(self):
        return len(self.roleLabels)

    def get_location_labels_as_list(self):
        return self.locationLabels.values()

    def get_labels_no_groups(self) -> Dict[str, 'pylo.Label']:
        data = {}
        for label in self.itemsByHRef.values():
            if label.is_label():
                data[label.href] = label
        return data

    def get_label_groups(self) -> Dict[str, 'pylo.LabelGroup']:
        data = {}

        for label in self.itemsByHRef.values():
            if label.is_group():
                data[label.href] = label
        return data

    def find_label_by_name_whatever_type(self, name: str) -> Optional[Union['pylo.Label', 'pylo.LabelGroup']]:

        find = self.locationLabels.get(name)
        if find is not None:
            return find

        find = self.environmentLabels.get(name)
        if find is not None:
            return find

        find = self.applicationLabels.get(name)
        if find is not None:
            return find

        find = self.roleLabels.get(name)
        if find is not None:
            return find

        return None

    def find_label_by_name_and_type(self, name: str, type: int):
        if type == pylo.LOC_LABEL_TYPE:
            return self.locationLabels.get(name)
        if type == pylo.ENV_LABEL_TYPE:
            return self.environmentLabels.get(name)
        if type == pylo.APP_LABEL_TYPE:
            return self.applicationLabels.get(name)
        if type == pylo.ROLE_LABEL_TYPE:
            return self.roleLabels.get(name)
        raise Exception("Unsupported")

    cache_label_all_string = '-All-'
    cache_label_all_separator = '|'

    def generate_label_resolution_cache(self):
        self.label_resolution_cache = {}

        roles = list(self.roleLabels.keys())
        roles.append(self.cache_label_all_string)
        for role in roles:
            apps = list(self.applicationLabels.keys())
            apps.append(self.cache_label_all_string)
            for app in apps:
                envs = list(self.environmentLabels.keys())
                envs.append(self.cache_label_all_string)
                for env in envs:
                    locs = list(self.locationLabels.keys())
                    locs.append(self.cache_label_all_string)
                    for loc in locs:
                        group_name = role + LabelStore.cache_label_all_separator + app + LabelStore.cache_label_all_separator + env + LabelStore.cache_label_all_separator + loc
                        self.label_resolution_cache[group_name] = []

        all_string_and_sep = LabelStore.cache_label_all_string + LabelStore.cache_label_all_separator

        masks = [[False, False, False, False],
                 [True, False, False, False],
                 [False, True, False, False],
                 [True, True, False, False],
                 [False, False, True, False],
                 [True, False, True, False],
                 [True, True, True, False],
                 [False, False, False, True],
                 [True, False, False, True],
                 [False, True, False, True],
                 [True, True, False, True],
                 [False, False, True, True],
                 [True, False, True, True],
                 [True, True, True, True]]

        """masks = [
                 [True, True, True, True]]"""

        for workload in self.owner.WorkloadStore.itemsByHRef.values():
            if workload.deleted:
                continue

            already_processed = {}

            for mask in masks:
                if workload.role_label is not None and mask[0]:
                    group_name = workload.role_label.name + LabelStore.cache_label_all_separator
                else:
                    group_name = all_string_and_sep
                if workload.app_label is not None and mask[1]:
                    group_name += workload.app_label.name + LabelStore.cache_label_all_separator
                else:
                    group_name += all_string_and_sep
                if workload.env_label is not None and mask[2]:
                    group_name += workload.env_label.name + LabelStore.cache_label_all_separator
                else:
                    group_name += all_string_and_sep
                if workload.loc_label is not None and mask[3]:
                    group_name += workload.loc_label.name
                else:
                    group_name += LabelStore.cache_label_all_string

                if group_name not in already_processed:
                    self.label_resolution_cache[group_name].append(workload)
                already_processed[group_name] = True

    def get_workloads_by_label_scope(self, role: 'pylo.Label', app: 'pylo.Label', env: 'pylo.Label', loc: 'pylo.Label'):
        if self.label_resolution_cache is None:
            self.generate_label_resolution_cache()

        if role is None:
            role = LabelStore.cache_label_all_string
        else:
            role = role.name

        if app is None:
            app = LabelStore.cache_label_all_string
        else:
            app = app.name

        if env is None:
            env = LabelStore.cache_label_all_string
        else:
            env = env.name

        if loc is None:
            loc = LabelStore.cache_label_all_string
        else:
            loc = loc.name

        group_name = role + LabelStore.cache_label_all_separator + app + LabelStore.cache_label_all_separator + env + LabelStore.cache_label_all_separator + loc

        return self.label_resolution_cache[group_name]

    def create_label(self, name: str, label_type: str):

        new_label_name = name
        new_label_type = label_type
        new_label_href = '**fake-label-href**/{}'.format(md5(str(random.random()).encode('utf8')))

        new_label = pylo.Label(new_label_name, new_label_href, new_label_type, self)

        if new_label_href in self.itemsByHRef:
            raise Exception("A Label with href '%s' already exists in the table", new_label_href)

        self.itemsByHRef[new_label_href] = new_label

        if new_label.type_is_location():
            self.locationLabels[new_label_name] = new_label
        elif new_label.type_is_environment():
            self.environmentLabels[new_label_name] = new_label
        elif new_label.type_is_application():
            self.applicationLabels[new_label_name] = new_label
        elif new_label.type_is_role():
            self.roleLabels[new_label_name] = new_label

        return new_label

    def api_create_label(self, name: str, type: str):

        connector = pylo.find_connector_or_die(self.owner)
        json_label = connector.objects_label_create(name, type)

        if 'value' not in json_label or 'href' not in json_label or 'key' not in json_label:
            raise pylo.PyloEx("Cannot find 'value'/name or href for Label in JSON:\n" + pylo.nice_json(json_label))
        new_label_name = json_label['value']
        new_label_href = json_label['href']
        new_label_type = json_label['key']

        new_label = pylo.Label(new_label_name, new_label_href, new_label_type, self)

        if new_label_href in self.itemsByHRef:
            raise Exception("A Label with href '%s' already exists in the table", new_label_href)

        self.itemsByHRef[new_label_href] = new_label

        if new_label.type_is_location():
            self.locationLabels[new_label_name] = new_label
        elif new_label.type_is_environment():
            self.environmentLabels[new_label_name] = new_label
        elif new_label.type_is_application():
            self.applicationLabels[new_label_name] = new_label
        elif new_label.type_is_role():
            self.roleLabels[new_label_name] = new_label

        return new_label



    def find_label_by_name_lowercase_and_type(self, name: str, type: int):
        """

        :rtype: None|pylo.LabelCommon
        """
        ref = None
        name = name.lower()

        if type == pylo.LOC_LABEL_TYPE:
            ref = self.locationLabels
        elif type == pylo.ENV_LABEL_TYPE:
            ref = self.environmentLabels
        elif type == pylo.APP_LABEL_TYPE:
            ref = self.applicationLabels
        elif type == pylo.ROLE_LABEL_TYPE:
            ref = self.roleLabels
        else:
            raise pylo.PyloEx("Unsupported type '{}'".format(type))

        for labelName in ref.keys():
            if name == labelName.lower():
                return ref[labelName]

        return None

    def find_label_multi_by_name_lowercase_and_type(self, name: str, type: int):
        """

        :rtype: list[pylo.LabelCommon]
        """
        ref = None
        name = name.lower()
        result = []

        if type == pylo.LOC_LABEL_TYPE:
            ref = self.locationLabels
        elif type == pylo.ENV_LABEL_TYPE:
            ref = self.environmentLabels
        elif type == pylo.APP_LABEL_TYPE:
            ref = self.applicationLabels
        elif type == pylo.ROLE_LABEL_TYPE:
            ref = self.roleLabels

        for labelName in ref.keys():
            if name == labelName.lower():
                result.append(ref[labelName])

        return result

    def find_by_href_or_die(self, href: str):

        obj = self.itemsByHRef.get(href)

        if obj is None:
            raise Exception("Workload with HREF '%s' was not found" % href)

        return obj
