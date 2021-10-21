from enum import Enum

ROLE_LABEL_TYPE = 0
APP_LABEL_TYPE = 1
ENV_LABEL_TYPE = 2
LOC_LABEL_TYPE = 3


class LabelType(Enum):
    ROLE = ROLE_LABEL_TYPE
    APP = APP_LABEL_TYPE
    ENV = ENV_LABEL_TYPE
    LOC = LOC_LABEL_TYPE

ICMP = 1
TCP = 6
UDP = 17


class Protocol(Enum):
    ICMP = ICMP
    TCP = TCP
    UDP = UDP
