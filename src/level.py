from __future__ import annotations

import csv
import json
import os
import xml.etree.ElementTree as ET
from typing import Any

import pygame

from . import settings
from .enemies import BossEnemy, NormalEnemy, ShooterEnemy
from .pickups import create_pickup
from .utils import asset_path, load_image


class BackgroundLayer:
    def __init__(self, image: pygame.Surface, parallax_factor: float = 0.5, y_offset: int = 0):
        self.image = image
        self.parallax_factor = parallax_factor
        self.y_offset = y_offset


class Level:
    """
    Level loader with two modes:
    1) Tiled JSON (.tmj / .json) using a ground tile layer and object layers.
    2) Legacy CSV fallback for older levels.

    Tiled workflow:
    * paint visible tiles on a tile layer named: ground
    * mark behaviour using tile properties on the tileset:
        - solid  = true
        - hazard = true   (or danger = true)
        - damage = 20
        - ladder = true
    * place gameplay objects on an object layer, using names:
        player, enemy_runner, enemy_shooter, boss,
        health, ammo, shield, exit

    Notes:
    * different levels can use different tilesets
    * multiple tilesets per level are supported
    * external .tsx tilesets are supported
    * Tiled flip/rotation flags are stripped for lookup, but not visually drawn
    """

    EMPTY = 0

    # Tiled gid flip flags.
    FLIPPED_HORIZONTALLY_FLAG = 0x80000000
    FLIPPED_VERTICALLY_FLAG = 0x40000000
    FLIPPED_DIAGONALLY_FLAG = 0x20000000
    ALL_FLIP_FLAGS = (
        FLIPPED_HORIZONTALLY_FLAG
        | FLIPPED_VERTICALLY_FLAG
        | FLIPPED_DIAGONALLY_FLAG
    )

    # Legacy CSV IDs kept for backwards compatibility.
    SOLID_01 = 1
    SOLID_02 = 2
    SOLID_03 = 3
    SOLID_04 = 4
    SOLID_05 = 5
    PLAYER_SPAWN = 90
    ENEMY_SPAWN = 91
    PICKUP_HEALTH = 92
    BOSS_SPAWN = 93
    EXIT_FLAG = 94
    SHOOTER_ENEMY_SPAWN = 95

    def __init__(self, level_name: str):
        self.level_name = level_name
        self.csv_name = level_name  # keep existing background naming code working

        self.background_layers: list[BackgroundLayer] = []
        self.load_backgrounds()

        # Drawing / map data
        self.grid: list[list[int]] = []
        self.width = 0
        self.height = 0
        self.pixel_width = 0
        self.pixel_height = 0

        # Collision / gameplay regions
        self.solid_rects: list[pygame.Rect] = []
        self.hazard_tiles: list[dict[str, Any]] = []
        self.ladder_rects: list[pygame.Rect] = []

        # Spawned content
        self.player_spawn = (0, 0)
        self.exit_rect: pygame.Rect | None = None
        self.enemies = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.boss: BossEnemy | None = None

        # Tiled tileset support
        self.tilesets: list[dict[str, Any]] = []
        self.default_tiles: list[pygame.Surface] = []
        self.tile_properties_by_gid: dict[int, dict[str, Any]] = {}

        # Legacy CSV support only
        self.tilesheet = load_image("tileset.png")
        self.default_tiles = self.slice_tilesheet(self.tilesheet, settings.TILE_SIZE)
        self.tile_id_to_sheet_index = {
            self.SOLID_01: 83,
            self.SOLID_02: 88,
            self.SOLID_03: 89,
            self.SOLID_04: 74,
            self.SOLID_05: 98,
        }
        self.legacy_solid_ids = {self.SOLID_01, self.SOLID_02, self.SOLID_03, self.SOLID_05}
        self.legacy_draw_ids = {self.SOLID_01, self.SOLID_02, self.SOLID_03, self.SOLID_04, self.SOLID_05}

        self.load_level(level_name)

    @staticmethod
    def slice_tilesheet(
        sheet: pygame.Surface,
        tile_size: int,
        *,
        margin: int = 0,
        spacing: int = 0,
        tile_count: int | None = None,
        columns: int | None = None,
    ) -> list[pygame.Surface]:
        """Slice a sheet into TILE_SIZE tiles, supporting Tiled margin/spacing."""
        sheet_w, sheet_h = sheet.get_size()
        tiles: list[pygame.Surface] = []

        if columns is None or columns <= 0:
            columns = max(0, (sheet_w - margin * 2 + spacing) // (tile_size + spacing))

        rows = max(0, (sheet_h - margin * 2 + spacing) // (tile_size + spacing))

        for row in range(rows):
            for col in range(columns):
                x = margin + col * (tile_size + spacing)
                y = margin + row * (tile_size + spacing)
                if x + tile_size > sheet_w or y + tile_size > sheet_h:
                    continue
                rect = pygame.Rect(x, y, tile_size, tile_size)
                tiles.append(sheet.subsurface(rect))
                if tile_count is not None and len(tiles) >= tile_count:
                    return tiles
        return tiles

    @staticmethod
    def _strip_gid_flags(gid: int) -> int:
        return gid & ~Level.ALL_FLIP_FLAGS

    @staticmethod
    def _coerce_property_value(value: Any, declared_type: str | None = None) -> Any:
        if declared_type == "bool":
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in {"1", "true", "yes", "on"}
        if declared_type == "int":
            return int(value)
        if declared_type == "float":
            return float(value)
        if declared_type == "color":
            return str(value)

        if isinstance(value, str):
            lower = value.strip().lower()
            if lower in {"true", "false"}:
                return lower == "true"
            try:
                return int(value)
            except ValueError:
                pass
            try:
                return float(value)
            except ValueError:
                pass
        return value

    @classmethod
    def _parse_tiled_properties(cls, raw_properties: list[dict[str, Any]] | None) -> dict[str, Any]:
        props: dict[str, Any] = {}
        for prop in raw_properties or []:
            name = prop.get("name")
            if not name:
                continue
            props[name] = cls._coerce_property_value(prop.get("value"), prop.get("type"))
        return props

    def load_level(self, level_name: str) -> None:
        """Try Tiled JSON first, then fall back to the older CSV format."""
        tmj_path = asset_path("levels", level_name + ".tmj")
        json_path = asset_path("levels", level_name + ".json")
        csv_path = asset_path("levels", level_name + ".csv")

        if os.path.exists(tmj_path):            
            self.load_tiled_map(tmj_path)
        elif os.path.exists(json_path):
            self.load_tiled_map(json_path)
        elif os.path.exists(csv_path):
            self.load_csv(level_name)
        else:
            raise FileNotFoundError(
                f"No level found for '{level_name}'. Expected {tmj_path}, {json_path}, or {csv_path}."
            )

    def reset_runtime_state(self) -> None:
        self.solid_rects.clear()
        self.hazard_tiles.clear()
        self.ladder_rects.clear()
        self.enemies.empty()
        self.pickups.empty()
        self.boss = None
        self.exit_rect = None
        self.player_spawn = (0, 0)

    # ------------------------------------------------------------------
    # Legacy CSV loader
    # ------------------------------------------------------------------
    def load_csv(self, csv_name: str) -> None:
        path = asset_path("levels", csv_name + ".csv")
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            self.grid = [[int(cell.strip()) for cell in row] for row in reader]

        self.height = len(self.grid)
        self.width = len(self.grid[0]) if self.height else 0
        self.pixel_width = self.width * settings.TILE_SIZE
        self.pixel_height = self.height * settings.TILE_SIZE

        self.tilesets = []
        self.tile_properties_by_gid.clear()
        self.reset_runtime_state()

        tile_size = settings.TILE_SIZE

        for gy in range(self.height):
            for gx in range(self.width):
                tile_id = self.grid[gy][gx]
                world_x = gx * tile_size
                world_y = gy * tile_size

                if tile_id in self.legacy_solid_ids:
                    self.solid_rects.append(pygame.Rect(world_x, world_y, tile_size, tile_size))
                elif tile_id == self.PLAYER_SPAWN:
                    self.player_spawn = (world_x, world_y - (32 - tile_size))
                elif tile_id == self.ENEMY_SPAWN:
                    self.enemies.add(NormalEnemy((world_x, world_y - (32 - tile_size))))
                elif tile_id == self.PICKUP_HEALTH:
                    self.pickups.add(create_pickup("health", world_x, world_y - (32 - tile_size)))
                elif tile_id == self.BOSS_SPAWN:
                    self.boss = BossEnemy((world_x, world_y - (64 - tile_size)))
                elif tile_id == self.EXIT_FLAG:
                    self.exit_rect = pygame.Rect(world_x, world_y - tile_size, tile_size, tile_size)
                elif tile_id == self.SHOOTER_ENEMY_SPAWN:
                    self.enemies.add(ShooterEnemy((world_x, world_y - (32 - tile_size))))

    # ------------------------------------------------------------------
    # Tiled JSON / TSX loader
    # ------------------------------------------------------------------
    def load_tiled_map(self, map_path: str) -> None:
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        map_dir = os.path.dirname(map_path)
        self.width = int(data["width"])
        self.height = int(data["height"])
        tile_w = int(data["tilewidth"])
        tile_h = int(data["tileheight"])

        if tile_w != settings.TILE_SIZE or tile_h != settings.TILE_SIZE:
            raise ValueError(
                f"Map tile size is {tile_w}x{tile_h}, but settings.TILE_SIZE is {settings.TILE_SIZE}."
            )

        self.pixel_width = self.width * settings.TILE_SIZE
        self.pixel_height = self.height * settings.TILE_SIZE

        self.reset_runtime_state()
        self.load_tiled_tilesets(data, map_dir)

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

    def decode_tile_layer_data(self, layer: dict[str, Any]) -> list[list[int]]:
        raw = layer.get("data")
        if raw is None:
            raise ValueError("Only finite, non-chunked Tiled layers with inline data are supported.")

        if len(raw) != self.width * self.height:
            raise ValueError("Ground layer tile count does not match map width/height.")

        grid: list[list[int]] = []
        for y in range(self.height):
            start = y * self.width
            row = [int(v) for v in raw[start:start + self.width]]
            grid.append(row)
        return grid

    def load_tiled_tilesets(self, map_data: dict[str, Any], map_dir: str) -> None:
        self.tilesets = []
        self.tile_properties_by_gid.clear()

        for ts in map_data.get("tilesets", []):
            firstgid = int(ts.get("firstgid", 1))

            if "source" in ts:
                tsx_path = os.path.normpath(os.path.join(map_dir, ts["source"]))
                tileset_info = self.load_tsx_tileset(tsx_path)
            else:
                tileset_info = self.load_embedded_tileset(ts, map_dir)

            tileset_info["firstgid"] = firstgid
            self.tilesets.append(tileset_info)

            for local_id, props in tileset_info["tile_properties"].items():
                self.tile_properties_by_gid[firstgid + local_id] = props

        self.tilesets.sort(key=lambda t: t["firstgid"])

    def load_embedded_tileset(self, ts: dict[str, Any], map_dir: str) -> dict[str, Any]:
        image_rel = ts.get("image")
        if not image_rel:
            raise ValueError("Embedded Tiled tileset is missing an image path.")

        image_path = os.path.normpath(os.path.join(map_dir, image_rel))
        sheet = pygame.image.load(image_path).convert_alpha()

        tile_w = int(ts.get("tilewidth", settings.TILE_SIZE))
        tile_h = int(ts.get("tileheight", settings.TILE_SIZE))
        if tile_w != settings.TILE_SIZE or tile_h != settings.TILE_SIZE:
            raise ValueError("Tileset tile size must match settings.TILE_SIZE.")

        margin = int(ts.get("margin", 0))
        spacing = int(ts.get("spacing", 0))
        tilecount = int(ts.get("tilecount", 0)) or None
        columns = int(ts.get("columns", 0)) or None

        tiles = self.slice_tilesheet(
            sheet,
            settings.TILE_SIZE,
            margin=margin,
            spacing=spacing,
            tile_count=tilecount,
            columns=columns,
        )

        return {
            "image_path": image_path,
            "tiles": tiles,
            "tile_properties": {
                int(tile.get("id", 0)): self._parse_tiled_properties(tile.get("properties"))
                for tile in ts.get("tiles", [])
            },
        }

    def load_tsx_tileset(self, tsx_path: str) -> dict[str, Any]:
        root = ET.parse(tsx_path).getroot()
        tsx_dir = os.path.dirname(tsx_path)

        tile_w = int(root.attrib.get("tilewidth", settings.TILE_SIZE))
        tile_h = int(root.attrib.get("tileheight", settings.TILE_SIZE))
        if tile_w != settings.TILE_SIZE or tile_h != settings.TILE_SIZE:
            raise ValueError("TSX tile size must match settings.TILE_SIZE.")

        margin = int(root.attrib.get("margin", 0))
        spacing = int(root.attrib.get("spacing", 0))
        tilecount = int(root.attrib.get("tilecount", 0)) or None
        columns = int(root.attrib.get("columns", 0)) or None

        image_node = root.find("image")
        if image_node is None or "source" not in image_node.attrib:
            raise ValueError(f"TSX tileset '{tsx_path}' is missing an image source.")

        image_path = os.path.normpath(os.path.join(tsx_dir, image_node.attrib["source"]))
        sheet = pygame.image.load(image_path).convert_alpha()
        tiles = self.slice_tilesheet(
            sheet,
            settings.TILE_SIZE,
            margin=margin,
            spacing=spacing,
            tile_count=tilecount,
            columns=columns,
        )

        tile_properties: dict[int, dict[str, Any]] = {}
        for tile_node in root.findall("tile"):
            local_id = int(tile_node.attrib.get("id", 0))
            prop_node = tile_node.find("properties")
            props: dict[str, Any] = {}
            if prop_node is not None:
                for p in prop_node.findall("property"):
                    name = p.attrib.get("name")
                    if not name:
                        continue
                    props[name] = self._coerce_property_value(
                        p.attrib.get("value", p.text),
                        p.attrib.get("type"),
                    )
            tile_properties[local_id] = props

        return {
            "image_path": image_path,
            "tiles": tiles,
            "tile_properties": tile_properties,
        }

    def build_property_regions_from_ground(self) -> None:
        tile_size = settings.TILE_SIZE

        for gy in range(self.height):
            for gx in range(self.width):
                raw_gid = self.grid[gy][gx]
                gid = self._strip_gid_flags(raw_gid)
                if gid == 0:
                    continue

                props = self.get_tile_properties(gid)
                rect = pygame.Rect(gx * tile_size, gy * tile_size, tile_size, tile_size)

                if props.get("solid", False):
                    self.solid_rects.append(rect)                    

                if props.get("hazard", False) or props.get("danger", False):
                    damage = int(props.get("damage", 10))
                    self.hazard_tiles.append({"rect": rect, "damage": damage})

                if props.get("ladder", False):
                    self.ladder_rects.append(rect)

    def load_object_layers(self, object_layers: list[dict[str, Any]]) -> None:
        for layer in object_layers:
            for obj in layer.get("objects", []):
                name = str(obj.get("name", "")).strip().lower()
                x = int(obj.get("x", 0))
                y = int(obj.get("y", 0))

                if not name:
                    continue

                if name == "player":
                    self.player_spawn = (x, y - 32)
                elif name == "enemy_runner":
                    self.enemies.add(NormalEnemy((x, y - 32)))
                elif name == "enemy_shooter":
                    self.enemies.add(ShooterEnemy((x, y - 32)))
                elif name == "boss":
                    self.boss = BossEnemy((x, y - 64))
                elif name in {"health", "ammo", "shield"}:
                    self.pickups.add(create_pickup(name, x, y - 32))
                elif name == "exit":
                    width = int(obj.get("width", settings.TILE_SIZE)) or settings.TILE_SIZE
                    height = int(obj.get("height", settings.TILE_SIZE)) or settings.TILE_SIZE
                    if width == 0:
                        width = settings.TILE_SIZE
                    if height == 0:
                        height = settings.TILE_SIZE
                    self.exit_rect = pygame.Rect(x, y - height, width, height)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def get_tile_properties(self, gid: int) -> dict[str, Any]:
        return self.tile_properties_by_gid.get(self._strip_gid_flags(gid), {})

    def get_tile_image(self, gid: int) -> pygame.Surface | None:
        gid = self._strip_gid_flags(gid)
        if gid == 0:
            return None

        if self.tilesets:
            chosen: dict[str, Any] | None = None
            for ts in self.tilesets:
                if gid >= ts["firstgid"]:
                    chosen = ts
                else:
                    break
            if chosen is None:
                return None
            local_index = gid - chosen["firstgid"]
            tiles = chosen["tiles"]
            if 0 <= local_index < len(tiles):
                return tiles[local_index]
            return None

        # Legacy CSV drawing path.
        sheet_index = self.tile_id_to_sheet_index.get(gid)
        if sheet_index is None:
            return None
        if 0 <= sheet_index < len(self.default_tiles):
            return self.default_tiles[sheet_index]
        return None

    def get_solid_hits(self, rect: pygame.Rect) -> list[pygame.Rect]:
        return [r for r in self.solid_rects if r.colliderect(rect)]

    def rect_collides_solid(self, rect: pygame.Rect) -> bool:
        return any(r.colliderect(rect) for r in self.solid_rects)

    def rect_overlaps_ladder(self, rect: pygame.Rect) -> bool:
        return any(ladder_rect.colliderect(rect) for ladder_rect in self.ladder_rects)

    def get_hazard_hits(self, rect: pygame.Rect) -> list[dict[str, Any]]:
        return [h for h in self.hazard_tiles if h["rect"].colliderect(rect)]


    # ------------------------------------------------------------------
    # Update / draw
    # ------------------------------------------------------------------
    def update(self, dt: float, player, bullets, boss_bullets, enemy_bullets) -> None:
        for e in list(self.enemies):
            if hasattr(e, "weapon"):
                e.update(dt, self, player, enemy_bullets)
            else:
                e.update(dt, self, player)

        if self.boss and self.boss.alive():
            self.boss.update(dt, self, player, boss_bullets)

        for p in list(self.pickups):
            p.update(dt)

        for b in list(bullets):
            hit_enemy = pygame.sprite.spritecollideany(b, self.enemies)
            if hit_enemy:
                hit_enemy.take_damage(15)
                b.kill()
                continue

            if self.boss and self.boss.alive() and b.rect.colliderect(self.boss.rect):
                self.boss.take_damage(12)
                b.kill()

    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float) -> None:
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        self.draw_backgrounds(surface, camera_x, screen_width, screen_height)

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

        if self.exit_rect:
            pygame.draw.rect(
                surface,
                (80, 240, 180),
                (self.exit_rect.x - camera_x, self.exit_rect.y - camera_y, self.exit_rect.w, self.exit_rect.h),
                2,
            )


    def draw_debug_overlay(self, surface: pygame.Surface, camera_x: float, camera_y: float) -> None:
        viewport = pygame.Rect(0, 0, surface.get_width(), surface.get_height())

        for rect in self.solid_rects:
            screen_rect = rect.move(-int(camera_x), -int(camera_y))
            if screen_rect.colliderect(viewport):
                pygame.draw.rect(surface, (0, 255, 0), screen_rect, 1)

        for hazard in self.hazard_tiles:
            screen_rect = hazard["rect"].move(-int(camera_x), -int(camera_y))
            if screen_rect.colliderect(viewport):
                pygame.draw.rect(surface, (255, 0, 0), screen_rect, 1)

        for rect in self.ladder_rects:
            screen_rect = rect.move(-int(camera_x), -int(camera_y))
            if screen_rect.colliderect(viewport):
                pygame.draw.rect(surface, (80, 160, 255), screen_rect, 1)

    # ------------------------------------------------------------------
    # Backgrounds
    # ------------------------------------------------------------------
    def load_background_layer(self, image_path: str, parallax_factor: float = 0.5, y_offset: int = 0, scale=None) -> None:
        image = pygame.image.load(image_path).convert_alpha()
        if scale is not None:
            image = pygame.transform.scale(image, scale)
        self.background_layers.append(BackgroundLayer(image, parallax_factor, y_offset))

    def draw_backgrounds(self, screen: pygame.Surface, camera_x: float, screen_width: int, screen_height: int) -> None:
        _ = screen_height  # kept for compatibility / future use
        for layer in self.background_layers:
            image = layer.image
            image_width = image.get_width()
            x = camera_x * layer.parallax_factor
            start_x = int(x) % image_width
            draw_x = -start_x

            while draw_x < screen_width:
                screen.blit(image, (draw_x, layer.y_offset))
                draw_x += image_width

    def load_backgrounds(self) -> None:
        layers = [
            (self.csv_name + "bg1.png", 0.1),
            (self.csv_name + "bg2.png", 0.3),
            (self.csv_name + "bg3.png", 0.5),
        ]

        for filename, parallax in layers:
            path = asset_path("levels", filename)
            if not os.path.exists(path):
                print("Missing background:", path)
                continue
            image = pygame.image.load(path).convert_alpha()
            self.background_layers.append(BackgroundLayer(image, parallax, 0))
