from typing import Set
from pydantic import BaseModel, ConfigDict, field_validator


# Base
class Node(BaseModel):
    type: str
    lat: float
    lng: float
    uide: str
    model_config = ConfigDict(extra='forbid')


# Nodes
class PPL(Node):
    type: str = 'PPL'
    owner: str
    address: str
    FTE: float
    raw: float
    wgh: float

    @field_validator('FTE')
    @classmethod
    def must_be_between_0_1(cls, v: float) -> float:
        if v > 1 or v < 0:
            raise ValueError(f'{v} is not between 0 and 1.')
        return v


class VPL(Node):
    type: str = 'VPL'
    name: str


class VIA(Node):
    type: str = 'VIA'
    name: str
    country: str
    via_type: str


nodes: Set[str] = {
    PPL.model_construct().type,
    VPL.model_construct().type,
    VIA.model_construct().type
}
