from py3dbp import Packer, Bin, Item, Painter
import time
import copy
import itertools
import matplotlib.pyplot as plt

# Define pallet
PALLET_SIZE = (1000, 1200, 1800)
PALLET_WEIGHT_LIMIT = 1000

# Single SKU to benchmark
SKU_NAME = "BenchmarkBox"
SKU_SIZE = (400, 250, 200)
SKU_WEIGHT = 5

# Generate all possible planar rotations
def planar_rotations(size):
    w, h, d = size
    # Only allow rotations that preserve 'height' in the same axis (second)
    return [(w, d, h), (d, w, h)]


# Store results and visuals
results = []

print("\n=== Benchmarking All Rotations ===\n")

# Create a figure for each result
figures = []

# Test each rotation
for i, rot_dims in enumerate(planar_rotations(SKU_SIZE), 1):
    print(f"Test #{i}: Orientation {rot_dims}")
    start = time.time()

    added_items = []
    count = 0
    max_attempts = 1000

    while count < max_attempts:
        item = Item(
            partno=f"{SKU_NAME}-{count}",
            name=f"{SKU_NAME}-Box-{count}",
            typeof='cube',
            WHD=rot_dims,
            weight=SKU_WEIGHT,
            level=1,
            loadbear=100,
            updown=True,
            color='skyblue'
        )

        test_packer = Packer()
        test_bin = Bin('Pallet-1', PALLET_SIZE,
                       max_weight=PALLET_WEIGHT_LIMIT, corner=0, put_type=0)
        test_packer.addBin(test_bin)

        for it in added_items + [item]:
            test_packer.addItem(copy.deepcopy(it))

        test_packer.pack(
            bigger_first=True,
            distribute_items=True,
            fix_point=True,
            check_stable=True,
            support_surface_ratio=0.75,
            number_of_decimals=0
        )

        if test_packer.unfit_items:
            break

        added_items.append(item)
        count += 1

    # Finalize with all accepted items
    final_packer = Packer()
    final_bin = Bin(f'Pallet-{i}', PALLET_SIZE,
                    max_weight=PALLET_WEIGHT_LIMIT, corner=0, put_type=0)
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

    stop = time.time()

    # Volume & stats
    pallet_vol = PALLET_SIZE[0] * PALLET_SIZE[1] * PALLET_SIZE[2]
    item_vol = rot_dims[0] * rot_dims[1] * rot_dims[2]
    total_vol = item_vol * len(final_bin.items)
    utilization = round(total_vol / pallet_vol * 100, 2)

    print(f"  → Fitted Items: {len(final_bin.items)}")
    print(f"  → Volume Utilization: {utilization}%")
    print(f"  → Time: {round(stop - start, 3)} sec\n")

    # Store result and figure
    results.append({
        'rotation': rot_dims,
        'count': len(final_bin.items),
        'utilization': utilization,
        'time': round(stop - start, 3),
        'bin': final_bin
    })

    painter = Painter(final_bin)
    fig = painter.plotBoxAndItems(
        title=f'Rotation {rot_dims}',
        alpha=0.8,
        write_num=False,
        fontsize=9
    )
    figures.append(fig)

# Summary
print("\n====== Benchmark Summary ======\n")
for r in results:
    print(
        f"Rotation: {r['rotation']} → Items: {r['count']} | Utilization: {r['utilization']}% | Time: {r['time']}s")

# Best result
best = max(results, key=lambda x: x['count'])
print(f"\nBest Rotation: {best['rotation']} → {best['count']} items packed.")

# Show all 3D visualizations
print("\nShowing 3D visualizations for each orientation...\n")
for fig in figures:
    fig.show()
