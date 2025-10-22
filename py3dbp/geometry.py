"""Geometry helpers used across the packing implementation.

The original project bundled these helpers in a module named
``auxiliary_methods`` with missing imports and without any documentation.  The
modernised version in this repository offers clear docstrings, type hints and a
small utility for dealing with ``Decimal`` rounding.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from .constants import Axis


@dataclass(frozen=True)
class Dimensions:
    """Light-weight container storing width, height and depth values."""

    width: Decimal
    height: Decimal
    depth: Decimal

    def as_tuple(self) -> tuple[Decimal, Decimal, Decimal]:
        return self.width, self.height, self.depth


def rect_intersect(item1, item2, axis_x: Axis, axis_y: Axis) -> bool:
    """Return ``True`` when the projections of two items intersect."""

    d1 = item1.get_dimension()
    d2 = item2.get_dimension()

    cx1 = item1.position[axis_x] + d1[axis_x] / 2
    cy1 = item1.position[axis_y] + d1[axis_y] / 2
    cx2 = item2.position[axis_x] + d2[axis_x] / 2
    cy2 = item2.position[axis_y] + d2[axis_y] / 2

    ix = abs(cx1 - cx2)
    iy = abs(cy1 - cy2)

    return ix < (d1[axis_x] + d2[axis_x]) / 2 and iy < (d1[axis_y] + d2[axis_y]) / 2


def intersect(item1, item2) -> bool:
    """Return ``True`` if two items intersect in 3D space."""

    return (
        rect_intersect(item1, item2, Axis.WIDTH, Axis.HEIGHT)
        and rect_intersect(item1, item2, Axis.HEIGHT, Axis.DEPTH)
        and rect_intersect(item1, item2, Axis.WIDTH, Axis.DEPTH)
    )


def get_limit_number_of_decimals(number_of_decimals: int) -> Decimal:
    """Return the quantisation mask for the desired decimal precision."""

    return Decimal("1.{}".format("0" * number_of_decimals))


def set_to_decimal(value: float | int | Decimal, number_of_decimals: int = 0) -> Decimal:
    """Round a numeric value to the desired number of decimals."""

    quant = get_limit_number_of_decimals(number_of_decimals)
    if isinstance(value, Decimal):
        return value.quantize(quant, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)

