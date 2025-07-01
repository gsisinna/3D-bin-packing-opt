from typing import Tuple, Dict
from .utils import convert_decimal
from py3dbp import Packer, Bin, Item
import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


def cross_layer_rotations(size):
    w, h, d = size
    return [(w, d, h), (d, w, h)]


def palletize_single_sku(
    sku_size: Tuple[float, float, float],
    sku_weight: float,
    pallet_size: Tuple[float, float, float],
    weight_limit: float
) -> Dict:

    MAX_ITEMS_PER_LAYER = 500  # safety limit to prevent infinite packing

    packer = Packer()
    bin = Bin('Pallet-CrossLayer', pallet_size,
              max_weight=weight_limit, corner=0, put_type=0)
    packer.addBin(bin)

    rotations = cross_layer_rotations(sku_size)
    layer_height = rotations[0][2]
    item_index = 0
    layer_index = 0
    z_offset = 0

    while z_offset + layer_height <= pallet_size[2]:
        current_rotation = rotations[layer_index % 2]
        current_items = []
        temp_packer = Packer()
        temp_bin = Bin('TempBin', (pallet_size[0], pallet_size[1], layer_height),
                       max_weight=weight_limit, corner=0, put_type=0)
        temp_packer.addBin(temp_bin)

        items_added = 0
        for i in range(MAX_ITEMS_PER_LAYER):
            item = Item(
                partno=f"Box-{item_index}",
                name=f"Box-{item_index}",
                typeof='cube',
                WHD=current_rotation,
                weight=sku_weight,
                level=1,
                loadbear=100,
                updown=True,
                color='skyblue'
            )
            temp_packer.addItem(item)
            try:
                temp_packer.pack(
                    bigger_first=True,
                    distribute_items=True,
                    fix_point=True,
                    check_stable=True,
                    support_surface_ratio=0.75,
                    number_of_decimals=0
                )
            except Exception as e:
                print(
                    f"Packing error in layer {layer_index}, item {item_index}: {e}")
                break

            if temp_packer.unfit_items:
                break

            current_items.append(item)
            item_index += 1
            items_added += 1

        if items_added == 0:
            break  # stop adding new layers if no items could be added

        # Move items to the main packer with adjusted z-offset
        for item in current_items:
            item.position = (
                float(item.position[0]),
                float(item.position[1]),
                float(item.position[2]) + z_offset
            )
            packer.addItem(item)

        z_offset += layer_height
        layer_index += 1

    # Final pack
    try:
        packer.pack(
            bigger_first=True,
            distribute_items=True,
            fix_point=True,
            check_stable=True,
            support_surface_ratio=0.75,
            number_of_decimals=0
        )
    except Exception as e:
        print(f"Final packing error: {e}")

    final_bin = packer.bins[0]
    item_count = len(final_bin.items)
    item_vol = sku_size[0] * sku_size[1] * sku_size[2]
    pallet_vol = pallet_size[0] * pallet_size[1] * pallet_size[2]
    total_vol = item_vol * item_count
    utilization = round(total_vol / pallet_vol * 100, 2)

    layer_height = rotations[0][2]
    stack = []

    for i, item in enumerate(final_bin.items):
        l, w, h = map(float, item.getDimension())
        x, y, z = map(float, item.position)

        lx, wy, hz = float(l), float(w), float(h)
        xx, yy, zz = float(x), float(y), float(z)

        rotated = (round(lx), round(wy)) != (sku_size[0], sku_size[1])
        layer_id = int(zz // layer_height)
        rotation_id = layer_id % 2

        stack.append({
            "box_id": i,
            "dimensions": {"length": lx, "width": wy, "height": hz},
            "grasp_offset": {"dx": 0, "dy": 0, "dz": 0},
            "grasp_point": {"x": xx + lx / 2, "y": yy + wy / 2, "z": zz + hz / 2},
            "layer_id": layer_id,
            "rotated": rotated,
            "rotation": rotation_id
        })

    return {
        "pallet_stack": convert_decimal(stack),
        "item_count": item_count,
        "utilization": utilization
    }
