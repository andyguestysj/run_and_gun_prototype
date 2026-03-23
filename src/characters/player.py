# player.py
# Generic Player base class (movement, combat, health, animation selection).
# Specific characters should subclass Player and provide sprite/animation config.

from __future__ import annotations
import pygame

from ..utils import load_image, slice_sprite_sheet_row
from ..weapons.weapon import Weapon
from ..weapons.pistol import Pistol
from ..animation import Animation
from .. import settings


class Player(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: tuple[int, int],
        *,
        sprite_sheet: str,
        idle_row: int,
        run_row: int,
        jump_row: int,
        idle_frames: int,
        run_frames: int,
        jump_frames: int,
        frame_w: int = 32,
        frame_h: int = 32,
        stride_x: int = 32,
        start_x: int = 0,
        start_y: int = 0,
        muzzle_dx: int = 16,
        muzzle_dy: int = 4,
        idle_frame_duration: float = 0.15,
        run_frame_duration: float = 0.20,
        jump_frame_duration: float = 0.12,
        max_health: int = settings.PLAYER_MAX_HEALTH,
        move_speed: float = settings.PLAYER_SPEED,
        jump_speed: float = settings.JUMP_SPEED,
        weapon: Weapon | None = None,
    ):
        super().__init__()

        # --- Character visuals / animation frames ---
        sheet = load_image(sprite_sheet)

        self.anim_idle = slice_sprite_sheet_row(
            sheet,
            row=idle_row,
            frame_w=frame_w,
            frame_h=frame_h,
            num_frames=idle_frames,
            stride_x=stride_x,
            start_x=start_x,
            start_y=start_y,
            clamp=True,
        )
        self.anim_run = slice_sprite_sheet_row(
            sheet,
            row=run_row,
            frame_w=frame_w,
            frame_h=frame_h,
            num_frames=run_frames,
            stride_x=stride_x,
            start_x=start_x,
            start_y=start_y,
            clamp=True,
        )
        self.anim_jump = slice_sprite_sheet_row(
            sheet,
            row=jump_row,
            frame_w=frame_w,
            frame_h=frame_h,
            num_frames=jump_frames,
            stride_x=stride_x,
            start_x=start_x,
            start_y=start_y,
            clamp=True,
        )

        if len(self.anim_idle) < 2:
            print("[WARN] anim_idle has <2 frames. Check your sprite sheet row/frame count settings.")

        self.image = self.anim_idle[0]
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pygame.Vector2(self.rect.topleft)

        # --- Physics / movement state ---
        self.vel = pygame.Vector2(0.0, 0.0)
        self.on_ground = False
        self.on_ladder = False
        self.facing = 1
        self.climb_intent = 0

        self.move_speed = float(move_speed)
        self.jump_speed = float(jump_speed)
        self.ladder_speed = float(settings.LADDER_SPEED)
        self.moving = False

        self.jump_buffer_time = 0.12
        self.jump_buffer = 0.0

        self.coyote_time = 0.10
        self.coyote_timer = 0.0

        self.weapon = weapon if weapon is not None else Pistol()
        self.health = max_health
        self.max_health = max_health
        self.invuln_time = 0.0

        self.muzzle_dx = muzzle_dx
        self.muzzle_dy = muzzle_dy

        self.idle_anim = Animation(self.anim_idle, frame_duration=idle_frame_duration, loop=True)
        self.run_anim = Animation(self.anim_run, frame_duration=run_frame_duration, loop=True)
        self.jump_anim = Animation(self.anim_jump, frame_duration=jump_frame_duration, loop=True)

        self.current_anim = self.idle_anim

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def take_damage(self, amount: int) -> None:
        if self.invuln_time > 0:
            return
        self.health -= amount
        self.invuln_time = 0.6
        if self.health < 0:
            self.health = 0

    def is_dead(self) -> bool:
        return self.health <= 0

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        self.vel.x = 0.0
        self.moving = False
        self.climb_intent = 0

        if keys[pygame.K_a]:
            self.vel.x -= self.move_speed
            self.facing = -1
            self.moving = True

        if keys[pygame.K_d]:
            self.vel.x += self.move_speed
            self.facing = 1
            self.moving = True

        if keys[pygame.K_w]:
            self.climb_intent -= 1
        if keys[pygame.K_s]:
            self.climb_intent += 1

    def queue_jump(self) -> None:
        """Called on key press. Stores jump for short time."""
        self.jump_buffer = self.jump_buffer_time

    def cut_jump(self) -> None:
        """Called on key release for variable jump height."""
        if self.on_ladder:
            return
        if self.vel.y < 0:
            self.vel.y *= 0.45

    def try_shoot(self, bullets_group: pygame.sprite.Group) -> bool:
        muzzle = pygame.Vector2(
            self.rect.centerx + self.muzzle_dx * self.facing,
            self.rect.centery + self.muzzle_dy,
        )
        before = len(bullets_group)
        self.weapon.shoot(bullets_group, muzzle, self.facing)
        return len(bullets_group) > before

    def update(self, dt: float, level) -> None:
        if self.invuln_time > 0:
            self.invuln_time = max(0.0, self.invuln_time - dt)

        if self.jump_buffer > 0:
            self.jump_buffer = max(0.0, self.jump_buffer - dt)

        if self.coyote_timer > 0:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        self.weapon.update(dt)

        touching_ladder = level.rect_overlaps_ladder(self.rect)
        self.on_ladder = touching_ladder and self.climb_intent != 0

        if self.on_ladder:
            self.vel.y = self.climb_intent * self.ladder_speed
            if self.jump_buffer > 0:
                self.on_ladder = False
                self.vel.y = -self.jump_speed
                self.jump_buffer = 0.0
        else:
            self.vel.y += settings.GRAVITY * dt

        # Horizontal movement
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        hits = level.get_solid_hits(self.rect)
        for tile_rect in hits:
            if self.vel.x > 0:
                self.rect.right = tile_rect.left
            elif self.vel.x < 0:
                self.rect.left = tile_rect.right
            self.pos.x = self.rect.x

        # Vertical movement
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

        if not self.on_ladder and not self.on_ground:
            probe = self.rect.move(0, 1)
            if level.get_solid_hits(probe):
                self.on_ground = True

        if self.on_ground:
            self.coyote_timer = self.coyote_time

        can_jump = (self.on_ground or self.coyote_timer > 0.0) and not self.on_ladder
        if self.jump_buffer > 0 and can_jump:
            self.vel.y = -self.jump_speed
            self.on_ground = False
            self.coyote_timer = 0.0
            self.jump_buffer = 0.0

        if self.on_ladder:
            self.on_ground = False

        if not self.on_ground:
            self.set_anim(self.jump_anim, dt)
        elif self.moving:
            self.set_anim(self.run_anim, dt)
        else:
            self.set_anim(self.idle_anim, dt)

    def set_anim(self, anim: Animation, dt: float, speed: float = 1.0) -> None:
        if self.current_anim is not anim:
            self.current_anim = anim
            self.current_anim.reset()

        self.current_anim.update(dt, speed=speed)

        img = self.current_anim.image
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        self.image = img
