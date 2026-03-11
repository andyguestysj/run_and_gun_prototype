from .pickup import Pickup


class ShieldPickup(Pickup):
    IMAGE_PATH = "assets/pickups/shield.png"
    PICKUP_NAME = "shield"
    FRAME_WIDTH = 32
    FRAME_HEIGHT = 32

    def apply(self, player):
        player.shield = min(player.max_shield, player.shield + 25)
        self.kill()