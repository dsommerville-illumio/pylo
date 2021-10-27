from typing import Union

from .Exception import PyloEx
from .Helpers import LOC_LABEL_TYPE, ENV_LABEL_TYPE, APP_LABEL_TYPE, ROLE_LABEL_TYPE


class LabelCommon:

    def __init__(self, name: str, href: str, label_type: Union[int, str]):
        self.name: str = name
        self.href: str = href

        if type(label_type) is str:
            if label_type == 'loc':
                label_type = LOC_LABEL_TYPE
            elif label_type == 'env':
                label_type = ENV_LABEL_TYPE
            elif label_type == 'app':
                label_type = APP_LABEL_TYPE
            elif label_type == 'role':
                label_type = ROLE_LABEL_TYPE
            else:
                raise PyloEx("Tried to initialize a Label object with unsupported type '%s'" % (label_type))

        self._type = label_type

    def is_label(self) -> bool:
        raise PyloEx("not implemented")

    def is_group(self) -> bool:
        raise PyloEx("not implemented")

    def type_to_short_string(self):
        if self.type_is_location():
            return "loc"
        elif self.type_is_environment():
            return "env"
        elif self.type_is_application():
            return "app"
        elif self.type_is_role():
            return "role"

        raise PyloEx("unsupported yet")

    def type_is_location(self) -> bool:
        return self._type == LOC_LABEL_TYPE

    def type_is_environment(self) -> bool:
        return self._type == ENV_LABEL_TYPE

    def type_is_application(self) -> bool:
        return self._type == APP_LABEL_TYPE

    def type_is_role(self) -> bool:
        return self._type == ROLE_LABEL_TYPE

    def type(self):
        return self._type

    def type_string(self) -> str:
        if self._type == LOC_LABEL_TYPE:
            return 'loc'
        if self._type == ENV_LABEL_TYPE:
            return 'env'
        if self._type == APP_LABEL_TYPE:
            return 'app'
        if self._type == ROLE_LABEL_TYPE:
            return 'role'
        raise PyloEx("unsupported Label type #{} for label href={}".format(self._type, self.href))

    def api_set_name(self, new_name: str):
        # FIXME
        # find_collision = self.owner.find_label_by_name_and_type(new_name, self.type())
        # if find_collision is not self:
        #     raise PyloEx("A Label/LabelGroup with name '{}' already exists".format(new_name))

        # self.owner.owner.connector.objects_label_update(self.href, data={'name': new_name})
        # self.name = new_name
        pass
