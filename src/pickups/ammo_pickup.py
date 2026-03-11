from .pickup import Pickup


class AmmoPickup(Pickup):
    IMAGE_PATH = "assets/pickups/ammo.png"
    PICKUP_NAME = "ammo"
    FRAME_WIDTH = 32
    FRAME_HEIGHT = 32

    def apply(self, player):
        player.ammo += 20
        self.kill()