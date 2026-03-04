# wizardbob.py
# Default playable character. Behaves exactly like the original Player implementation,
# but now as a concrete subclass of the generic Player base class.

from __future__ import annotations

from .player import Player
from ..weapons.pistol import Pistol
from .. import settings


class WizardBob(Player):
    def __init__(self, pos: tuple[int, int]):
        # Sprite sheet layout (matching the original player.py):
        # row 4 idle (6 frames), row 3 run (8 frames), row 5 jump (8 frames)
        super().__init__(
            pos,
            sprite_sheet="player_sheet.png",
            idle_row=4,
            run_row=3,
            jump_row=5,
            idle_frames=6,
            run_frames=8,
            jump_frames=8,
            frame_w=32,
            frame_h=32,
            stride_x=32,
            start_x=0,
            start_y=0,
            muzzle_dx=16,
            muzzle_dy=4,
            idle_frame_duration=0.15,
            run_frame_duration=0.20,
            jump_frame_duration=0.12,
            max_health=settings.PLAYER_MAX_HEALTH,
            move_speed=settings.PLAYER_SPEED,
            jump_speed=settings.JUMP_SPEED,
            weapon=Pistol(),
        )
