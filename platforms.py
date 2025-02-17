import pygame
from settings import *


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        """
        Initialize a Platform instance.

        :param x: The x-coordinate of the platform's position.
        :param y: The y-coordinate of the platform's position.
        :param width: The width of the platform.
        :param height: The height of the platform.
        """
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class LadderPlatform(Platform):
    def __init__(self, x, y, width, height):
        """
        Initialize a LadderPlatform instance.

        :param x: The x-coordinate of the ladder platform's position.
        :param y: The y-coordinate of the ladder platform's position.
        :param width: The width of the ladder platform.
        :param height: The height of the ladder platform.
        """
        super().__init__(x, y, width, height)
        self.image.fill(GREEN)
        self.image.set_alpha(192)


class DeadlyPlatform(Platform):
    def __init__(self, x, y, width, height):
        """
        Initialize a DeadlyPlatform instance.

        :param x: The x-coordinate of the platform's position.
        :param y: The y-coordinate of the platform's position.
        :param width: The width of the platform.
        :param height: The height of the platform.
        """
        super().__init__(x, y, width, height)
        self.image.fill((255, 0, 0))


class SlipperyPlatform(Platform):
    def __init__(self, x, y, width, height):
        """
        Initialize a SlipperyPlatform instance.

        :param x: The x-coordinate of the slippery platform's position.
        :param y: The y-coordinate of the slippery platform's position.
        :param width: The width of the slippery platform.
        :param height: The height of the slippery platform.
        """
        super().__init__(x, y, width, height)
        self.image.fill(BLUE)


class TeleporterPlatform(Platform):
    def __init__(self, x, y, width, height, pair_id=0):
        """
        Initialize a TeleporterPlatform instance.

        :param x: The x-coordinate of the teleporter platform's position.
        :param y: The y-coordinate of the teleporter platform's position.
        :param width: The width of the teleporter platform.
        :param height: The height of the teleporter platform.
        :param pair_id: The pair id of the teleporter platform. This is used to match the teleporter with its pair.
        """
        super().__init__(x, y, width, height)
        self.pair_id = pair_id
        self.image.fill((148, 0, 211))
        self.cooldown = 500
        self.last_teleport = 0
        self.image.set_alpha(128)
