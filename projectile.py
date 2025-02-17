import pygame
import math


class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, game, x, y, angle):
        """
        Initialize an EnemyProjectile instance.

        :param game: The game object that owns this projectile.
        :param x: The x-coordinate of the projectile's starting position.
        :param y: The y-coordinate of the projectile's starting position.
        :param angle: The angle in which the projectile should travel in radians.

        Attributes:
        image: The visual representation of the projectile.
        rect: The rectangle representing the projectile's position and size.
        speed: The speed at which the projectile travels.
        vel_x: The x component of the projectile's velocity.
        vel_y: The y component of the projectile's velocity.
        damage: The amount of damage the projectile inflicts on the player.
        """
        super().__init__()
        self.game = game
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = 8
        self.vel_x = math.cos(angle) * self.speed
        self.vel_y = math.sin(angle) * self.speed
        self.damage = 10

    def check_collisions(self, platforms):
        """
        Check if the projectile has collided with any platforms.

        :param platforms: A list of platforms to check for collisions with.
        :return: True if the projectile has collided with a platform, False otherwise.
        """

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.kill()
                return True
        return False

    def update(self):
        """
        Update the enemy projectile's position and handle collisions.

        This method updates the position of the projectile based on its velocity.
        It checks for collisions with platforms and the player, dealing damage
        to the player if a collision occurs and the player is not invulnerable.
        If the projectile goes outside the world boundaries or collides with a
        platform, it is destroyed.

        :return: None
        """

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        if self.check_collisions(self.game.platforms):
            return

        if self.rect.colliderect(self.game.player.rect):
            if not self.game.player.is_invulnerable_to(self):
                self.game.player.take_damage(self.damage, self)
                self.kill()
                return

        if (
            self.rect.right < 0
            or self.rect.left > self.game.world_width
            or self.rect.bottom < 0
            or self.rect.top > self.game.world_height
        ):
            self.kill()
