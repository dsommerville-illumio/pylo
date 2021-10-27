from typing import Optional

from .ReferenceTracker import ReferenceTracker


class SecurityPrincipal(ReferenceTracker):
    def __init__(self, name: str, href: str):
        ReferenceTracker.__init__(self)
        self.name: str = name
        self.href: str = href
        self.sid: Optional[str] = None
        self.deleted: bool = False

        self.raw_json = None

    def load_from_json(self, data):
        self.raw_json = data

        self.sid = data['sid']
        self.deleted = data['deleted']
