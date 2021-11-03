from dataclasses import dataclass

from pylo.Helpers import LabelType
from .policyobject import PolicyObject


@dataclass
class Label(PolicyObject):
    label_type: LabelType

    def get_api_reference_json(self):
        return {'label': {'href': self.href}}

    __hash__ = PolicyObject.__hash__
