from __future__ import annotations

import csv
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import pygame

from . import settings
from .enemies import BossEnemy, NormalEnemy, ShooterEnemy
from .pickups import create_pickup
from .utils import asset_path


# Tiled stores flip flags inside the gid value.
_FLIP_MASK = 0xE0000000
_GID_MASK = 0x1FFFFFFF


@dataclass
class BackgroundLayer:
    image: pygame.Surface
    parallax_factor: float = 0.5
    y_offset: int = 0


@dataclass
class LoadedTileset:
    firstgid: int
    tiles: list[pygame.Surface]


class Level:
    # Legacy CSV tile IDs
    EMPTY = 0
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
        self.csv_name = level_name  # keep old background naming working

        self.background_layers: list[BackgroundLayer] = []
        self.tilesets: list[LoadedTileset] = []
        self.grid: list[list[int]] = []
        self.solid_rects: list[pygame.Rect] = []

        self.player_spawn = (0, 0)
        self.exit_rect: pygame.Rect | None = None
        self.enemies = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.boss: BossEnemy | None = None

        self.width = 0
        self.height = 0
        self.pixel_width = 0
        self.pixel_height = 0

        # Legacy CSV support
        self.solid_ids = {self.SOLID_01, self.SOLID_02, self.SOLID_03, self.SOLID_05}
        self.draw_ids = {self.SOLID_01, self.SOLID_02, self.SOLID_03, self.SOLID_04, self.SOLID_05}
        self.tile_id_to_sheet_index = {
            self.SOLID_01: 83,
            self.SOLID_02: 88,
            self.SOLID_03: 89,
            self.SOLID_04: 74,
            self.SOLID_05: 98,
        }

        self.load_backgrounds()
        self.load_level(level_name)

    @staticmethod
    def slice_tilesheet(
        sheet: pygame.Surface,
        tile_width: int,
        tile_height: int,
        *,
        margin: int = 0,
        spacing: int = 0,
        tilecount: int | None = None,
        columns: int | None = None,
    ) -> list[pygame.Surface]:
        """Slice a tilesheet into individual tiles, including Tiled margin/spacing support."""
        sheet_w, sheet_h = sheet.get_size()
        tiles: list[pygame.Surface] = []

        if columns is None:
            usable_w = sheet_w - (margin * 2)
            columns = max(1, (usable_w + spacing) // (tile_width + spacing))

        y = margin
        while y + tile_height <= sheet_h - margin:
            x = margin
            col = 0
            while x + tile_width <= sheet_w - margin and col < columns:
                rect = pygame.Rect(x, y, tile_width, tile_height)
                tiles.append(sheet.subsurface(rect))
                if tilecount is not None and len(tiles) >= tilecount:
                    return tiles
                x += tile_width + spacing
                col += 1
            y += tile_height + spacing

        return tiles

    def load_level(self, level_name: str) -> None:
        tmj_path = asset_path("levels", level_name + ".tmj")
        json_path = asset_path("levels", level_name + ".json")
        csv_path = asset_path("levels", level_name + ".csv")

        if os.path.exists(tmj_path):
            self.load_tiled_map(tmj_path)
            return
        if os.path.exists(json_path):
            self.load_tiled_map(json_path)
            return
        if os.path.exists(csv_path):
            self.load_csv(level_name)
            return

        raise FileNotFoundError(f"No level file found for '{level_name}' (.tmj, .json, or .csv)")

    def reset_content(self) -> None:
        self.solid_rects.clear()
        self.enemies.empty()
        self.pickups.empty()
        self.boss = None
        self.exit_rect = None
        self.player_spawn = (0, 0)

    def load_csv(self, csv_name: str) -> None:
        """Legacy CSV loader kept for older maps."""
        path = asset_path("levels", csv_name + ".csv")
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            self.grid = [[int(cell.strip()) for cell in row] for row in reader]

        self.height = len(self.grid)
        self.width = len(self.grid[0]) if self.height else 0
        self.pixel_width = self.width * settings.TILE_SIZE
        self.pixel_height = self.height * settings.TILE_SIZE

        self.reset_content()

        # Legacy CSV always uses the shared tileset.png
        sheet = pygame.image.load(asset_path("images", "tileset.png")).convert_alpha()
        self.tilesets = [
            LoadedTileset(
                firstgid=1,
                tiles=self.slice_tilesheet(sheet, settings.TILE_SIZE, settings.TILE_SIZE),
            )
        ]

        tile_size = settings.TILE_SIZE
        for gy in range(self.height):
            for gx in range(self.width):
                tile_id = self.grid[gy][gx]
                world_x = gx * tile_size
                world_y = gy * tile_size

                if tile_id in self.solid_ids:
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

    def load_tiled_map(self, map_path: str) -> None:
        with open(map_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.width = int(data["width"])
        self.height = int(data["height"])
        map_tile_w = int(data["tilewidth"])
        map_tile_h = int(data["tileheight"])
        if map_tile_w != settings.TILE_SIZE or map_tile_h != settings.TILE_SIZE:
            raise ValueError(
                f"Map uses {map_tile_w}x{map_tile_h} tiles but settings.TILE_SIZE is {settings.TILE_SIZE}."
            )

        self.pixel_width = self.width * settings.TILE_SIZE
        self.pixel_height = self.height * settings.TILE_SIZE
        self.reset_content()

        self.tilesets = self._load_tilesets_from_tiled(data, map_path)
        if not self.tilesets:
            raise ValueError("Tiled map contains no supported tilesets.")

        ground_layer = None
        collision_layer = None
        object_layers = []

        for layer in data.get("layers", []):
            if layer.get("type") == "tilelayer" and layer.get("name") == "ground":
                ground_layer = layer
            elif layer.get("type") == "tilelayer" and layer.get("name") == "collision":
                collision_layer = layer
            elif layer.get("type") == "objectgroup":
                object_layers.append(layer)

        if ground_layer is None:
            raise ValueError("Tiled map is missing a 'ground' tile layer.")

        self.grid = self._decode_tile_layer(ground_layer)

        if collision_layer is not None:
            collision_grid = self._decode_tile_layer(collision_layer)
            for gy in range(self.height):
                for gx in range(self.width):
                    gid = self._strip_gid_flags(collision_grid[gy][gx])
                    if gid != 0:
                        self.solid_rects.append(
                            pygame.Rect(
                                gx * settings.TILE_SIZE,
                                gy * settings.TILE_SIZE,
                                settings.TILE_SIZE,
                                settings.TILE_SIZE,
                            )
                        )

        for layer in object_layers:
            for obj in layer.get("objects", []):
                self._spawn_object(obj)

    def _decode_tile_layer(self, layer: dict) -> list[list[int]]:
        raw = layer.get("data")
        if raw is None:
            raise ValueError(
                f"Layer '{layer.get('name', '<unnamed>')}' has no inline tile data. "
                "Export your Tiled map with embedded layer data."
            )
        if len(raw) != self.width * self.height:
            raise ValueError(f"Layer '{layer.get('name', '<unnamed>')}' has unexpected data length.")

        return [raw[y * self.width : (y + 1) * self.width] for y in range(self.height)]

    def _spawn_object(self, obj: dict) -> None:
        name = str(obj.get("name", "")).strip().lower()
        if not name:
            return

        x = int(obj.get("x", 0))
        y = int(obj.get("y", 0))
        w = int(obj.get("width", 0))
        h = int(obj.get("height", 0))

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
            rect_w = w if w > 0 else settings.TILE_SIZE
            rect_h = h if h > 0 else settings.TILE_SIZE
            rect_y = y - rect_h if h == 0 else y
            self.exit_rect = pygame.Rect(x, rect_y, rect_w, rect_h)

    def _load_tilesets_from_tiled(self, data: dict, map_path: str) -> list[LoadedTileset]:
        map_dir = os.path.dirname(map_path)
        loaded: list[LoadedTileset] = []

        for tileset in data.get("tilesets", []):
            firstgid = int(tileset.get("firstgid", 1))

            # External TSX tileset
            if "source" in tileset:
                tsx_path = os.path.normpath(os.path.join(map_dir, tileset["source"]))
                ts_meta = self._read_tsx(tsx_path)
            else:
                ts_meta = self._read_embedded_tileset(tileset, map_dir)

            if ts_meta["tilewidth"] != settings.TILE_SIZE or ts_meta["tileheight"] != settings.TILE_SIZE:
                raise ValueError(
                    f"Tileset '{ts_meta['name']}' uses {ts_meta['tilewidth']}x{ts_meta['tileheight']} tiles; "
                    f"expected {settings.TILE_SIZE}x{settings.TILE_SIZE}."
                )

            image = pygame.image.load(ts_meta["image_path"]).convert_alpha()
            tiles = self.slice_tilesheet(
                image,
                ts_meta["tilewidth"],
                ts_meta["tileheight"],
                margin=ts_meta.get("margin", 0),
                spacing=ts_meta.get("spacing", 0),
                tilecount=ts_meta.get("tilecount"),
                columns=ts_meta.get("columns"),
            )
            loaded.append(LoadedTileset(firstgid=firstgid, tiles=tiles))

        loaded.sort(key=lambda ts: ts.firstgid)
        return loaded

    def _read_embedded_tileset(self, tileset: dict, map_dir: str) -> dict:
        image_rel = tileset.get("image")
        if not image_rel:
            raise ValueError("Embedded tileset is missing an image.")
        image_path = self._resolve_tiled_path(map_dir, image_rel)
        return {
            "name": tileset.get("name", os.path.basename(image_rel)),
            "image_path": image_path,
            "tilewidth": int(tileset["tilewidth"]),
            "tileheight": int(tileset["tileheight"]),
            "spacing": int(tileset.get("spacing", 0)),
            "margin": int(tileset.get("margin", 0)),
            "tilecount": int(tileset["tilecount"]) if "tilecount" in tileset else None,
            "columns": int(tileset["columns"]) if "columns" in tileset else None,
        }

    def _read_tsx(self, tsx_path: str) -> dict:
        root = ET.parse(tsx_path).getroot()
        image_node = root.find("image")
        if image_node is None or not image_node.get("source"):
            raise ValueError(f"TSX file '{tsx_path}' is missing its image source.")

        tsx_dir = os.path.dirname(tsx_path)
        image_path = self._resolve_tiled_path(tsx_dir, image_node.get("source"))
        return {
            "name": root.get("name", os.path.basename(tsx_path)),
            "image_path": image_path,
            "tilewidth": int(root.get("tilewidth", settings.TILE_SIZE)),
            "tileheight": int(root.get("tileheight", settings.TILE_SIZE)),
            "spacing": int(root.get("spacing", 0)),
            "margin": int(root.get("margin", 0)),
            "tilecount": int(root.get("tilecount")) if root.get("tilecount") else None,
            "columns": int(root.get("columns")) if root.get("columns") else None,
        }

    def _resolve_tiled_path(self, base_dir: str, relative_path: str) -> str:
        """Resolve Tiled image/source paths relative to the map/tsx file first."""
        candidate = os.path.normpath(os.path.join(base_dir, relative_path))
        if os.path.exists(candidate):
            return candidate

        # Helpful fallback for student projects: allow bare filenames from assets/images.
        fallback = asset_path("images", os.path.basename(relative_path))
        if os.path.exists(fallback):
            return fallback

        raise FileNotFoundError(f"Could not resolve Tiled path '{relative_path}' from '{base_dir}'.")

    @staticmethod
    def _strip_gid_flags(gid: int) -> int:
        return gid & _GID_MASK

    def get_tile_image(self, gid: int) -> pygame.Surface | None:
        gid = self._strip_gid_flags(gid)
        if gid == 0:
            return None

        for i, tileset in enumerate(self.tilesets):
            next_firstgid = self.tilesets[i + 1].firstgid if i + 1 < len(self.tilesets) else None
            if next_firstgid is None or gid < next_firstgid:
                index = gid - tileset.firstgid
                if 0 <= index < len(tileset.tiles):
                    return tileset.tiles[index]
                return None

        return None

    def get_solid_hits(self, rect: pygame.Rect) -> list[pygame.Rect]:
        return [r for r in self.solid_rects if r.colliderect(rect)]

    def rect_collides_solid(self, rect: pygame.Rect) -> bool:
        return any(r.colliderect(rect) for r in self.solid_rects)

    def update(self, dt: float, player, bullets, boss_bullets, enemy_bullets) -> None:
        for e in list(self.enemies):
            if hasattr(e, "weapon"):
                e.update(dt, self, player, enemy_bullets)
            else:
                e.update(dt, self, player)

        if self.boss and self.boss.alive():
            self.boss.update(dt, self, player, boss_bullets)

        for p in list(self.pickups):
            p.update(dt * 1000)

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

                # Legacy CSV draw path
                if not self._looks_like_tiled_gid(gid) and gid in self.draw_ids:
                    legacy_index = self.tile_id_to_sheet_index.get(gid)
                    if legacy_index is None or not self.tilesets:
                        continue
                    if 0 <= legacy_index < len(self.tilesets[0].tiles):
                        img = self.tilesets[0].tiles[legacy_index]
                    else:
                        continue
                else:
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
                (
                    self.exit_rect.x - camera_x,
                    self.exit_rect.y - camera_y,
                    self.exit_rect.w,
                    self.exit_rect.h,
                ),
                2,
            )

    def _looks_like_tiled_gid(self, value: int) -> bool:
        # CSV maps only use a tiny custom ID range. Tiled gids are usually 0..N and may contain flip flags.
        return value == 0 or value > 100 or bool(value & _FLIP_MASK)

    def load_background_layer(self, image_path, parallax_factor=0.5, y_offset=0, scale=None):
        image = pygame.image.load(image_path).convert_alpha()
        if scale is not None:
            image = pygame.transform.scale(image, scale)
        self.background_layers.append(BackgroundLayer(image, parallax_factor, y_offset))

    def draw_backgrounds(self, screen, camera_x, screen_width, screen_height):
        for layer in self.background_layers:
            image = layer.image
            image_width = image.get_width()
            x = camera_x * layer.parallax_factor
            start_x = int(x) % image_width
            draw_x = -start_x
            while draw_x < screen_width:
                screen.blit(image, (draw_x, layer.y_offset))
                draw_x += image_width

    def load_backgrounds(self):
        layers = [
            (self.level_name + "bg1.png", 0.1),
            (self.level_name + "bg2.png", 0.3),
            (self.level_name + "bg3.png", 0.5),
        ]

        for filename, parallax in layers:
            path = asset_path("levels", filename)
            if not os.path.exists(path):
                continue
            image = pygame.image.load(path).convert_alpha()
            self.background_layers.append(BackgroundLayer(image, parallax, 0))
