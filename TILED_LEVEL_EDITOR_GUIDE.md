# Tiled Level Editor Guide (Property-Driven Version)

## Overview

This project now uses **Tiled JSON maps (`.tmj`)** with a **property-driven level system**.

Levels are defined using:

* **tile properties** (for terrain behaviour)
* **object layer** (for gameplay entities)

❌ There is **no collision layer anymore**

---

## File Structure

Levels are stored in:

```
assets/levels/
```

Example:

```
level1.tmj
level1bg1.png
level1bg2.png
level1bg3.png
```

Tilesets are stored in:

```
assets/images/
```

---

## Creating a New Map in Tiled

### Map Settings

* Orientation: **Orthogonal**
* Tile size: **16 × 16**
* Map size: your choice
* Tile layer format: **CSV (internal)**

---

## Adding a Tileset

1. **Map → New Tileset**
2. Select:

   ```
   assets/images/tileset.png
   ```
3. Settings:

   * Tile size: **16 × 16**
   * Margin: **0**
   * Spacing: **0**

✔ You can use multiple tilesets
✔ You can create your own tilesets

---

## Required Layers

### Tile Layer

| Layer Name | Purpose                              |
| ---------- | ------------------------------------ |
| `ground`   | Visuals + collision + tile behaviour |

---

### Object Layer

| Layer Name | Purpose                        |
| ---------- | ------------------------------ |
| `objects`  | Player, enemies, pickups, exit |

---

## Tile Properties (Core System)

Instead of a collision layer, tiles define behaviour.

### Solid Tiles (collision)

```
solid = true
```

Used for:

* ground
* platforms
* walls

---

### Hazard Tiles (damage)

```
hazard = true
damage = 20
```

OR:

```
danger = true
damage = 20
```

Used for:

* spikes
* lava
* traps

---

### Ladder Tiles (climbing)

```
ladder = true
```

Used for:

* ladders
* climbable ropes

---

## How to Add Tile Properties in Tiled

1. Open **Tilesets panel**
2. Click your tileset
3. Click a tile
4. Open **Properties panel**
5. Click **+**
6. Add property:

Example:

```
Name: solid
Type: bool
Value: true
```

---

## Object Layer Setup

Create a layer:

```
objects
```

Use **point objects** and name them exactly:

### Player

```
player
```

### Enemies

```
enemy_runner
enemy_shooter
boss
```

### Pickups

```
health
ammo
shield
```

### Exit

```
exit
```

---

## Object Placement Rules

* Place objects where their **feet touch the ground**
* Use **point objects**
* Names are **case-sensitive**

---

## Background Layers

Backgrounds are separate images:

```
level1bg1.png
level1bg2.png
level1bg3.png
```

These create parallax scrolling.

---

## Recommended Workflow

1. Paint terrain in `ground`
2. Ensure correct tile properties:

   * ground → `solid=true`
   * spikes → `hazard=true`
   * ladder → `ladder=true`
3. Place entities in `objects`
4. Save as `.tmj`
5. Run the game

---

## Common Mistakes

### ❌ Player falls through ground

Cause:

```
solid property missing
```

Fix:

```
solid = true
```

---

### ❌ Hazards do nothing

Cause:

```
hazard property missing or misspelled
```

---

### ❌ Ladder does not work

Cause:

```
ladder property missing
```

---

### ❌ Wrong layer names

Must be exactly:

```
ground
objects
```

---

### ❌ Adding properties to wrong thing

Make sure:

* you select a **tile in the tileset**
* NOT the map or layer

---

## Debug Tip

If something is not working:

* check tile properties spelling
* check tile is actually used in map
* check `.tmj` file contains properties

---

## Example Tile Setup

| Tile   | Properties                     |
| ------ | ------------------------------ |
| Grass  | `solid = true`                 |
| Stone  | `solid = true`                 |
| Spikes | `hazard = true`, `damage = 20` |
| Ladder | `ladder = true`                |

---

## Teaching Benefits

This system demonstrates:

* data-driven design
* separation of content and code
* reusable game systems
* professional level design workflows

---

## Extension Ideas

Students can extend this system with:

* `slippery = true` (ice physics)
* `bounce = 20` (jump pads)
* `slow = true` (water)
* custom mechanics

---

## Summary

The level system now uses:

* **ground layer → everything tile-based**
* **object layer → gameplay entities**
* **tile properties → behaviour**

This is a clean, flexible, and industry-relevant workflow.

---
