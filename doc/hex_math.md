# Hex math notes

## Scope

These notes explain coordinate systems for the combat battlefield. The public
Python API should stay simple and use `HexCoord(column: int, row: int)`. Axial
or cube coordinates are internal math tools for future distance, movement range,
spell area-of-effect rings, line-of-sight, and pathfinding logic.

## Battlefield shape

The default battlefield uses flat-top hexes in 11 zero-based rows:

```text
row 0  - 12 hexes
row 1  - 13 hexes
row 2  - 12 hexes
row 3  - 13 hexes
row 4  - 12 hexes
row 5  - 13 hexes
row 6  - 12 hexes
row 7  - 13 hexes
row 8  - 12 hexes
row 9  - 13 hexes
row 10 - 12 hexes
```

Total valid coordinates: 137.

## Offset coordinates

Offset coordinates are the public coordinate model:

```python
HexCoord(column=4, row=2)
```

They match how the battlefield is drawn and discussed: a row number plus a
column number. They also make ragged-row validation direct because each row has
an explicit length.

Offset coordinates are less convenient for advanced hex math because neighbor
and range calculations depend on whether the row is shifted.

## Axial coordinates

Axial coordinates use two values, usually named `q` and `r`:

```python
AxialCoord(q=4, r=2)
```

They are still 2D coordinates, but the axes are aligned to the hex grid instead
of a rectangular row-column layout. Axial coordinates are often enough for
distance, neighbor, ring, and range calculations.

Use axial coordinates as an internal helper when offset-coordinate formulas
start becoming hard to verify.

## Cube coordinates

Cube coordinates use three values, usually named `x`, `y`, and `z`:

```python
CubeCoord(x=2, y=-5, z=3)
```

The battlefield is still 2D. The `z` value is not height or depth. It is a
mathematical helper axis. Valid cube coordinates always satisfy:

```text
x + y + z = 0
```

Because of that constraint, only two values are independent. If `x` and `y` are
known, `z` can always be derived:

```python
z = -x - y
```

Cube coordinates are useful because many hex-grid algorithms become simpler and
less error-prone. For example, distance between two cube coordinates can be
calculated with:

```python
distance = max(abs(dx), abs(dy), abs(dz))
```

or equivalently:

```python
distance = (abs(dx) + abs(dy) + abs(dz)) // 2
```

Cube coordinates should remain private implementation detail unless a future API
has a strong reason to expose them.

## Recommended approach

Use `HexCoord(column, row)` at domain boundaries and in tests that describe game
behavior. Add conversion helpers to axial or cube coordinates only when a feature
needs hex math that would be awkward in offset coordinates.

Likely future triggers for conversion helpers:

* distance between two hexes
* movement radius from a unit speed value
* spell area-of-effect rings
* line-of-sight
* pathfinding
