import os
import sys

parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendors')
sys.path.append(vendor_dir)

from .tmp import *
from .Helpers import *
from .stores import *
from .policyobjects import *

from .Exception import PyloEx, PyloApiEx, PyloApiTooManyRequestsEx, PyloApiUnexpectedSyntax
from .SoftwareVersion import SoftwareVersion
from .IPMap import IP4Map
from .ReferenceTracker import ReferenceTracker, Referencer, Pathable
from .APIConnector import APIConnector
from .IPList import IPList
from .IPListStore import IPListStore
from .VENAgent import VENAgent
from .VENAgentStore import VENAgentStore
from .Workload import Workload, WorkloadInterface
from .WorkloadStore import WorkloadStore
from .VirtualService import VirtualService
from .VirtualServiceStore import VirtualServiceStore
from .Service import Service, PortMap, ServiceEntry
from .ServiceStore import ServiceStore
from .Rule import Rule, RuleServiceContainer, RuleSecurityPrincipalContainer, DirectServiceInRule, RuleHostContainer
from .Ruleset import Ruleset, RulesetScope, RulesetScopeEntry
from .RulesetStore import RulesetStore
from .SecurityPrincipal import SecurityPrincipal
from .SecurityPrincipalStore import SecurityPrincipalStore
from .Organization import Organization
from .Query import Query


ignoreWorkloadsWithSameName = True

objectNotFound = object()









