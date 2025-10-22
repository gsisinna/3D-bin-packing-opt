"""Command line interface for the 3D bin packing library.

The original repository exposed a partially implemented Flask application that
did not run.  The refactored project replaces it with a small but fully tested
command line utility that can be used to pack items described in JSON files.

Example usage::

    $ python api.py examples/basic_request.json

The script prints a JSON document containing the packing result.  The format of
the input request is documented in :mod:`docs/api.md` and mirrors the structure
returned by the previous Flask service.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from py3dbp import Bin, Item, Packer


def _load_request(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf8") as handle:
        return json.load(handle)


def _build_packer(data: Dict[str, Any]) -> Tuple[Packer, List[Tuple[str, ...]]]:
    packer = Packer()

    for entry in data.get("box", []):
        packer.add_bin(
            Bin(
                partno=entry["name"],
                WHD=tuple(entry["WHD"]),
                max_weight=entry["weight"],
                corner=entry.get("corner", 0),
                put_type=entry.get("openTop", 1),
            )
        )

    for entry in data.get("item", []):
        for index in range(entry.get("count", 1)):
            packer.add_item(
                Item(
                    partno=f"{entry['name']}-{index + 1}",
                    name=entry["name"],
                    typeof="cylinder" if entry.get("type") == 2 else "cube",
                    WHD=tuple(entry["WHD"]),
                    weight=entry["weight"],
                    level=entry.get("level", 1),
                    loadbear=entry.get("loadbear", 0),
                    updown=bool(entry.get("updown", True)),
                    color=entry.get("color", "#CCCCCC"),
                )
            )

    bindings = [tuple(binding) for binding in data.get("binding", [])]
    return packer, bindings


def pack_from_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Pack the request described by ``data`` and return a serialisable result."""

    packer, bindings = _build_packer(data)
    packer.pack_items(binding=bindings)

    response: Dict[str, Any] = {"bins": [], "unfit_items": []}
    for bin in packer:
        response["bins"].append(
            {
                "part_number": bin.partno,
                "dimensions": [float(bin.width), float(bin.height), float(bin.depth)],
                "max_weight": float(bin.max_weight),
                "gravity": bin.gravity,
                "items": [
                    {
                        "part_number": item.partno,
                        "name": item.name,
                        "type": item.typeof,
                        "color": item.color,
                        "position": [float(value) for value in item.position],
                        "rotation_type": int(item.rotation_type),
                        "dimensions": [float(value) for value in item.get_dimension()],
                        "weight": float(item.weight),
                    }
                    for item in bin.items
                ],
                "unfitted_items": [item.partno for item in bin.unfitted_items],
            }
        )

    response["unfit_items"] = [item.partno for item in packer.unfit_items]
    return response


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="Path to a JSON request")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to save the resulting JSON (defaults to stdout)",
    )
    args = parser.parse_args(argv)

    data = _load_request(args.request)
    result = pack_from_json(data)

    if args.output:
        with args.output.open("w", encoding="utf8") as handle:
            json.dump(result, handle, indent=2)
    else:
        print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

