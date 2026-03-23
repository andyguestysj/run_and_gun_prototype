# TILED LEVEL SYSTEM (UPDATED - PROPERTY DRIVEN)

This project uses Tiled JSON maps (.tmj) with a property-driven level system.

## IMPORTANT:

Collision, hazards, and ladders are defined using TILE PROPERTIES.

## FOLDER STRUCTURE

Place level files in:

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

## REQUIRED LAYERS IN TILED

1. Tile Layer:
   Name: ground

   This layer handles:

   * visual tiles
   * collision (via properties)
   * hazards
   * ladders

2. Object Layer:
   Name: objects

   This layer handles:

   * player spawn
   * enemies
   * pickups
   * exit

## TILE PROPERTIES (VERY IMPORTANT)

Tiles define behaviour using properties.

Add properties in the TILESET (not the map).

SOLID (collision):
solid = true

HAZARD (damage):
hazard = true
damage = 20

```
OR:
danger = true
damage = 20
```

LADDER (climbing):
ladder = true

## HOW TO ADD TILE PROPERTIES IN TILED

1. Open the Tilesets panel
2. Click the tileset (e.g. tileset.png)
3. Click a tile
4. Open the Properties panel
5. Click "+"
6. Add property:

   Name: solid
   Type: bool
   Value: true

IMPORTANT:
You must select a TILE (not a layer or the map).

## OBJECT NAMES (CASE-SENSITIVE)

Use point objects in the "objects" layer.

Player:
player

Enemies:
enemy_runner
enemy_shooter
boss

Pickups:
health
ammo
shield

Exit:
exit

## OBJECT PLACEMENT

Place objects where their FEET touch the ground.

Use point objects (simplest).

## BACKGROUND IMAGES

Backgrounds are loaded automatically if named:

```
level1bg1.png
level1bg2.png
level1bg3.png
```

These create a parallax effect.

## COMMON PROBLEMS

Player falls through ground:
-> solid = true is missing

Hazards do nothing:
-> hazard/danger property missing or misspelled

Ladder does not work:
-> ladder = true missing

"Add Property" is greyed out:
-> you are not selecting a tile in the tileset

Wrong layer names:
-> must be exactly:
ground
objects

## RECOMMENDED WORKFLOW

1. Paint terrain in "ground"
2. Ensure tiles have correct properties:
   ground -> solid = true
   spikes -> hazard = true
   ladder -> ladder = true
3. Place objects in "objects"
4. Save as .tmj
5. Run the game

## NOTES

* Multiple tilesets are supported
* Different levels can use different tilesets
* External .tsx tilesets are supported
* Tile flipping/rotation is ignored by the game
* CSV maps are still supported but deprecated

## SUMMARY

ground layer = visuals + behaviour
objects layer = gameplay entities
tile properties = collision, hazards, ladders

This is a data-driven system similar to real game engines.
