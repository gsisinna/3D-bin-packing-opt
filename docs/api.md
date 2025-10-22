# API reference

This document describes the JSON interface consumed by :mod:`api.py` and the
corresponding response format.  The command line tool replaces the legacy Flask
service that previously shipped with the project while keeping the data model
compatible with existing clients.

## Request format

```json
{
  "box": [
    {
      "name": "Example Bin",
      "WHD": [589, 243, 259],
      "weight": 28080,
      "corner": 15,
      "openTop": 1
    }
  ],
  "item": [
    {
      "name": "Crate",
      "WHD": [60, 60, 60],
      "count": 5,
      "updown": 1,
      "type": 1,
      "level": 1,
      "loadbear": 120,
      "weight": 20,
      "color": "#FFAA00"
    }
  ],
  "binding": [["Crate", "Other"]]
}
```

### Fields

* ``box`` – list of containers.  Each entry contains the bin name, dimensions
  (WHD), maximum supported weight, the optional size of corner reinforcements
  and whether the container is loaded from the top (``openTop`` equals ``2``)
  or from the side (``openTop`` equals ``1``).
* ``item`` – list of items to pack.  ``type`` distinguishes cubes (``1``) from
  cylinders (``2``).  ``updown`` should be set to ``0`` for items that cannot be
  flipped upside down.  The ``count`` field is expanded automatically by the CLI
  utility so a single item definition can represent many identical objects.
* ``binding`` – optional binding rules.  Items listed in the same tuple must be
  present in equal numbers inside a bin.  If the requirement cannot be
  satisfied the associated items are reported as unfit.

## Response format

The CLI prints a JSON document containing a list of processed bins and a list of
globally unfit items:

```json
{
  "bins": [
    {
      "part_number": "Example Bin",
      "dimensions": [589.0, 243.0, 259.0],
      "max_weight": 28080.0,
      "gravity": [23.4, 23.4, 26.6, 26.6],
      "items": [
        {
          "part_number": "Crate-1",
          "name": "Crate",
          "type": "cube",
          "color": "#FFAA00",
          "position": [0.0, 0.0, 0.0],
          "rotation_type": 0,
          "dimensions": [60.0, 60.0, 60.0],
          "weight": 20.0
        }
      ],
      "unfitted_items": []
    }
  ],
  "unfit_items": []
}
```

Each entry in ``items`` contains the item's placement, rotation and resulting
dimensions.  ``gravity`` reports the percentage of the payload located in each
quadrant of the bin which is helpful for analysing balance.

