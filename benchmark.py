import time
import copy
import random

from matplotlib import pyplot as plt
from py3dbp import Packer, Bin, Item, Painter


def run_benchmark(
    skus,
    pallet_size=(1000, 1200, 1700),
    pallet_weight_limit=10000,
    boxes_per_test=140,
    num_tests=10,
    visualize=False
):
    cmap = plt.colormaps.get_cmap("tab20").resampled(len(skus))
    sku_colors = [
        tuple(int(255 * c) for c in cmap(i)[:3])
        for i in range(len(skus))
    ]

    boxes_per_sku = boxes_per_test // len(skus)  # equal count per SKU

    for test_idx in range(num_tests):
        random.seed(time.time() + test_idx)
        print(f"\n=== TEST {test_idx + 1} / {num_tests} ===")
        start = time.time()

        # Generate uniform queue of boxes (same count per SKU)
        item_queue = []
        for sku_index, (sku_name, sku_dims, sku_weight) in enumerate(skus):
            color_rgb = sku_colors[sku_index]
            for i in range(boxes_per_sku):
                # Randomly permute width-height-depth
                dims = list(sku_dims)
                random.shuffle(dims)
                item_queue.append(Item(
                    partno=f'{sku_name}-{test_idx}-{i}',
                    name=f'{sku_name}-Box-{test_idx}-{i}',
                    typeof='cube',
                    WHD=tuple(dims),  # Randomized orientation
                    weight=sku_weight,
                    level=1,
                    loadbear=100,
                    updown=True,
                    color=color_rgb
                ))

        # Full randomization of queue order — unique each test
        random.shuffle(item_queue)
        print(
            f"First 5 items in queue (test {test_idx}): {[item.partno for item in item_queue[:5]]}")

        # Pack
        packer = Packer()
        bin = Bin(
            f'Pallet-{test_idx + 1}',
            WHD=pallet_size,
            max_weight=pallet_weight_limit,
            corner=0,
            put_type=0
        )
        packer.addBin(bin)

        for item in item_queue:
            packer.addItem(copy.deepcopy(item))

        packer.pack(
            bigger_first=True,
            distribute_items=True,
            fix_point=True,
            check_stable=True,
            support_surface_ratio=0.75,
            number_of_decimals=0
        )

        bin = packer.bins[0]
        total_volume = bin.width * bin.height * bin.depth
        used_volume = sum(i.width * i.height * i.depth for i in bin.items)
        utilization = round((used_volume / total_volume) * 100, 2)

        # Report
        print(f"Items attempted : {len(item_queue)}")
        print(f"Items packed    : {len(bin.items)}")
        print(f"Used volume     : {used_volume} mm³")
        print(f"Total volume    : {total_volume} mm³")
        print(f"Utilization     : {utilization}%")
        print(f"Unfitted items  : {len(packer.unfit_items)}")
        print(f"Center of Mass  : {bin.gravity}")
        print(f"Time taken      : {round(time.time() - start, 2)} seconds")

        if visualize:
            painter = Painter(bin)
            painter.plotBoxAndItems(
                title=bin.partno, alpha=1.0, write_num=False)


# ============================================
# CONFIGURE BENCHMARK BELOW
# ============================================

if __name__ == "__main__":
    # Define 7 SKUs
    skus = [
        ("SKU-1", (200, 140, 140), 5),
        ("SKU-2", (320, 220, 150), 3),
        ("SKU-3", (350, 250, 150), 7),
        ("SKU-4", (300, 300, 300), 10),
        ("SKU-5", (370, 370, 250), 2),
        ("SKU-6", (430, 350, 250), 4),
        ("SKU-7", (590, 390, 250), 6)
    ]

    run_benchmark(
        skus=skus,
        pallet_size=(1000, 1200, 1700),  # Width x Depth x Height
        pallet_weight_limit=10000,
        boxes_per_test=140,
        num_tests=10,
        visualize=True  # Set True to visualize each test
    )
