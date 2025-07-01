from .palletizer import palletize_single_sku
from .models import PalletizationRequest, PalletizationResponse
from fastapi import FastAPI
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


app = FastAPI(title="Palletizer API", version="1.0")


@app.post("/palletize", response_model=PalletizationResponse)
def palletize(req: PalletizationRequest):
    sku_size = (
        float(req.box.length),
        float(req.box.width),
        float(req.box.height)
    )
    pallet_size = (
        float(req.pallet.length),
        float(req.pallet.width),
        float(req.pallet.height)
    )

    result = palletize_single_sku(
        sku_size,
        float(req.box.weight),
        pallet_size,
        float(req.pallet.max_weight)
    )

    return result
