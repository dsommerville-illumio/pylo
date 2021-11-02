from  .ReferenceTracker import ReferenceTracker


class VirtualService(ReferenceTracker):
    def __init__(self, name: str, href: str):
        super().__init__()
        self.name: str = name
        self.href: str = href

        self.raw_json = None

    def load_from_json(self, data):
        self.raw_json = data
