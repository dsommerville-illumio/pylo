from typing import Dict, Union

from .Exception import PyloEx
from .Label import Label
from .LabelCommon import LabelCommon
from .ReferenceTracker import ReferenceTracker


class LabelGroup(ReferenceTracker, LabelCommon):

    def __init__(self, name: str, href: str, ltype: int):
        ReferenceTracker.__init__(self)
        LabelCommon.__init__(self, name, href, ltype)
        self._members: Dict[str, Union[Label, LabelGroup]] = {}
        self.raw_json = None

    def load_from_json(self):
        if 'labels' in self.raw_json:
            for href_record in self.raw_json['labels']:
                if 'href' in href_record:
                    find_label = self.owner.find_by_href_or_die(href_record['href'])
                    find_label.add_reference(self)
                    self._members[find_label.name] = find_label
                else:
                    raise PyloEx('LabelGroup member has no HREF')

    def expand_nested_to_array(self):
        results = {}
        for label in self._members.values():
            if isinstance(label, Label):
                results[label] = label
            elif isinstance(label, LabelGroup):
                for nested_label in label.expand_nested_to_array():
                    results[nested_label] = nested_label
            else:
                raise PyloEx("Unsupported object type {}".format(type(label)))
        return list(results.values())

    def get_api_reference_json(self) -> Dict:
        return {'label_group': {'href': self.href}}

    def get_members(self) -> Dict[str, Label]:
        data = {}
        for label in self._members.values():
            data[label.href] = label
        return data

    def is_group(self) -> bool:
        return True

    def is_label(self) -> bool:
        return False
