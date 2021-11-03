from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict

from pylo.Exception import PyloEx
from pylo.policyobjects import PolicyObject


@dataclass
class Store(ABC):
    items_by_href: Dict[str, PolicyObject] = field(default_factory=dict)
    items_by_name: Dict[str, PolicyObject] = field(default_factory=dict)

    @abstractmethod
    def load_from_json(self, json: str) -> None:
        pass

    def find_by_href_or_die(self, href: str) -> PolicyObject:
        if href not in self.items_by_href:
            raise PyloEx('HREF "{}" not found in {}'.format(href, self.__class__.__name__))
        return self.items_by_href[href]

    def find_by_name(self, name: str) -> PolicyObject:
        if name not in self.items_by_href:
            raise PyloEx('Name "{}" not found in {}'.format(name, self.__class__.__name__))
        return self.items_by_name[name]
