from typing import List, Set
from pydantic import BaseModel


# Base
class Node(BaseModel):
    type: str
    lat: float
    lng: float
    uide: str


# Nodes
class PPL(Node):
    type: str = 'PPL'
    owner: str
    address: str


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
