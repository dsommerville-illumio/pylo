from abc import ABC, abstractmethod
from dataclasses import dataclass

from .Helpers import LabelType
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
