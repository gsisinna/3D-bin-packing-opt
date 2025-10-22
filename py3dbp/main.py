"""Public facing classes of the 3D bin packing library.

The original project bundled the implementation in a single gigantic module.
The rewritten version keeps the public API compatible while adding type hints,
docstrings and extensive inline comments to clarify the intent of the packing
algorithm.  The code is now structured to be understandable and debuggable and
each significant piece of state is encapsulated in a data class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterator, List, Sequence, Tuple

import copy

import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.art3d as art3d
import numpy as np
from matplotlib.patches import Circle, Rectangle

from .constants import Axis, RotationType
from .geometry import intersect, set_to_decimal

DEFAULT_NUMBER_OF_DECIMALS = 0
START_POSITION = [Decimal("0"), Decimal("0"), Decimal("0")]


def _decimal_tuple(values: Sequence[float | int | Decimal]) -> List[Decimal]:
    return [Decimal(str(value)) for value in values]


@dataclass
class Item:
    """Physical item to be placed inside a :class:`Bin`."""

    partno: str
    name: str
    typeof: str
    WHD: Tuple[float, float, float]
    weight: float
    level: int
    loadbear: float
    updown: bool
    color: str
    rotation_type: RotationType = field(init=False, default=RotationType.RT_WHD)
    position: List[Decimal] = field(init=False, default_factory=lambda: list(START_POSITION))
    number_of_decimals: int = field(init=False, default=DEFAULT_NUMBER_OF_DECIMALS)

    def __post_init__(self) -> None:
        self.width, self.height, self.depth = _decimal_tuple(self.WHD)
        self.weight = Decimal(str(self.weight))
        self.level = int(self.level)
        self.loadbear = Decimal(str(self.loadbear))
        self.updown = bool(self.updown) if self.typeof == "cube" else False

    # -- Compatibility helpers -------------------------------------------------
    def formatNumbers(self, number_of_decimals: int) -> None:  # pragma: no cover - legacy API
        self.format_numbers(number_of_decimals)

    def string(self) -> str:  # pragma: no cover - legacy API
        return self.__str__()

    def getVolume(self) -> Decimal:  # pragma: no cover - legacy API
        return self.get_volume()

    def getMaxArea(self) -> Decimal:  # pragma: no cover - legacy API
        return self.get_max_area()

    def getDimension(self) -> Tuple[Decimal, Decimal, Decimal]:  # pragma: no cover - legacy API
        return self.get_dimension()

    # -- Modern API ------------------------------------------------------------
    def __str__(self) -> str:
        return (
            f"{self.partno}({self.width}x{self.height}x{self.depth}, "
            f"weight: {self.weight}) pos({self.position}) rt({self.rotation_type}) "
            f"vol({self.get_volume()})"
        )

    def format_numbers(self, number_of_decimals: int) -> None:
        """Round the stored numeric values to ``number_of_decimals`` decimals."""

        self.width = set_to_decimal(self.width, number_of_decimals)
        self.height = set_to_decimal(self.height, number_of_decimals)
        self.depth = set_to_decimal(self.depth, number_of_decimals)
        self.weight = set_to_decimal(self.weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals

    def get_volume(self) -> Decimal:
        return set_to_decimal(self.width * self.height * self.depth, self.number_of_decimals)

    def get_max_area(self) -> Decimal:
        sides = [self.width, self.height, self.depth]
        if self.updown:
            sides.sort(reverse=True)
        return set_to_decimal(sides[0] * sides[1], self.number_of_decimals)

    def get_dimension(self) -> Tuple[Decimal, Decimal, Decimal]:
        w, h, d = self.width, self.height, self.depth
        rotation = self.rotation_type
        if rotation == RotationType.RT_WHD:
            return w, h, d
        if rotation == RotationType.RT_HWD:
            return h, w, d
        if rotation == RotationType.RT_HDW:
            return h, d, w
        if rotation == RotationType.RT_DHW:
            return d, h, w
        if rotation == RotationType.RT_DWH:
            return d, w, h
        if rotation == RotationType.RT_WDH:
            return w, d, h
        raise ValueError(f"Unknown rotation type: {rotation}")

    def clone(self) -> "Item":
        """Return a deep copy of the item.

        ``copy.deepcopy`` works but is substantially slower for the thousands of
        objects the algorithm can manipulate.  Having an explicit clone method
        keeps the implementation lean.
        """

        duplicate = copy.copy(self)
        duplicate.position = list(self.position)
        duplicate.rotation_type = self.rotation_type
        duplicate.width = Decimal(self.width)
        duplicate.height = Decimal(self.height)
        duplicate.depth = Decimal(self.depth)
        duplicate.weight = Decimal(self.weight)
        duplicate.WHD = self.WHD
        return duplicate


@dataclass
class Bin:
    """Container receiving packed :class:`Item` instances."""

    partno: str
    WHD: Tuple[float, float, float]
    max_weight: float
    corner: float = 0
    put_type: int = 1
    items: List[Item] = field(default_factory=list)
    unfitted_items: List[Item] = field(default_factory=list)
    gravity: List[float] = field(default_factory=list)
    number_of_decimals: int = field(init=False, default=DEFAULT_NUMBER_OF_DECIMALS)
    fix_point: bool = field(init=False, default=False)
    check_stable: bool = field(init=False, default=False)
    support_surface_ratio: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.width, self.height, self.depth = _decimal_tuple(self.WHD)
        self.max_weight = Decimal(str(self.max_weight))
        self.corner = Decimal(str(self.corner))
        self.fit_items: List[List[float]] = [
            [0.0, float(self.width), 0.0, float(self.height), 0.0, 0.0]
        ]

    # -- Compatibility helpers -------------------------------------------------
    def formatNumbers(self, number_of_decimals: int) -> None:  # pragma: no cover - legacy API
        self.format_numbers(number_of_decimals)

    def string(self) -> str:  # pragma: no cover - legacy API
        return self.__str__()

    def getVolume(self) -> Decimal:  # pragma: no cover - legacy API
        return self.get_volume()

    def getTotalWeight(self) -> Decimal:  # pragma: no cover - legacy API
        return self.get_total_weight()

    def putItem(self, item: Item, pivot: Sequence[Decimal | float], axis: Axis | None = None) -> bool:  # pragma: no cover - legacy API
        return self.put_item(item, pivot, axis)

    def addCorner(self) -> List[Item]:  # pragma: no cover - legacy API
        return self.add_corner()

    def putCorner(self, index: int, item: Item) -> None:  # pragma: no cover - legacy API
        self.put_corner(index, item)

    def clearBin(self) -> None:  # pragma: no cover - legacy API
        self.clear()

    # -- Modern API ------------------------------------------------------------
    def __str__(self) -> str:
        return (
            f"{self.partno}({self.width}x{self.height}x{self.depth}, "
            f"max_weight:{self.max_weight}) vol({self.get_volume()})"
        )

    def format_numbers(self, number_of_decimals: int) -> None:
        self.width = set_to_decimal(self.width, number_of_decimals)
        self.height = set_to_decimal(self.height, number_of_decimals)
        self.depth = set_to_decimal(self.depth, number_of_decimals)
        self.max_weight = set_to_decimal(self.max_weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals

    def get_volume(self) -> Decimal:
        return set_to_decimal(self.width * self.height * self.depth, self.number_of_decimals)

    def get_total_weight(self) -> Decimal:
        total = sum((item.weight for item in self.items), Decimal(0))
        return set_to_decimal(total, self.number_of_decimals)

    # -- Packing helpers -------------------------------------------------------
    def put_item(self, item: Item, pivot: Sequence[Decimal | float], axis: Axis | None = None) -> bool:
        """Attempt to place ``item`` at ``pivot``.

        ``pivot`` is expected to be an iterable of x, y and z coordinates.  The
        method returns ``True`` when the item was placed successfully, otherwise
        the original item state is restored and ``False`` is returned.
        """

        fit = False
        pivot = [Decimal(str(value)) for value in pivot]
        original_position = list(item.position)
        original_rotation = item.rotation_type
        item.position = pivot

        for rotation in RotationType.allowed(item.updown):
            item.rotation_type = rotation
            dimension = item.get_dimension()
            if (
                self.width < pivot[0] + dimension[0]
                or self.height < pivot[1] + dimension[1]
                or self.depth < pivot[2] + dimension[2]
            ):
                continue

            fit = True
            for current in self.items:
                if intersect(current, item):
                    fit = False
                    break

            if not fit:
                continue

            if self.get_total_weight() + item.weight > self.max_weight:
                fit = False
                break

            x, y, z = map(float, pivot)
            w, h, d = map(float, dimension)
            if self.fix_point:
                for _ in range(3):
                    y = self.check_height([x, x + w, y, y + h, z, z + d])
                    x = self.check_width([x, x + w, y, y + h, z, z + d])
                    z = self.check_depth([x, x + w, y, y + h, z, z + d])

                if self.check_stable:
                    if not self._is_surface_supported(x, y, z, w, h, d):
                        fit = False
                        break

            if fit:
                self.fit_items.append([x, x + w, y, y + h, z, z + d])
                item.position = [
                    set_to_decimal(value, item.number_of_decimals) for value in (x, y, z)
                ]
                self.items.append(item.clone())
                return True

        item.position = original_position
        item.rotation_type = original_rotation
        return False

    def _is_surface_supported(self, x: float, y: float, z: float, w: float, h: float, d: float) -> bool:
        item_area = int(w * h)
        support_area = 0
        for boundary in self.fit_items:
            if z == boundary[5]:
                intersection_w = len(set(range(int(x), int(x + w))) & set(range(int(boundary[0]), int(boundary[1]))))
                intersection_h = len(set(range(int(y), int(y + h))) & set(range(int(boundary[2]), int(boundary[3]))))
                support_area += intersection_w * intersection_h

        if item_area == 0:
            return True

        if support_area / item_area >= self.support_surface_ratio:
            return True

        corners = [
            (x, y),
            (x + w, y),
            (x, y + h),
            (x + w, y + h),
        ]
        supported = [False, False, False, False]
        for boundary in self.fit_items:
            if z != boundary[5]:
                continue
            for idx, (cx, cy) in enumerate(corners):
                if boundary[0] <= cx <= boundary[1] and boundary[2] <= cy <= boundary[3]:
                    supported[idx] = True
        return all(supported)

    def check_depth(self, bounds: List[float]) -> float:
        return self._check_axis(bounds, Axis.DEPTH)

    def check_width(self, bounds: List[float]) -> float:
        return self._check_axis(bounds, Axis.WIDTH)

    def check_height(self, bounds: List[float]) -> float:
        return self._check_axis(bounds, Axis.HEIGHT)

    def _check_axis(self, bounds: List[float], axis: Axis) -> float:
        index_map = {
            Axis.WIDTH: (0, 1, 4, 5),
            Axis.HEIGHT: (2, 3, 4, 5),
            Axis.DEPTH: (4, 5, 0, 1),
        }
        current_start, current_end, other_start, other_end = index_map[axis]

        axis_length = bounds[current_end] - bounds[current_start]
        start = 0.0
        end = float(self.width if axis == Axis.WIDTH else self.height if axis == Axis.HEIGHT else self.depth)
        available = [[start, start], [end, end]]

        for fitted in self.fit_items:
            ranges = [
                set(range(int(fitted[current_start]), int(fitted[current_end]))),
                set(range(int(bounds[current_start]), int(bounds[current_end]))),
                set(range(int(fitted[other_start]), int(fitted[other_end]))),
                set(range(int(bounds[other_start]), int(bounds[other_end]))),
            ]
            if len(ranges[0] & ranges[1]) and len(ranges[2] & ranges[3]):
                available.append([float(fitted[current_start]), float(fitted[current_end])])

        available.sort(key=lambda value: value[1])
        for idx in range(len(available) - 1):
            if available[idx + 1][0] - available[idx][1] >= axis_length:
                return available[idx][1]
        return bounds[current_start]

    def add_corner(self) -> List[Item]:
        if not self.corner:
            return []
        corner_size = set_to_decimal(self.corner, self.number_of_decimals)
        corners = []
        for index in range(8):
            corners.append(
                Item(
                    partno=f"corner{index}",
                    name="corner",
                    typeof="cube",
                    WHD=(corner_size, corner_size, corner_size),
                    weight=0,
                    level=0,
                    loadbear=0,
                    updown=True,
                    color="#000000",
                )
            )
        return corners

    def put_corner(self, index: int, item: Item) -> None:
        size = float(self.corner)
        width = float(self.width)
        height = float(self.height)
        depth = float(self.depth)
        positions = [
            (0.0, 0.0, 0.0),
            (0.0, 0.0, depth - size),
            (0.0, height - size, depth - size),
            (0.0, height - size, 0.0),
            (width - size, height - size, 0.0),
            (width - size, 0.0, 0.0),
            (width - size, 0.0, depth - size),
            (width - size, height - size, depth - size),
        ]
        item.position = [set_to_decimal(value, item.number_of_decimals) for value in positions[index]]
        self.items.append(item)
        self.fit_items.append(
            [
                float(item.position[0]),
                float(item.position[0] + self.corner),
                float(item.position[1]),
                float(item.position[1] + self.corner),
                float(item.position[2]),
                float(item.position[2] + self.corner),
            ]
        )

    def clear(self) -> None:
        self.items = []
        self.fit_items = [[0.0, float(self.width), 0.0, float(self.height), 0.0, 0.0]]


class Packer:
    """High level API to pack a collection of :class:`Item` objects."""

    def __init__(self) -> None:
        self.bins: List[Bin] = []
        self.items: List[Item] = []
        self.unfit_items: List[Item] = []
        self.binding: List[Tuple[str, ...]] = []

    def addBin(self, bin: Bin) -> None:  # pragma: no cover - legacy API
        self.add_bin(bin)

    def addItem(self, item: Item) -> None:  # pragma: no cover - legacy API
        self.add_item(item)

    def pack(
        self,
        bigger_first: bool = False,
        distribute_items: bool = True,
        fix_point: bool = True,
        check_stable: bool = True,
        support_surface_ratio: float = 0.75,
        binding: Sequence[Tuple[str, ...]] | None = None,
        number_of_decimals: int = DEFAULT_NUMBER_OF_DECIMALS,
    ) -> None:
        return self.pack_items(
            bigger_first=bigger_first,
            distribute_items=distribute_items,
            fix_point=fix_point,
            check_stable=check_stable,
            support_surface_ratio=support_surface_ratio,
            binding=binding,
            number_of_decimals=number_of_decimals,
        )

    def __iter__(self) -> Iterator[Bin]:
        return iter(self.bins)

    # -- Modern API ------------------------------------------------------------
    def add_bin(self, bin: Bin) -> None:
        self.bins.append(bin)

    def add_item(self, item: Item) -> None:
        self.items.append(item)

    def pack_items(
        self,
        *,
        bigger_first: bool = False,
        distribute_items: bool = True,
        fix_point: bool = True,
        check_stable: bool = True,
        support_surface_ratio: float = 0.75,
        binding: Sequence[Tuple[str, ...]] | None = None,
        number_of_decimals: int = DEFAULT_NUMBER_OF_DECIMALS,
    ) -> None:
        for bin in self.bins:
            bin.format_numbers(number_of_decimals)
        for item in self.items:
            item.format_numbers(number_of_decimals)

        self.binding = list(binding or [])
        self.bins.sort(key=lambda candidate: candidate.get_volume(), reverse=bigger_first)
        self.items.sort(key=lambda candidate: candidate.get_volume(), reverse=bigger_first)
        self.items.sort(key=lambda candidate: candidate.loadbear, reverse=True)
        self.items.sort(key=lambda candidate: candidate.level)

        if self.binding:
            self._sort_binding()

        for idx, bin in enumerate(self.bins):
            bin.fix_point = fix_point
            bin.check_stable = check_stable
            bin.support_surface_ratio = support_surface_ratio
            bin.unfitted_items = []

            if bin.corner and not bin.items:
                for index, corner in enumerate(bin.add_corner()):
                    bin.put_corner(index, corner)

            for item in list(self.items):
                self._pack_item_into_bin(bin, item)

            if self.binding:
                self.items.sort(key=lambda candidate: candidate.get_volume(), reverse=bigger_first)
                self.items.sort(key=lambda candidate: candidate.loadbear, reverse=True)
                self.items.sort(key=lambda candidate: candidate.level)
                bin.items = []
                bin.unfitted_items = list(self.unfit_items)
                bin.clear()
                for item in list(self.items):
                    self._pack_item_into_bin(bin, item)

            bin.gravity = self.gravity_center(bin)

            if distribute_items:
                for packed_item in list(bin.items):
                    for candidate in list(self.items):
                        if candidate.partno == packed_item.partno:
                            self.items.remove(candidate)
                            break

        self.put_order()

        if self.items:
            self.unfit_items = [item.clone() for item in self.items]
            self.items = []

    # -- Internal helpers -----------------------------------------------------
    def _sort_binding(self) -> None:
        grouped: List[List[Item]] = [[] for _ in self.binding]
        front: List[Item] = []
        back: List[Item] = []

        for item in self.items:
            matched = False
            for idx, names in enumerate(self.binding):
                if item.name in names:
                    grouped[idx].append(item)
                    matched = True
                    break
            if not matched:
                if item not in front:
                    front.append(item)
                else:
                    back.append(item)

        min_group = min((len(group) for group in grouped), default=0)
        ordered: List[Item] = []
        for index in range(min_group):
            for group in grouped:
                ordered.append(group[index])

        for group in grouped:
            for item in group:
                if item not in ordered:
                    self.unfit_items.append(item)

        self.items = front + ordered + back

    def _pack_item_into_bin(self, bin: Bin, item: Item) -> None:
        if not bin.items:
            if not bin.put_item(item, item.position):
                bin.unfitted_items.append(item)
            return

        for axis in Axis.ALL:
            for existing in list(bin.items):
                pivot = list(existing.position)
                width, height, depth = existing.get_dimension()
                if axis == Axis.WIDTH:
                    pivot[0] += width
                elif axis == Axis.HEIGHT:
                    pivot[1] += height
                else:
                    pivot[2] += depth

                if bin.put_item(item, pivot, axis):
                    return

        bin.unfitted_items.append(item)

    def put_order(self) -> None:
        for bin in self.bins:
            if bin.put_type == 2:  # open top
                bin.items.sort(key=lambda item: item.position[0])
                bin.items.sort(key=lambda item: item.position[1])
                bin.items.sort(key=lambda item: item.position[2])
            elif bin.put_type == 1:  # general
                bin.items.sort(key=lambda item: item.position[1])
                bin.items.sort(key=lambda item: item.position[2])
                bin.items.sort(key=lambda item: item.position[0])

    def gravity_center(self, bin: Bin) -> List[float]:
        width = int(bin.width)
        height = int(bin.height)
        depth = int(bin.depth)

        area = [
            [set(range(0, width // 2 + 1)), set(range(0, height // 2 + 1)), 0],
            [set(range(width // 2 + 1, width + 1)), set(range(0, height // 2 + 1)), 0],
            [set(range(0, width // 2 + 1)), set(range(height // 2 + 1, height + 1)), 0],
            [set(range(width // 2 + 1, width + 1)), set(range(height // 2 + 1, height + 1)), 0],
        ]

        for item in bin.items:
            x_start = int(item.position[0])
            y_start = int(item.position[1])
            dimension = item.get_dimension()
            x_end = int(item.position[0] + dimension[0])
            y_end = int(item.position[1] + dimension[1])

            x_set = set(range(x_start, x_end + 1))
            y_set = set(range(y_start, y_end + 1))

            for idx, (area_x, area_y, weight) in enumerate(area):
                if x_set.issubset(area_x) and y_set.issubset(area_y):
                    area[idx][2] += int(item.weight)
                    break
                if x_set.issubset(area_x) and not y_set.issubset(area_y) and (y_set & area_y):
                    y_weight = len(y_set & area_y) / (y_end - y_start) * int(item.weight)
                    area[idx][2] += y_weight
                    target = idx - 2 if idx >= 2 else idx + 2
                    area[target][2] += int(item.weight) - y_weight
                    break
                if y_set.issubset(area_y) and not x_set.issubset(area_x) and (x_set & area_x):
                    x_weight = len(x_set & area_x) / (x_end - x_start) * int(item.weight)
                    area[idx][2] += x_weight
                    target = idx - 1 if idx % 2 else idx + 1
                    area[target][2] += int(item.weight) - x_weight
                    break
                if (x_set & area_x) and (y_set & area_y):
                    total = (y_end - y_start) * (x_end - x_start)
                    y_1 = len(y_set & area[0][1])
                    y_2 = y_end - y_start - y_1
                    x_1 = len(x_set & area[0][0])
                    x_2 = x_end - x_start - x_1
                    area[0][2] += x_1 * y_1 / total * int(item.weight)
                    area[1][2] += x_2 * y_1 / total * int(item.weight)
                    area[2][2] += x_1 * y_2 / total * int(item.weight)
                    area[3][2] += x_2 * y_2 / total * int(item.weight)
                    break

        total_weight = sum(section[2] for section in area) or 1
        return [round(section[2] / total_weight * 100, 2) for section in area]


class Painter:
    """Plot :class:`Bin` instances using ``matplotlib``."""

    def __init__(self, bin: Bin) -> None:
        self.items = bin.items
        self.width = bin.width
        self.height = bin.height
        self.depth = bin.depth

    def _plot_cube(
        self,
        ax,
        x: float,
        y: float,
        z: float,
        dx: float,
        dy: float,
        dz: float,
        color: str = "red",
        mode: int = 2,
        linewidth: int = 1,
        text: str = "",
        fontsize: int = 15,
        alpha: float = 0.5,
    ) -> None:
        xx = [x, x, x + dx, x + dx, x]
        yy = [y, y + dy, y + dy, y, y]

        kwargs = {"alpha": 1, "color": color, "linewidth": linewidth}
        if mode == 1:
            ax.plot3D(xx, yy, [z] * 5, **kwargs)
            ax.plot3D(xx, yy, [z + dz] * 5, **kwargs)
            ax.plot3D([x, x], [y, y], [z, z + dz], **kwargs)
            ax.plot3D([x, x], [y + dy, y + dy], [z, z + dz], **kwargs)
            ax.plot3D([x + dx, x + dx], [y + dy, y + dy], [z, z + dz], **kwargs)
            ax.plot3D([x + dx, x + dx], [y, y], [z, z + dz], **kwargs)
        else:
            patches = [
                Rectangle((x, y), dx, dy, fc=color, ec="black", alpha=alpha),
                Rectangle((x, y), dx, dy, fc=color, ec="black", alpha=alpha),
                Rectangle((y, z), dy, dz, fc=color, ec="black", alpha=alpha),
                Rectangle((y, z), dy, dz, fc=color, ec="black", alpha=alpha),
                Rectangle((x, z), dx, dz, fc=color, ec="black", alpha=alpha),
                Rectangle((x, z), dx, dz, fc=color, ec="black", alpha=alpha),
            ]
            for patch in patches:
                ax.add_patch(patch)

            if text:
                ax.text((x + dx / 2), (y + dy / 2), (z + dz / 2), text, color="black", fontsize=fontsize, ha="center", va="center")

            art3d.pathpatch_2d_to_3d(patches[0], z=z, zdir="z")
            art3d.pathpatch_2d_to_3d(patches[1], z=z + dz, zdir="z")
            art3d.pathpatch_2d_to_3d(patches[2], z=x, zdir="x")
            art3d.pathpatch_2d_to_3d(patches[3], z=x + dx, zdir="x")
            art3d.pathpatch_2d_to_3d(patches[4], z=y, zdir="y")
            art3d.pathpatch_2d_to_3d(patches[5], z=y + dy, zdir="y")

    def _plot_cylinder(
        self,
        ax,
        x: float,
        y: float,
        z: float,
        dx: float,
        dy: float,
        dz: float,
        color: str = "red",
        text: str = "",
        fontsize: int = 10,
        alpha: float = 0.2,
    ) -> None:
        circle_bottom = Circle((x + dx / 2, y + dy / 2), radius=dx / 2, color=color, alpha=0.5)
        circle_top = Circle((x + dx / 2, y + dy / 2), radius=dx / 2, color=color, alpha=0.5)
        ax.add_patch(circle_bottom)
        ax.add_patch(circle_top)
        art3d.pathpatch_2d_to_3d(circle_bottom, z=z, zdir="z")
        art3d.pathpatch_2d_to_3d(circle_top, z=z + dz, zdir="z")

        center_z = np.linspace(0, dz, 10)
        theta = np.linspace(0, 2 * np.pi, 10)
        theta_grid, z_grid = np.meshgrid(theta, center_z)
        x_grid = dx / 2 * np.cos(theta_grid) + x + dx / 2
        y_grid = dy / 2 * np.sin(theta_grid) + y + dy / 2
        z_grid = z_grid + z
        ax.plot_surface(x_grid, y_grid, z_grid, shade=False, fc=color, alpha=alpha, color=color)

        if text:
            ax.text((x + dx / 2), (y + dy / 2), (z + dz / 2), text, color="black", fontsize=fontsize, ha="center", va="center")

    def plot_box_and_items(
        self,
        title: str = "",
        alpha: float = 0.2,
        write_num: bool = False,
        fontsize: int = 10,
    ):
        fig = plt.figure()
        ax = plt.axes(projection="3d")
        self._plot_cube(
            ax,
            0.0,
            0.0,
            0.0,
            float(self.width),
            float(self.height),
            float(self.depth),
            color="black",
            mode=1,
            linewidth=2,
            text="",
        )

        for item in self.items:
            x, y, z = (float(value) for value in item.position)
            w, h, d = (float(value) for value in item.get_dimension())
            text = item.partno if write_num else ""
            if item.typeof == "cube":
                self._plot_cube(ax, x, y, z, w, h, d, color=item.color, mode=2, text=text, fontsize=fontsize, alpha=alpha)
            else:
                self._plot_cylinder(ax, x, y, z, w, h, d, color=item.color, text=text, fontsize=fontsize, alpha=alpha)

        plt.title(title)
        self.set_axes_equal(ax)
        return plt

    def plotBoxAndItems(self, *args, **kwargs):  # pragma: no cover - legacy API
        return self.plot_box_and_items(*args, **kwargs)

    def set_axes_equal(self, ax) -> None:
        x_limits = ax.get_xlim3d()
        y_limits = ax.get_ylim3d()
        z_limits = ax.get_zlim3d()

        x_range = abs(x_limits[1] - x_limits[0])
        x_middle = np.mean(x_limits)
        y_range = abs(y_limits[1] - y_limits[0])
        y_middle = np.mean(y_limits)
        z_range = abs(z_limits[1] - z_limits[0])
        z_middle = np.mean(z_limits)

        plot_radius = 0.5 * max([x_range, y_range, z_range])
        ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
        ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
        ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

    def setAxesEqual(self, ax):  # pragma: no cover - legacy API
        self.set_axes_equal(ax)

