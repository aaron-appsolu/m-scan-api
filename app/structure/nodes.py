from enum import Enum
from typing import Set
from pydantic import BaseModel, ConfigDict, field_validator

from app.structure.types import StandardisedFormat


class NodeTypes(str, Enum):
    PPL = 'PPL'
    VPL = 'VPL'
    VIA = 'VIA'


# Base
class Node(BaseModel):
    type: NodeTypes
    lat: float
    lng: float
    uide: str
    model_config = ConfigDict(extra='forbid')


# Nodes
class PPL(Node):
    type: NodeTypes = NodeTypes.PPL
    vpl_uide: str
    owner: str
    address: str
    FTE: float
    vvm: StandardisedFormat
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


class VIA(Node):
    type: NodeTypes = NodeTypes.VIA
    name: str
    country: str
    via_type: str
