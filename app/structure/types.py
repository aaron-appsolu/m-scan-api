from enum import Enum
from typing import Union, List, Dict

from pydantic import BaseModel, ConfigDict


class Colours(BaseModel):
    nu: str
    potential: str


class Modals(str, Enum):
    WALK = 'WALK'
    TRANSIT = 'TRANSIT'
    BICYCLE = 'BICYCLE'
    CAR = 'CAR'
    CARPOOL = 'CARPOOL'


class VVMTypes(str, Enum):
    std = 'std'
    rpt = 'rpt'
    obs = 'obs'


class VVMBase(BaseModel):
    type: VVMTypes
    uide: str
    value: str
    owner: str


class VVMObserved(VVMBase):
    type: VVMTypes = VVMTypes.obs
    std_uide: Union[str, None]
    rpt_uide: Union[str, None]


class VVMFormatted(VVMBase):
    is_bedrijfswagen: bool
    is_smart: bool
    traject: Union[Modals, None]
    icon_uide: Union[str, None]
    colour: Colours
    lastEdited: str


class Route(BaseModel):
    route_type: str
    features_zlib: str
    excluded_from: List[str]
    route_id: str
    total_distance: float
    total_duration: float
    uide: str

    model_config = ConfigDict(extra='ignore')


class Language(BaseModel):
    uide: str
    translations: Dict[str, str]
