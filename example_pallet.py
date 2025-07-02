from matplotlib import pyplot as plt
from py3dbp import Packer, Bin, Item, Painter
import time
import copy

start = time.time()

# Pallet config
pallet_size = (1000, 1200, 1800)
pallet_weight_limit = 10000

# SKU definitions: (name, (W, H, D), weight)
skus = [
    ("SKU-1", (400, 250, 200), 5),
    ("SKU-2", (300, 200, 150), 3),
    ("SKU-3", (500, 300, 200), 7),
    ("SKU-4", (600, 400, 300), 10),
    ("SKU-5", (200, 200, 100), 2),
    ("SKU-6", (350, 300, 250), 4),
    ("SKU-7", (300, 300, 300), 6),
    ("SKU-8", (250, 150, 100), 1),
    ("SKU-9", (450, 350, 200), 8),
    ("SKU-10", (500, 400, 200), 9),
]

# Precompute colors
cmap = plt.colormaps.get_cmap("tab20").resampled(len(skus))
sku_colors = [
    tuple(int(255 * c) for c in cmap(i)[:3])  # RGB 0–255
    for i in range(len(skus))
]

# Track added items
added_items = []
added_count = 0
max_attempts = 1000

while added_count < max_attempts:
    sku_index = added_count % len(skus)
    sku_name, sku_dims, sku_weight = skus[sku_index]
    color_rgb = sku_colors[sku_index]  # color based on SKU type

    new_item = Item(
        partno=f'{sku_name}-{added_count}',
        name=f'{sku_name}-Box-{added_count}',
        typeof='cube',
        WHD=sku_dims,
        weight=sku_weight,
        level=1,
        loadbear=100,
        updown=True,
        color=color_rgb
    )

    # Simulate packing with all added items + new one
    test_packer = Packer()
    test_bin = Bin('Pallet-1', pallet_size,
                   max_weight=pallet_weight_limit, corner=0, put_type=0)
    test_packer.addBin(test_bin)

    for item in added_items + [new_item]:
        test_packer.addItem(copy.deepcopy(item))

    test_packer.pack(
        bigger_first=True,
        distribute_items=True,
        fix_point=True,
        check_stable=True,
        support_surface_ratio=0.75,
        number_of_decimals=0
    )

    if test_packer.unfit_items:
        print(
            f"\nStopped at {added_count} items. Could not fit: {new_item.partno}")
        break

    added_items.append(new_item)
    added_count += 1

# Final packing with all successfully added items
final_packer = Packer()
final_bin = Bin('Pallet-1', pallet_size,
                max_weight=pallet_weight_limit, corner=0, put_type=0)
final_packer.addBin(final_bin)

for item in added_items:
    final_packer.addItem(item)

final_packer.pack(
    bigger_first=True,
    distribute_items=True,
    fix_point=True,
    check_stable=True,
    support_surface_ratio=0.75,
    number_of_decimals=0
)

final_packer.putOrder()

# Report
print("\n================== FINAL PALLET REPORT ==================\n")
for b in final_packer.bins:
    print(f"Pallet: {b.partno}")
    print("---------------------------------------------------------")
    volume = b.width * b.height * b.depth
    volume_t = 0
    for item in b.items:
        print(f"{item.partno} at {item.position}, rotated={item.rotation_type} "
              f"size={item.width}x{item.height}x{item.depth} "
              f"vol={item.width * item.height * item.depth}")
        volume_t += item.width * item.height * item.depth

    print("---------------------------------------------------------")
    utilization = round(float(volume_t) / float(volume) * 100, 2)
    print(f"Used Volume: {volume_t} mm³")
    print(f"Total Volume: {volume} mm³")
    print(f"Utilization: {utilization}%")
    print(f"Residual Volume: {volume - volume_t} mm³")
    print(f"Gravity Center: {b.gravity}")
    print("---------------------------------------------------------")

    # Visualize
    painter = Painter(b)
    fig = painter.plotBoxAndItems(
        title=b.partno,
        alpha=1.0,
        write_num=False,
        fontsize=10
    )

# Unfitted (should be 0 here)
print("\n================ UNFITTED ITEMS ================\n")
if not final_packer.unfit_items:
    print("All items successfully packed.")
else:
    for item in final_packer.unfit_items:
        print(f"{item.partno} - {item.width}x{item.height}x{item.depth}")

stop = time.time()
print(f"\nTotal Time Used: {round(stop - start, 2)} seconds")
