# Adding multi-tile-layer support to level.py

These changes allow the level loader to read and render all tile layers from a
Tiled `.tmj` file instead of only the single layer named `"ground"`.
Layers are drawn in the order they appear in Tiled, so layers placed above
`"ground"` in the Tiled layer panel render in front of it.
Transparency works automatically because tileset images are already loaded with
`convert_alpha()`.

The `"ground"` layer still drives all collision/gameplay logic (solid, hazard,
ladder). Every other tile layer is visual only.

---

## Step 1 — add `tile_layers` field in `__init__`

Find the block that initialises Tiled tileset support (around line 100) and add
one new field after `tile_properties_by_gid`:

```python
# before
self.tilesets: list[dict[str, Any]] = []
self.default_tiles: list[pygame.Surface] = []
self.tile_properties_by_gid: dict[int, dict[str, Any]] = {}

# after
self.tilesets: list[dict[str, Any]] = []
self.default_tiles: list[pygame.Surface] = []
self.tile_properties_by_gid: dict[int, dict[str, Any]] = {}
self.tile_layers: list[list[list[int]]] = []
```

---

## Step 2 — clear `tile_layers` in `reset_runtime_state`

```python
# before
def reset_runtime_state(self) -> None:
    self.solid_rects.clear()
    self.hazard_tiles.clear()
    self.ladder_rects.clear()
    self.enemies.empty()
    ...

# after
def reset_runtime_state(self) -> None:
    self.solid_rects.clear()
    self.hazard_tiles.clear()
    self.ladder_rects.clear()
    self.tile_layers.clear()
    self.enemies.empty()
    ...
```

---

## Step 3 — collect all tile layers in `load_tiled_map`

Replace the section that looks for the ground layer only:

```python
# before
ground_layer = None
object_layers: list[dict[str, Any]] = []

for layer in data.get("layers", []):
    layer_type = layer.get("type")
    layer_name = layer.get("name", "")

    if layer_type == "tilelayer" and layer_name == "ground":
        ground_layer = layer
    elif layer_type == "objectgroup":
        object_layers.append(layer)

if ground_layer is None:
    raise ValueError("Tiled map is missing a tile layer named 'ground'.")

self.grid = self.decode_tile_layer_data(ground_layer)
self.build_property_regions_from_ground()
self.load_object_layers(object_layers)
```

```python
# after
ground_layer = None
raw_tile_layers: list[dict[str, Any]] = []
object_layers: list[dict[str, Any]] = []

for layer in data.get("layers", []):
    layer_type = layer.get("type")
    layer_name = layer.get("name", "")

    if layer_type == "tilelayer":
        raw_tile_layers.append(layer)
        if layer_name == "ground":
            ground_layer = layer
    elif layer_type == "objectgroup":
        object_layers.append(layer)

if ground_layer is None:
    raise ValueError("Tiled map is missing a tile layer named 'ground'.")

self.grid = self.decode_tile_layer_data(ground_layer)
self.tile_layers = [self.decode_tile_layer_data(l) for l in raw_tile_layers]
self.build_property_regions_from_ground()
self.load_object_layers(object_layers)
```

Key point: every tile layer is decoded and stored in `self.tile_layers` in Tiled
order. `self.grid` is still set to the ground layer for collision use.

---

## Step 4 — keep the legacy CSV path working

At the very end of `load_csv`, after the loop that processes all tiles, add:

```python
self.tile_layers = [self.grid]
```

This means the draw method works the same way for CSV levels without any
special-casing.

---

## Step 5 — draw all tile layers in `draw()`

Replace the loop that iterates `self.grid`:

```python
# before
for gy in range(self.height):
    for gx in range(self.width):
        gid = self.grid[gy][gx]
        img = None

        if self.tilesets:
            img = self.get_tile_image(gid)
        else:
            if gid in self.legacy_draw_ids:
                img = self.get_tile_image(gid)

        if img is None:
            continue

        x = gx * settings.TILE_SIZE - camera_x
        y = gy * settings.TILE_SIZE - camera_y
        surface.blit(img, (x, y))
```

```python
# after
for grid in self.tile_layers:
    for gy in range(self.height):
        for gx in range(self.width):
            gid = grid[gy][gx]
            img = None

            if self.tilesets:
                img = self.get_tile_image(gid)
            else:
                if gid in self.legacy_draw_ids:
                    img = self.get_tile_image(gid)

            if img is None:
                continue

            x = gx * settings.TILE_SIZE - camera_x
            y = gy * settings.TILE_SIZE - camera_y
            surface.blit(img, (x, y))
```

The only change is the outer `for grid in self.tile_layers:` loop wrapping the
existing per-tile logic.
