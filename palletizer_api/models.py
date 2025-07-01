from pydantic import BaseModel
from typing import List


class BoxSpec(BaseModel):
    length: float
    width: float
    height: float
    weight: float


class PalletSpec(BaseModel):
    length: float
    width: float
    height: float
    max_weight: float


class PalletizationRequest(BaseModel):
    box: BoxSpec
    pallet: PalletSpec


class BoxPlacement(BaseModel):
    box_id: int
    dimensions: dict
    grasp_offset: dict
    grasp_point: dict
    layer_id: int
    rotated: bool
    rotation: int


class PalletizationResponse(BaseModel):
    pallet_stack: List[BoxPlacement]
    item_count: int
    utilization: float
