from enum import Enum
from random import random
from typing import Union

from pydantic import BaseModel, ConfigDict, field_validator, computed_field


def jitter(n: float):
    rand = (.5 - random()) * 0.0005
    return n + rand


class NodeTypes(str, Enum):
    PPL = 'PPL'
    VPL = 'VPL'
    VIA = 'VIA'
    MEETINGPOINT = 'MEETINGPOINT'


# Base
class Node(BaseModel):
    type: NodeTypes
    lat: float
    lng: float
    uide: str

    @computed_field
    @property
    def lat_jitter(self) -> float:
        return jitter(self.lat)

    @computed_field
    @property
    def lng_jitter(self) -> float:
        return jitter(self.lng)

    model_config = ConfigDict(extra='forbid')


# Nodes
class PPL(Node):
    type: NodeTypes = NodeTypes.PPL
    vpl_uide: str
    owner: str
    address: Union[str, None]
    FTE: float
    vvm_uide: str
    raw: float
    wgh: float

    model_config = ConfigDict(extra="ignore")

    @field_validator('FTE')
    @classmethod
    def must_be_between_0_1(cls, v: float) -> float:
        if v > 1 or v < 0:
            raise ValueError(f'{v} is not between 0 and 1.')
        return v


class VPL(Node):
    type: NodeTypes = NodeTypes.VPL
    name: str
    owner: str


class VIA(Node):
    type: NodeTypes = NodeTypes.VIA
    name: str
    country: str
    via_type: str


class MEETINGPOINT(Node):
    type: NodeTypes = NodeTypes.MEETINGPOINT
