from typing import Optional, Union, Dict

from .Exception import PyloEx
from .Helpers import nice_json
from .Label import Label
from .Rule import Rule
from .Ruleset import Ruleset
from .tmp import log


class RulesetStore:

    def __init__(self):
        self.items_by_href: Dict[str, Ruleset] = {}
        self.items_by_name: Dict[str, Ruleset] = {}

    def count_rulesets(self):
        return len(self.items_by_href)

    def count_rules(self):
        count = 0
        for ruleset in self.items_by_href.values():
            count += ruleset.count_rules()

        return count

    def load_rulesets_from_json(self, data):
        for json_item in data:
            self.load_single_ruleset_from_json(json_item)

    def load_single_ruleset_from_json(self, json_item):
        new_item = Ruleset(self)
        new_item.load_from_json(json_item)

        if new_item.href in self.items_by_href:
            raise PyloEx(
                "A Ruleset with href '%s' already exists in the table, please check your JSON data for consistency. JSON:\n%s"
                % (new_item.href, nice_json(json_item)))

        if new_item.name in self.items_by_name:
            print("The following Ruleset is conflicting (name already exists): '%s' Href: '%s'" % (
                self.items_by_name[new_item.name].name, self.items_by_name[new_item.name].href), flush=True)
            raise PyloEx(
                "A Ruleset with name '%s' already exists in the table, please check your JSON data for consistency. JSON:\n%s"
                % (new_item.name, nice_json(json_item)))

        self.items_by_href[new_item.href] = new_item
        self.items_by_name[new_item.name] = new_item

        log.debug("Found Ruleset '%s' with href '%s'" % (new_item.name, new_item.href))

        return new_item

    def find_rule_by_href(self, href: str) -> Rule:
        for ruleset in self.items_by_href.values():
            rule = ruleset.rules_by_href.get(href)
            if rule is not None:
                return rule

        return None

    def find_ruleset_by_name(self, name: str, case_sensitive=True) -> Ruleset:
        if case_sensitive:
            return self.items_by_name.get(name)

        lower_name = name.lower()

        for ruleset in self.items_by_href.values():
            if ruleset.name.lower() == lower_name:
                return ruleset

        return None

    def api_create_ruleset(self, name: str,
                           scope_app: Label = None,
                           scope_env: Label = None,
                           scope_loc: Label = None,
                           description: str = '', enabled: bool = True) -> Ruleset:
        con = self.owner.connector
        json_item = con.objects_ruleset_create(name, scope_app, scope_env, scope_loc, description, enabled)
        return self.load_single_ruleset_from_json(json_item)

    def api_delete_ruleset(self, ruleset: Union[str, Ruleset]):
        href = ruleset
        if isinstance(ruleset, Ruleset):
            href = ruleset.href

        find_object = self.items_by_href.get(href)
        if find_object is None:
            raise PyloEx("Cannot delete a Ruleset with href={} which is not part of this RulesetStore".format(href))

        self.owner.connector.objects_ruleset_delete(href)
        del self.items_by_href[href]
        del self.items_by_name[find_object.name]
