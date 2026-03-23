# Tiled Level Editor Guide (Updated)

## Overview

This project now uses **Tiled JSON maps (`.tmj`)** for level creation.

Each level can:

* use its own tileset(s)
* mix multiple tilesets
* define gameplay using object layers
* separate visuals and collision cleanly

This replaces the older CSV-only system (which is still supported for legacy maps).

---

## File Structure

Levels are stored in:

```
assets/levels/
```

Each level should follow this naming:

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

### 1. New Map Settings

* Orientation: **Orthogonal**
* Tile size: **16 × 16**
* Map size: your choice (e.g. 100 × 20)
* Tile layer format: **CSV (internal)**

---

### 2. Add a Tileset

In Tiled:

1. **Map → New Tileset**
2. Select image:

   ```
   assets/images/tileset.png
   ```
3. Settings:

   * Tile size: **16 × 16**
   * Margin: **0**
   * Spacing: **0**

You can also:

* create your own tileset
* use multiple tilesets in one level

---

## Required Layers

### Tile Layers

| Layer Name  | Purpose                             |
| ----------- | ----------------------------------- |
| `ground`    | Visual tiles (what the player sees) |
| `collision` | Solid tiles (for physics)           |

---

### Object Layer

| Layer Name | Purpose                        |
| ---------- | ------------------------------ |
| `objects`  | Player, enemies, pickups, exit |

---

## Placing Objects

Use **Insert → Insert Tile / Point Object**

Name objects exactly as follows:

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

### Level Exit

```
exit
```

---

## Object Placement Rules

* Place objects where their **feet touch the ground**
* The game adjusts positioning automatically
* Use **point objects** (simplest and recommended)

---

## Collision Layer Rules

* Any tile placed in the `collision` layer = **solid**
* Empty tiles = **non-solid**
* The actual tile graphic does not matter

---

## Tilesets (Important)

This version of the game:

✔ supports **multiple tilesets per level**
✔ supports **different tilesets for different levels**
✔ supports **external `.tsx` tilesets**

### How it works

Tiled assigns each tileset a `firstgid`.

The game automatically:

* detects which tileset a tile belongs to
* selects the correct image
* draws it correctly

---

## Exporting the Map

Save your map as:

```
assets/levels/level_name.tmj
```

Do NOT export as CSV.

---

## Background Layers

Backgrounds are still handled separately.

Name them like:

```
level1bg1.png
level1bg2.png
level1bg3.png
```

These create the parallax effect.

---

## Common Mistakes

### ❌ Wrong layer names

Must match exactly:

```
ground
collision
objects
```

---

### ❌ Wrong object names

Names are case-sensitive and must match exactly.

---

### ❌ Using CSV export

The game expects `.tmj` (JSON), not CSV.

---

### ❌ Tileset path issues

If using external `.tsx`:

* keep relative paths valid
* usually safest to keep tilesets in `assets/images`

---

## Limitations (Current Version)

* Tile flipping/rotation from Tiled is ignored
* Animated tiles from Tiled are not yet supported

---

## Recommended Student Workflow

1. Open template map
2. Paint level in `ground`
3. Paint collision in `collision`
4. Add objects in `objects`
5. Save as `.tmj`
6. Run the game

---

## Extension Ideas (for students)

* Create your own tileset
* Mix multiple tilesets in one level
* Design different themed levels (forest, cave, sci-fi)
* Experiment with level flow and difficulty

---

## Summary

This system separates:

* **Visuals → ground layer**
* **Physics → collision layer**
* **Gameplay → object layer**

This is closer to how real games and engines structure levels.

---
