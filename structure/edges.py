from typing import List, Set

from pydantic import BaseModel


# Base

class Edge(BaseModel):
    type: str
    type_a: str
    type_b: str
    uide_a: str
    uide_b: str
    polyline: str
    distance: float
    duration: float


# Intermediate edges
class Gamma(Edge):
    type_a: str = 'PPL'
    type_b: str = 'VPL'


class Alfa(Edge):
    type_a: str = 'PPL'
    type_b: str = 'VIA'


class Beta(Edge):
    type_a: str = 'VIA'
    type_b: str = 'VPL'


# Edges
class GammaWalk(Gamma):
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
