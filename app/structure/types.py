from enum import Enum
from typing import Union

from pydantic import BaseModel


class Modals(str, Enum):
    WALK = 'WALK'
    TRANSIT = 'TRANSIT'
    BICYCLE = 'BICYCLE'
    CAR = 'CAR'


class AAA(str, Enum):
    std = 'std'
    rpt = 'rpt'
    obs = 'obs'


class StandardisedFormat(BaseModel):
    std: str = ""
    obs: str = ""
    rpt: str = ""


class VVMBase(BaseModel):
    type: AAA
    uide: str
    value: str


class VVMObserved(VVMBase):
    type: AAA = 'obs'
    std_uide: Union[str, None]
    rpt_uide: Union[str, None]


class VVMFormatted(VVMBase):
    is_bedrijfswagen: bool
    is_smart: bool
    traject: Union[Modals, None]
