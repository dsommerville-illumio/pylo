from dataclasses import dataclass, field
from typing import Dict

from .Exception import PyloEx
from .Label import Label, LabelCommon


@dataclass
class LabelGroup(LabelCommon):
    members: Dict[str, LabelCommon] = field(default_factory=dict)

    def expand_nested_to_array(self):
        results = {}
        for label in self.members.values():
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
