from .pickup import Pickup


class HealthPickup(Pickup):
    IMAGE_PATH = "assets/pickups/health.png"
    PICKUP_NAME = "health"
    FRAME_WIDTH = 32
    FRAME_HEIGHT = 32

    def apply(self, player):
        player.health = min(player.max_health, player.health + 25)
        self.kill()