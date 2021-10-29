from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union

from .Exception import PyloEx
from .Helpers import LOC_LABEL_TYPE, ENV_LABEL_TYPE, APP_LABEL_TYPE, ROLE_LABEL_TYPE, LabelType
from .ReferenceTracker import ReferenceTracker


@dataclass
class LabelCommon(ABC, ReferenceTracker):
    name: str
    href: str
    label_type: LabelType

    def __post_init__(self):
        ReferenceTracker.__init__(self)

    @abstractmethod
    def get_api_reference_json(self) -> dict:
        pass


class Label(LabelCommon):
    def get_api_reference_json(self):
        return {'label': {'href': self.href}}
