from typing import Set

from pydantic import BaseModel, ConfigDict

from structure.nodes import NodeTypes


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


class Alfa(RouteEdge):
    type_a: NodeTypes = NodeTypes.PPL
    type_b: NodeTypes = NodeTypes.VIA


class Beta(RouteEdge):
    type_a: NodeTypes = NodeTypes.VIA
    type_b: NodeTypes = NodeTypes.VPL


# Edges
class PplVplOwnership(Edge):
    type_a: NodeTypes = NodeTypes.VPL
    type_b: NodeTypes = NodeTypes.PPL
    type: str = 'OWNER'


class GammaWalk(RouteEdge):
    type: str = 'WALK'


class GammaCar(Gamma):
    type: str = 'CAR'


class GammaTransit(Gamma):
    type: str = 'TRANSIT'


class GammaBicycle(Gamma):
    type: str = 'BICYCLE'


class AlfaWalk(Alfa):
    type: str = 'WALK'


class AlfaCar(Alfa):
    type: str = 'CAR'


class AlfaTransit(Alfa):
    type: str = 'TRANSIT'


class AlfaBicycle(Alfa):
    type: str = 'BICYCLE'


class BetaWalk(Beta):
    type: str = 'WALK'


class BetaCar(Beta):
    type: str = 'CAR'


class BetaTransit(Beta):
    type: str = 'TRANSIT'


class BetaBicycle(Beta):
    type: str = 'BICYCLE'


edges: Set[str] = {
    GammaWalk.model_construct().type,
    GammaCar.model_construct().type,
    GammaTransit.model_construct().type,
    GammaBicycle.model_construct().type,
    AlfaWalk.model_construct().type,
    AlfaCar.model_construct().type,
    AlfaTransit.model_construct().type,
    AlfaBicycle.model_construct().type,
    BetaWalk.model_construct().type,
    BetaCar.model_construct().type,
    BetaTransit.model_construct().type,
    BetaBicycle.model_construct().type,
}
