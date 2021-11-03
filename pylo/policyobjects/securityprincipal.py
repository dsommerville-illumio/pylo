from dataclasses import dataclass

from .policyobject import PolicyObject


@dataclass
class SecurityPrincipal(PolicyObject):
    sid: str = None
    deleted: bool = False

    __hash__ = PolicyObject.__hash__
