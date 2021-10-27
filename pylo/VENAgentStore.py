from typing import Dict

from .Exception import PyloEx
from .VENAgent import VENAgent
from .Workload import Workload


class VENAgentStore:

    def __init__(self):
        self.items_by_href: Dict[str, VENAgent] = {}

    def find_by_href_or_die(self, href: str) -> VENAgent:
        find_object = self.items_by_href.get(href)
        if find_object is None:
            raise PyloEx("Agent with ID {} was not found".format(href))

        return find_object

    def create_ven_agent_from_workload_record(self, workload: Workload, json_data) -> VENAgent:
        href = json_data.get('href')
        if href is None:
            raise PyloEx("Cannot extract Agent href from workload '{}'".format(workload.href))

        agent = VENAgent(href, workload)
        agent.load_from_json(json_data)

        self.items_by_href[href] = agent

        return agent

    def count_agents(self) -> int:
        return len(self.items_by_href)
