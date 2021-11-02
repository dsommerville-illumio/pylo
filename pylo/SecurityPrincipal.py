from dataclasses import dataclass
from typing import Optional

from .ReferenceTracker import ReferenceTracker


@dataclass
class SecurityPrincipal(ReferenceTracker):
    name: str
    href: str
    sid: str = None
    deleted: bool = False

    def __post_init__(self):
        ReferenceTracker.__init__(self)
