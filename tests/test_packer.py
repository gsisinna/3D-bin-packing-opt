from __future__ import annotations

from py3dbp import Bin, Item, Packer


def _build_basic_packer() -> Packer:
    packer = Packer()
    packer.add_bin(Bin(partno="bin", WHD=(120, 100, 80), max_weight=200))
    packer.add_item(
        Item(
            partno="crate-1",
            name="crate",
            typeof="cube",
            WHD=(40, 40, 40),
            weight=10,
            level=1,
            loadbear=100,
            updown=True,
            color="#FFAA00",
        )
    )
    packer.add_item(
        Item(
            partno="crate-2",
            name="crate",
            typeof="cube",
            WHD=(40, 40, 40),
            weight=10,
            level=1,
            loadbear=100,
            updown=True,
            color="#FFAA00",
        )
    )
    return packer


def test_pack_items_places_cargo():
    packer = _build_basic_packer()
    packer.pack_items()

    assert len(packer.bins[0].items) == 2
    assert not packer.bins[0].unfitted_items


def test_pack_items_respects_weight_limit():
    packer = Packer()
    packer.add_bin(Bin(partno="bin", WHD=(40, 40, 40), max_weight=15))
    packer.add_item(
        Item(
            partno="heavy",
            name="heavy",
            typeof="cube",
            WHD=(40, 40, 40),
            weight=20,
            level=1,
            loadbear=100,
            updown=True,
            color="#FF0000",
        )
    )

    packer.pack_items()

    assert not packer.bins[0].items
    assert packer.bins[0].unfitted_items
