# enemies/enemy_boss.py
from __future__ import annotations
import pygame

from ..utils import load_image, slice_sprite_sheet_row
from ..animation import Animation
from ..weapons.pistol import Pistol
from .. import settings
from .enemy import Enemy


class BossEnemy(Enemy):
    """A simple boss with more health + ranged shots."""

    def __init__(self, pos: tuple[int, int]):
        super().__init__()

        sheet = load_image("enemy_boss_sheet.png")
        frames = slice_sprite_sheet_row(
            sheet, row=0, frame_w=64, frame_h=64,
            num_frames=2, stride_x=64, start_x=0, start_y=0, clamp=True
        )

        self.anim = Animation(frames, frame_duration=0.30, loop=True)
        self.current_anim = self.anim

        self.image = self.current_anim.image
        self.rect = self.image.get_rect(midbottom=(pos[0] + 32, pos[1] + 32))
        self.pos = pygame.Vector2(self.rect.topleft)

        self.health = 180
        self.max_health = 180

        self.vel = pygame.Vector2(0.0, 0.0)
        self.speed = 110.0

        self.weapon = Pistol()
        self.weapon.cooldown = 0.6

        self.on_ground = False

    def update(self, dt: float, level, player, boss_bullets: pygame.sprite.Group) -> None:
        direction = self.face_player(player)
        self.vel.x = self.speed * direction

        self.vel.y += settings.GRAVITY * dt

        # horizontal
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)
        if level.rect_collides_solid(self.rect):
            self.pos.x -= self.vel.x * dt
            self.rect.x = round(self.pos.x)
            self.vel.x = 0

        # vertical
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

        if not self.on_ground:
            probe = self.rect.move(0, 1)
            if level.get_solid_hits(probe):
                self.on_ground = True

        self.apply_anim(dt)

        self.weapon.update(dt)
        if self.weapon.can_shoot():
            muzzle = pygame.Vector2(self.rect.centerx + 18 * direction, self.rect.centery - 8)
            self.weapon.shoot(boss_bullets, muzzle, direction)
