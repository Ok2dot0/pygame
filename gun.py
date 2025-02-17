import pygame
from platforms import LadderPlatform


class Gun(pygame.sprite.Sprite):
    def __init__(self, x, y):
        """
        Initialize a Gun instance.

        :param x: The x-coordinate of the gun's starting position.
        :param y: The y-coordinate of the gun's starting position.
        """
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill((255, 215, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Projectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, direction):
        """
        Initialize a Projectile instance.

        :param game: The game object that owns this projectile.
        :param x: The x-coordinate of the projectile's starting position.
        :param y: The y-coordinate of the projectile's starting position.
        :param direction: The direction that the projectile should travel in.
        """
        super().__init__()
        self.game = game
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 15
        self.direction = direction
        self.damage = 10

    def update(self):
        """
        Update the projectile's position.

        Move the projectile in the direction it was spawned with at the speed set in the constructor.
        Check for collisions with enemies and deal damage if a collision is detected.
        Check for collisions with platforms and kill the projectile if a collision is detected.
        Kill the projectile if it leaves the screen.
        """
        self.rect.x += self.speed * self.direction

        hits = pygame.sprite.spritecollide(self, self.game.enemies, False)
        for enemy in hits:
            enemy.take_damage(self.damage)
            self.kill()
            return

        if self.check_collisions(self.game.platforms):
            return

        camera = self.game.camera.camera
        view_width = self.game.screen.get_width()
        view_height = self.game.screen.get_height()

        screen_x = self.rect.x + camera.x
        screen_y = self.rect.y + camera.y

        if (
            screen_x < -50
            or screen_x > view_width + 50
            or screen_y < -50
            or screen_y > view_height + 50
        ):
            self.kill()

    def check_collisions(self, platforms):
        """
        Check if the projectile has collided with any platforms.

        :param platforms: A list of platforms to check for collisions with.
        :return: True if the projectile has collided with a platform, False otherwise.
        """
        for platform in platforms:
            if not isinstance(platform, LadderPlatform):
                if self.rect.colliderect(platform.rect):
                    self.kill()
                    return True
        return False
