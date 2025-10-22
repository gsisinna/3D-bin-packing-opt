from __future__ import annotations

from api import pack_from_json


def test_pack_from_json_returns_expected_structure():
    payload = {
        "box": [
            {
                "name": "bin",
                "WHD": [120, 100, 80],
                "weight": 200,
                "corner": 0,
                "openTop": 1,
            }
        ],
        "item": [
            {
                "name": "crate",
                "WHD": [40, 40, 40],
                "count": 1,
                "updown": 1,
                "type": 1,
                "level": 1,
                "loadbear": 100,
                "weight": 10,
                "color": "#FFAA00",
            }
        ],
    }

    result = pack_from_json(payload)

    assert result["bins"], "Bins should not be empty"
    bin_entry = result["bins"][0]
    assert bin_entry["items"], "Items should be present"
    assert bin_entry["items"][0]["part_number"] == "crate-1"
