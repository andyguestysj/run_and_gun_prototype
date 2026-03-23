Updated levels folder for the Tiled multi-tileset level loader.

Files:
* level1.tmj - converted version of the current example level using Tiled JSON
* level1_tileset.tsx - external tileset definition pointing to ../images/tileset.png
* level_template.tmj - blank starter map with the required layers
* level1.csv - legacy CSV kept for reference/backwards compatibility
* level1bg1.png / level1bg2.png / level1bg3.png - parallax backgrounds

Required Tiled layer names:
* ground
* collision
* objects

Use point objects named:
* player
* enemy_runner
* enemy_shooter
* boss
* health
* ammo
* shield
* exit
