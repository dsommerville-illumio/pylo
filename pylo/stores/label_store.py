import random
from dataclasses import dataclass
from hashlib import md5
from typing import Dict, List

from pylo.APIConnector import APIConnector
from pylo.Exception import PyloEx
from pylo.Helpers import LabelType, nice_json
from pylo.policyobjects import Label, LabelGroup
from pylo.tmp import log

from .store import Store


@dataclass
class LabelStore(Store):
    CACHE_LABEL_ALL_STRING = '-All-'
    labels: Dict[int, Dict[str, Label]] = None

    def __post_init__(self):
        self.labels = {
            LabelType.ROLE: {self.CACHE_LABEL_ALL_STRING: None},
            LabelType.APP: {self.CACHE_LABEL_ALL_STRING: None},
            LabelType.ENV: {self.CACHE_LABEL_ALL_STRING: None},
            LabelType.LOC: {self.CACHE_LABEL_ALL_STRING: None}
        }

    def load_from_json(self, json_list):
        for json_label in json_list:
            self._create_label_from_json(json_label)

    def _create_label_from_json(self, json_label: dict) -> Label:
        if (('value' not in json_label and 'name' not in json_label)
            or 'href' not in json_label or 'key' not in json_label):
            raise PyloEx("Incorrect formatting for Label JSON; must contain value/name, href, and key fields:\n" + nice_json(json_label))
        name = json_label.get('value', json_label.get('name'))
        href = json_label['href']
        label_type = json_label['key']
        label_class = LabelGroup if 'name' in json_label else Label
        new_label = self.create_label(name, label_type, href, label_class)
        if 'labels' in json_label:
            for href_record in json_label['labels']:
                if 'href' in href_record:
                    find_label = self.items_by_href[href_record['href']]
                    find_label.add_reference(new_label)
                    new_label.members[find_label.href] = find_label
                else:
                    raise PyloEx('LabelGroup member has no HREF')
        return new_label

    def create_label(self, name: str, label_type: str, href='', label_class=Label) -> Label:
        href = href or '**fake-label-href**/{}'.format(md5(str(random.random()).encode('utf8')))
        label_type = LabelType[label_type.upper()]

        if href in self.items_by_href:
            raise PyloEx("A Label with href '%s' already exists in the table", href)

        new_label = label_class(name=name, href=href, label_type=label_type)
        self.labels[label_type][name] = new_label
        self.items_by_href[href] = new_label

        log.debug("Found Label '%s' with href '%s' and type '%s'", name, href, label_type)
        return new_label

    def api_create_label(self, name: str, label_type: str, api_connector: APIConnector) -> Label:
        json_label = api_connector.objects_label_create(name, label_type)
        return self._create_label_from_json(json_label)

    def api_set_label_name(self, label: Label, name: str, api_connector: APIConnector) -> None:
        old_name = label.name
        if old_name == name:
            return
        if name in self.labels[label.label_type]:
            raise PyloEx("A Label/LabelGroup with name '{}' already exists".format(name))

        api_connector.objects_label_update(label.href, data={'name': name})
        label.name = name
        self.labels[label.label_type].pop(old_name)
        self.labels[label.label_type][name] = label

    def count_labels(self):
        return len(self.items_by_href)

    def count_location_labels(self):
        return len(self.labels[LabelType.LOC])

    def count_environment_labels(self):
        return len(self.labels[LabelType.ENV])

    def count_application_labels(self):
        return len(self.labels[LabelType.APP])

    def count_role_labels(self):
        return len(self.labels[LabelType.ROLE])

    def find_by_href_or_die(self, href: str) -> Label:
        return self.items_by_href[href]

    def find_by_name(self, name: str, label_type: LabelType = None) -> Label:
        label_maps = [self.labels[label_type]] if label_type else self.labels.values()
        for label_map in label_maps:
            if name in label_map:
                return label_map[name]

    def find_all_by_name(self, name: str, label_type: LabelType = None) -> Label:
        label_maps = [self.labels[label_type]] if label_type else self.labels.values()
        name = name.lower()
        labels = []
        for label_map in label_maps:
            for label_name in label_map.keys():
                if label_name.lower() == name:
                    labels.append(label_map[label_name])
        return labels

    def find_label_by_name_lowercase_and_type(self, name: str, label_type: LabelType):
        ref = self.labels[label_type]
        name = name.lower()

        for labelName in ref.keys():
            if name == labelName.lower():
                return ref[labelName]

    def find_label_multi_by_name_lowercase_and_type(self, name: str, label_type: LabelType):
        ref = self.labels[label_type]
        name = name.lower()
        result = []

        for labelName in ref.keys():
            if name == labelName.lower():
                result.append(ref[labelName])
        return result

    def find_label_by_name_whatever_type(self, name: str) -> Label:
        for labels in self.labels.values():
            if name in labels:
                return labels[name]

    def find_label_by_name_and_type(self, name: str, label_type: LabelType) -> Label:
        return self.labels[label_type][name]

    def get_location_labels_as_list(self) -> List[Label]:
        return list(self.labels[LabelType.LOC].values())

    def get_labels_no_groups(self) -> Dict[str, Label]:
        data = {}
        for label in self.items_by_href.values():
            if isinstance(label, Label):
                data[label.href] = label
        return data

    def get_label_groups(self) -> Dict[str, LabelGroup]:
        data = {}
        for label in self.items_by_href.values():
            if isinstance(label, LabelGroup):
                data[label.href] = label
        return data
