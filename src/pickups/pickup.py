import pygame


class Pickup(pygame.sprite.Sprite):
    """
    Base class for all pickups.

    Child classes should define:
        IMAGE_PATH
        PICKUP_NAME
        FRAME_WIDTH
        FRAME_HEIGHT
        apply(player)
    """

    IMAGE_PATH = None
    PICKUP_NAME = None
    FRAME_WIDTH = 32
    FRAME_HEIGHT = 32
    FRAME_COUNT = 2
    ANIMATION_SPEED = 0.20  # seconds per frame

    def __init__(self, x, y):
        super().__init__()

        if self.IMAGE_PATH is None:
            raise ValueError(
                f"{self.__class__.__name__} must define IMAGE_PATH"
            )

        if self.PICKUP_NAME is None:
            raise ValueError(
                f"{self.__class__.__name__} must define PICKUP_NAME"
            )

        sprite_sheet = pygame.image.load(self.IMAGE_PATH).convert_alpha()
        self.frames = self._load_frames(sprite_sheet)

        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        self.animation_timer = 0

    def _load_frames(self, sprite_sheet):
        frames = []

        for i in range(self.FRAME_COUNT):
            frame_surface = pygame.Surface(
                (self.FRAME_WIDTH, self.FRAME_HEIGHT),
                pygame.SRCALPHA
            )

            frame_surface.blit(
                sprite_sheet,
                (0, 0),
                (
                    i * self.FRAME_WIDTH,
                    0,
                    self.FRAME_WIDTH,
                    self.FRAME_HEIGHT
                )
            )

            frames.append(frame_surface)

        return frames

    def update(self, dt):
        """
        Animate between the pickup frames.

        dt should be delta time in seconds.
        """
        self.animation_timer += dt

        if self.animation_timer >= self.ANIMATION_SPEED:
            self.animation_timer -= self.ANIMATION_SPEED
            self.current_frame = (self.current_frame + 1) % self.FRAME_COUNT
            self.image = self.frames[self.current_frame]

    def apply(self, player):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement apply(player)"
        )