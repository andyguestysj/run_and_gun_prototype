# enemies/enemy_runner.py
from __future__ import annotations
import pygame

from ..utils import load_image, slice_sprite_sheet_row
from ..animation import Animation
from .. import settings
from .enemy import Enemy


class NormalEnemy(Enemy):
    """Simple patrol enemy (runner)."""
    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        sheet = load_image("enemy_runner_sheet.png")
        frames = slice_sprite_sheet_row(
            sheet, row=0, frame_w=32, frame_h=32,
            num_frames=6, stride_x=64, start_x=0, start_y=0, clamp=True
        )

        self.walk_anim = Animation(frames, frame_duration=0.10, loop=True)
        self.current_anim = self.walk_anim

        self.image = self.current_anim.image
        self.rect = self.image.get_rect(topleft=pos)

        self.pos = pygame.Vector2(self.rect.topleft)
        self.vel = pygame.Vector2(-80.0, 0.0)

        self.health = 30
        self.on_ground = False
        self.facing = 1

    def update(self, dt: float, level, player) -> None:
        # gravity
        self.vel.y += settings.GRAVITY * dt

        # horizontal (float)
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        if level.rect_collides_solid(self.rect):
            self.pos.x -= self.vel.x * dt
            self.rect.x = round(self.pos.x)
            self.vel.x *= -1
            self.facing *= -1

        # vertical (float)
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)

        self.on_ground = False
        hits = level.get_solid_hits(self.rect)
        for tile_rect in hits:
            if self.vel.y > 0:
                self.rect.bottom = tile_rect.top
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = tile_rect.bottom
                self.vel.y = 0
            self.pos.y = self.rect.y

        # ground probe
        if not self.on_ground:
            probe = self.rect.move(0, 1)
            if level.get_solid_hits(probe):
                self.on_ground = True

        # animation
        self.apply_anim(dt)

        # fell off world
        if self.rect.top > level.pixel_height + 200:
            self.kill()
