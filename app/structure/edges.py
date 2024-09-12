from typing import Set

from pydantic import BaseModel, ConfigDict

from app.structure.nodes import NodeTypes
from app.structure.types import Modals


# Base

class Edge(BaseModel):
    type: str
    type_a: str
    type_b: str
    uide_a: str
    uide_b: str

    model_config = ConfigDict(extra='forbid')


class RouteEdge(Edge):
    polyline: str
    distance: float
    duration: float


# Intermediate edges
class Gamma(RouteEdge):
    type_a: NodeTypes = NodeTypes.PPL
    type_b: NodeTypes = NodeTypes.VPL
    type: Modals


class Alfa(RouteEdge):
    type_a: NodeTypes = NodeTypes.PPL
    type_b: NodeTypes = NodeTypes.VIA
    type: Modals


class Beta(RouteEdge):
    type_a: NodeTypes = NodeTypes.VIA
    type_b: NodeTypes = NodeTypes.VPL
    type: Modals


class DeltaPre(RouteEdge):
    type_a: NodeTypes = NodeTypes.PPL
    type_b: NodeTypes = NodeTypes.MEETINGPOINT
    type: Modals = Modals.CAR


class DeltaShared(RouteEdge):
    type_a: NodeTypes = NodeTypes.MEETINGPOINT
    type_b: NodeTypes = NodeTypes.MEETINGPOINT
    type: Modals = Modals.CAR


class DeltaPost(RouteEdge):
    type_a: NodeTypes = NodeTypes.MEETINGPOINT
    type_b: NodeTypes = NodeTypes.VPL
    type: Modals = Modals.CAR

# Edges


class PplVplOwnership(Edge):
    type_a: NodeTypes = NodeTypes.VPL
    type_b: NodeTypes = NodeTypes.PPL
    type: str = 'OWNER'
