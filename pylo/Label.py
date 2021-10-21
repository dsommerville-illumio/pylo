import pylo


class Label(pylo.ReferenceTracker, pylo.LabelCommon):
    def __init__(self, name, href, ltype, owner: 'pylo.LabelStore'):
        pylo.ReferenceTracker.__init__(self)
        pylo.LabelCommon.__init__(self, name, href, ltype, owner)

    def is_group(self) -> bool:
        return False

    def is_label(self) -> bool:
        return True

    def reference_obj(self):
        return {"href": self.href,
                "value": self.name,
                "key": self.type_to_short_string()}

    def get_api_reference_json(self):
        return {'label': {'href': self.href}}

