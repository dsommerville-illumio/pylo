from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List

from ..policyobjects import PolicyObject


@dataclass
class Store(ABC):
    items_by_href: Dict[str, PolicyObject] = field(default_factory=dict)

    @abstractmethod
    def load_from_json(self, json: str) -> None:
        pass

    @abstractmethod
    def find_by_href_or_die(self, href: str) -> PolicyObject:
        pass

    @abstractmethod
    def find_by_name(self, name: str, *args, **kwargs) -> PolicyObject:
        """
        Performs a case-sensitive lookup and returns the Policy Object
        with the given name, or None if no such object exists
        """

    @abstractmethod
    def find_all_by_name(self, name: str, *args, **kwargs) -> List[PolicyObject]:
        """
        Performs a case-insensitive lookup and returns all Policy Objects
        matching the given name
        """
