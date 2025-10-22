"""Constants used by the 3D bin packing implementation.

This module provides small enumerations to make the rest of the code more
expressive.  The original project represented axes and rotation types by using
magic integers sprinkled throughout the implementation which made the code
harder to follow.  Using :class:`enum.IntEnum` keeps full backwards
compatibility – the values can still be used as integers – while giving the
attributes meaningful names that help static analysers and human readers alike.
"""

from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, List


class RotationType(IntEnum):
    """The possible axis aligned orientations of an item.

    The class emulates the behaviour of the original ``RotationType`` helper by
    exposing ``ALL`` and ``NOT_UPSIDE_DOWN`` collections.  The name
    ``NOT_UPSIDE_DOWN`` reads more clearly than ``Notupdown`` while still being
    backwards compatible through the :meth:`allowed` helper.
    """

    RT_WHD = 0
    RT_HWD = 1
    RT_HDW = 2
    RT_DHW = 3
    RT_DWH = 4
    RT_WDH = 5

    #: Every possible rotation of an item.
    ALL: ClassVar[List["RotationType"]]

    #: Rotations that keep the item upright.
    NOT_UPSIDE_DOWN: ClassVar[List["RotationType"]]

    @classmethod
    def allowed(cls, can_be_upside_down: bool) -> List["RotationType"]:
        """Return the orientations that an item is allowed to use."""

        return cls.ALL if can_be_upside_down else cls.NOT_UPSIDE_DOWN


RotationType.ALL = [
    RotationType.RT_WHD,
    RotationType.RT_HWD,
    RotationType.RT_HDW,
    RotationType.RT_DHW,
    RotationType.RT_DWH,
    RotationType.RT_WDH,
]
RotationType.NOT_UPSIDE_DOWN = [
    RotationType.RT_WHD,
    RotationType.RT_HWD,
]


class Axis(IntEnum):
    """Axis indices used to address width, height and depth.

    ``Axis`` objects can be compared with integers so existing code keeps
    working while new code can benefit from the more descriptive constant
    names.
    """

    WIDTH = 0
    HEIGHT = 1
    DEPTH = 2

    #: Helper collection mirroring the original constant.
    ALL: ClassVar[List["Axis"]]


Axis.ALL = [Axis.WIDTH, Axis.HEIGHT, Axis.DEPTH]


