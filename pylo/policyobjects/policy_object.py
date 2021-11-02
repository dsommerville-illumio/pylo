from abc import ABC, abstractmethod
from dataclasses import dataclass

from pylo.ReferenceTracker import ReferenceTracker


@dataclass
class PolicyObject(ABC, ReferenceTracker):
    href: str
    name: str

    def __post_init__(self):
        ReferenceTracker.__init__(self)

    @abstractmethod
    def get_api_reference_json(self) -> dict:
        pass

    def __hash__(self):
        return hash(self.href)
