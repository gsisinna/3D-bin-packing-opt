from py3dbp import Packer, Bin, Item, Painter
import time
import copy
import itertools
import matplotlib.pyplot as plt

# Define pallet
PALLET_SIZE = (1000, 1200, 1800)
PALLET_WEIGHT_LIMIT = 5000

# Single SKU to benchmark
SKU_NAME = "BenchmarkBox"
SKU_SIZE = (300, 200, 150)
SKU_WEIGHT = 5

# Generate all possible planar rotations


def planar_rotations(size):
    w, h, d = size
    # Only allow rotations that preserve 'height' in the same axis (second)
    return [(w, d, h), (d, w, h)]


def cross_layer_rotations(size):
    # Return two alternating planar rotations
    w, h, d = size
    return [(w, d, h), (d, w, h)]


# Store results and visuals
results = []

# Create a figure for each result
figures = []

rotations = cross_layer_rotations(SKU_SIZE)
max_layers = 1000  # to prevent infinite loops
layer_height = rotations[0][2]  # assuming fixed height from rotation

print(f"\n=== Cross Layer Packing Benchmark ===\n")

test_packer = Packer()
test_bin = Bin('Pallet-CrossLayer', PALLET_SIZE,
               max_weight=PALLET_WEIGHT_LIMIT, corner=0, put_type=0)
test_packer.addBin(test_bin)

item_index = 0
layer_index = 0
z_offset = 0

while z_offset + layer_height <= PALLET_SIZE[2]:
    current_rotation = rotations[layer_index % 2]
    current_items = []
    temp_packer = Packer()
    temp_bin = Bin('TempBin', (PALLET_SIZE[0], PALLET_SIZE[1], layer_height),
                   max_weight=PALLET_WEIGHT_LIMIT, corner=0, put_type=0)
    temp_packer.addBin(temp_bin)

    # Attempt to fill one full layer
    while True:
        item = Item(
            partno=f"{SKU_NAME}-{item_index}",
            name=f"{SKU_NAME}-Box-{item_index}",
            typeof='cube',
            WHD=current_rotation,
            weight=SKU_WEIGHT,
            level=1,
            loadbear=100,
            updown=True,
            color='skyblue'
        )
        temp_packer.addItem(item)
        temp_packer.pack(
            bigger_first=True,
            distribute_items=True,
            fix_point=True,
            check_stable=True,
            support_surface_ratio=0.75,
            number_of_decimals=0
        )

        if temp_packer.unfit_items:
            break
        else:
            current_items.append(item)
            item_index += 1

    if not current_items:
        break  # No items fit in this layer, stop building more

    # Offset z-position and add items to main bin
    for item in current_items:
        item.position = (
            item.position[0],
            item.position[1],
            item.position[2] + z_offset  # lift to new layer
        )
        test_packer.addItem(item)

    z_offset += layer_height
    layer_index += 1

# Final packing for visualization
test_packer.pack(
    bigger_first=True,
    distribute_items=True,
    fix_point=True,
    check_stable=True,
    support_surface_ratio=0.75,
    number_of_decimals=0
)

# Compute stats
final_bin = test_packer.bins[0]
item_count = len(final_bin.items)
item_vol = SKU_SIZE[0] * SKU_SIZE[1] * SKU_SIZE[2]
pallet_vol = PALLET_SIZE[0] * PALLET_SIZE[1] * PALLET_SIZE[2]
total_vol = item_vol * item_count
utilization = round(total_vol / pallet_vol * 100, 2)

print(f"Cross-layer packed {item_count} items.")
print(f"Volume Utilization: {utilization}%")

# Visualization
painter = Painter(final_bin)
fig = painter.plotBoxAndItems(
    title='Cross-Layer Packing',
    alpha=0.8,
    write_num=False,
    fontsize=9
)
fig.show()
