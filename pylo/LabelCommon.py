from typing import Union

import pylo


class LabelCommon:

    def __init__(self, name: str, href: str, label_type: Union[int, str], owner: pylo.LabelStore):
        self.owner: pylo.LabelStore = owner
        self.name: str = name
        self.href: str = href

        if type(label_type) is str:
            if label_type == 'loc':
                label_type = pylo.label_type_loc
            elif label_type == 'env':
                label_type = pylo.label_type_env
            elif label_type == 'app':
                label_type = pylo.label_type_app
            elif label_type == 'role':
                label_type = pylo.label_type_role
            else:
                raise pylo.PyloEx("Tried to initialize a Label object with unsupported type '%s'" % (pylo.ltype))

        self._type = label_type

    def is_label(self) -> bool:
        raise pylo.PyloEx("not implemented")

    def is_group(self) -> bool:
        raise pylo.PyloEx("not implemented")

    def type_to_short_string(self):
        if self.type_is_location():
            return "loc"
        elif self.type_is_environment():
            return "env"
        elif self.type_is_application():
            return "app"
        elif self.type_is_role():
            return "role"

        raise pylo.PyloEx("unsupported yet")

    def type_is_location(self) -> bool:
        return self._type == pylo.label_type_loc

    def type_is_environment(self) -> bool:
        return self._type == pylo.label_type_env

    def type_is_application(self) -> bool:
        return self._type == pylo.label_type_app

    def type_is_role(self) -> bool:
        return self._type == pylo.label_type_role

    def type(self):
        return self._type

    def type_string(self) -> str:
        if self._type == pylo.label_type_loc:
            return 'loc'
        if self._type == pylo.label_type_env:
            return 'env'
        if self._type == pylo.label_type_app:
            return 'app'
        if self._type == pylo.label_type_role:
            return 'role'
        raise pylo.PyloEx("unsupported Label type #{} for label href={}".format(self._type, self.href))

    def api_set_name(self, new_name: str):
        find_collision = self.owner.find_label_by_name_and_type(new_name, self.type())
        if find_collision is not self:
            raise pylo.PyloEx("A Label/LabelGroup with name '{}' already exists".format(new_name))

        self.owner.owner.connector.objects_label_update(self.href, data={'name': new_name})
        self.name = new_name
