import time
import pygame
import math
from abc import ABC, abstractmethod
from settings import *
from debug_logger import logger

import pygame
import math
from abc import ABC, abstractmethod
from settings import RED, GREEN, BLUE
from projectile import EnemyProjectile
from platforms import LadderPlatform


class Enemy(pygame.sprite.Sprite, ABC):
    def __init__(self, game, x, y):
        """
        Initialize the enemy.

        :param game: The current game instance.
        :type game: Game
        :param x: The x position of the enemy.
        :type x: int
        :param y: The y position of the enemy.
        :type y: int
        """
        super().__init__()
        self.game = game
        self.image = pygame.Surface((30, 30))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.damage_cooldown = 500
        self.last_damage_time = 0
        self.chase_range = 400

        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invulnerable_duration = 500

        self.max_health = 100
        self.health = self.max_health
        self.healthbar_width = 40
        self.healthbar_height = 5

        self.vel_x = 0
        self.vel_y = 0
        self.patrol_speed = 1
        self.chase_speed = 2
        self.acceleration = 0.2
        self.gravity = 0.8
        self.patrol_direction = 1
        self.vision_range = 300
        self.on_ground = False

    def draw_health_bar(self, surface, camera):
        """
        Draw the enemy's health bar on the screen.

        :param surface: The surface on which to draw the health bar.
        :type surface: pygame.Surface
        :param camera: The camera to use for drawing the health bar.
        :type camera: Camera
        """
        pos = camera.apply(self)
        health_ratio = self.health / self.max_health
        pygame.draw.rect(
            surface,
            (255, 0, 0),
            (pos.x - 5, pos.y - 10, self.healthbar_width, self.healthbar_height),
        )
        pygame.draw.rect(
            surface,
            (0, 255, 0),
            (
                pos.x - 5,
                pos.y - 10,
                self.healthbar_width * health_ratio,
                self.healthbar_height,
            ),
        )

    def take_damage(self, amount):
        """
        Reduce the enemy's health by the given amount.

        :param amount: The amount to subtract from the enemy's health.
        :type amount: int
        """
        try:
            if not self.invulnerable:
                self.health -= amount
                logger.warning(f"{self.__class__.__name__} at ({self.rect.x}, {self.rect.y}) took {amount} damage. Health: {self.health}/{self.max_health}")
                self.invulnerable = True
                self.invulnerable_timer = pygame.time.get_ticks()
                if self.health <= 0:
                    self.kill()
        except Exception as e:
            logger.error(f"Error in take_damage for {self.__class__.__name__}", exc_info=e)

    def detect_player(self):
        """
        Check if the player is within the enemy's line of sight.

        :return: True if the player is in range, False otherwise.
        :rtype: bool
        """
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        return distance <= self.vision_range

    def apply_gravity(self):
        """
        Apply gravity to the enemy's vertical velocity.

        """

        self.vel_y += self.gravity
        if self.vel_y > 10:
            self.vel_y = 10

    def update(self):
        """
        Update the enemy's state for the current frame.

        This method updates the invulnerability status, checks for collisions with the player,
        applies gravity, handles platform collisions, and moves the enemy.

        Invulnerability is checked based on the duration since the last invulnerability timer.
        If the enemy is invulnerable and the duration has passed, invulnerability is removed.

        The method also checks for player collisions and applies gravity to the enemy's
        vertical velocity. Platform collisions are handled, and the enemy is moved according
        to its current velocity and state.
        """
        if self.game.debug_mode:
            start_time = time.time()

        current_time = pygame.time.get_ticks()
        if self.invulnerable:
            if current_time - self.invulnerable_timer > self.invulnerable_duration:
                self.invulnerable = False

        self.check_player_collision()
        self.apply_gravity()
        self.handle_platform_collision()
        self.move()

        if self.game.debug_mode:
            logger.log_performance(f"{self.__class__.__name__} update", start_time)
            logger.trace(f"{self.__class__.__name__} pos: ({self.rect.x}, {self.rect.y}), vel: ({self.vel_x}, {self.vel_y})")

    @abstractmethod
    def move(self):
        """
        Move the enemy according to its current state and velocity.

        This method is abstract and must be implemented by subclasses.

        :return: None
        """
        pass

    def check_player_collision(self):
        """
        Check if the enemy has collided with the player.

        If the enemy has collided with the player and the player is not invulnerable to the enemy, the player is dealt 10 damage and the enemy's last damage time is updated.

        :return: None
        """
        if self.rect.colliderect(self.game.player.rect):
            current_time = pygame.time.get_ticks()
            if not self.game.player.is_invulnerable_to(self):
                if current_time - self.last_damage_time >= self.damage_cooldown:
                    self.game.player.take_damage(10, self)
                    self.last_damage_time = current_time

    def handle_platform_collision(self):
        """
        Handle platform collisions for the enemy.

        This method checks if the enemy has collided with any platforms in the game and
        handles the collision accordingly. If the enemy has collided with a platform from
        the top, it sets the enemy's on_ground flag to True and sets the enemy's vertical
        velocity to 0. If the enemy has collided with a platform from the bottom, it sets
        the enemy's vertical velocity to 0. If the enemy has collided with a platform from
        the left or right, it reverses the enemy's patrol direction.

        :return: None
        """
        self.on_ground = False
        for platform in self.game.platforms:
            if isinstance(platform, LadderPlatform):
                continue

            if self.rect.colliderect(platform.rect):
                overlap_left = self.rect.right - platform.rect.left
                overlap_right = platform.rect.right - self.rect.left
                overlap_top = self.rect.bottom - platform.rect.top
                overlap_bottom = platform.rect.bottom - self.rect.top

                min_overlap = min(
                    overlap_left, overlap_right, overlap_top, overlap_bottom
                )

                if min_overlap == overlap_top and self.vel_y >= 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif min_overlap == overlap_bottom and self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
                elif min_overlap == overlap_left and self.vel_x > 0:
                    self.rect.right = platform.rect.left
                    self.vel_x = 0
                    self.patrol_direction *= -1
                elif min_overlap == overlap_right and self.vel_x < 0:
                    self.rect.left = platform.rect.right
                    self.vel_x = 0
                    self.patrol_direction *= -1


class GroundEnemy(Enemy):
    def __init__(self, game, x, y):
        """
        Initialize a GroundEnemy instance.

        :param game: The game object that owns this enemy.
        :param x: The x-coordinate of the enemy's starting position.
        :param y: The y-coordinate of the enemy's starting position.
        :return: None
        """
        super().__init__(game, x, y)
        self.image.fill(RED)
        self.max_health = GROUND_ENEMIE_HEALTH
        self.health = self.max_health

    def check_edge(self):
        """
        Check if the enemy is at the edge of a platform.

        :return: True if the enemy is at the edge of a platform, False otherwise.
        """
        edge_check = self.rect.copy()
        edge_check.x += self.patrol_direction * self.patrol_speed
        edge_check.y += 5

        has_ground = False
        for platform in self.game.platforms:
            if not isinstance(platform, LadderPlatform) and edge_check.colliderect(
                platform.rect
            ):
                has_ground = True
                break
        return not has_ground

    def move(self):
        """
        Move the enemy.

        If the player is in sight, the enemy will move towards the player. Otherwise, it will move back and forth between two points on the platform it is on.

        When the enemy is on the ground, it will move horizontally. When it is not on the ground, it will not move at all.

        :return: None
        """
        if self.detect_player():
            dx = self.game.player.rect.centerx - self.rect.centerx
            target_speed = self.chase_speed * (1 if dx > 0 else -1)
        else:
            if self.check_edge():
                self.patrol_direction *= -1
            target_speed = self.patrol_speed * self.patrol_direction

        if self.vel_x < target_speed:
            self.vel_x = min(self.vel_x + self.acceleration, target_speed)
        elif self.vel_x > target_speed:
            self.vel_x = max(self.vel_x - self.acceleration, target_speed)

        if self.on_ground:
            self.rect.x += self.vel_x
        self.rect.y += self.vel_y


class FlyingEnemy(Enemy):
    def __init__(self, game, x, y):
        """
        Initialize a FlyingEnemy instance.

        :param game: The current game instance.
        :type game: Game
        :param x: The x-coordinate of the enemy's starting position.
        :type x: int
        :param y: The y-coordinate of the enemy's starting position.
        :type y: int

        Attributes:
        image: The visual representation of the flying enemy.
        gravity: The gravity affecting the flying enemy, set to 0.
        patrol_radius: The radius of the patrol path.
        angle: The current angle in the patrol path.
        angle_speed: The speed of rotation in the patrol path.
        start_pos: The starting position of the flying enemy.
        max_health: The maximum health of the flying enemy.
        health: The current health of the flying enemy.
        dive_cooldown: The cooldown time between dive attacks.
        last_dive: The time of the last dive attack.
        diving: A flag indicating if the enemy is currently diving.
        original_y: The original y-coordinate of the flying enemy.
        hover_speed: The speed at which the flying enemy hovers.
        chase_speed: The speed at which the flying enemy chases the player.
        """

        super().__init__(game, x, y)
        self.image.fill((255, 100, 100))
        self.gravity = 0
        self.patrol_radius = 100
        self.angle = 0
        self.angle_speed = 0.02
        self.start_pos = (x, y)
        self.max_health = FLYING_ENEMIE_HEALTH
        self.health = self.max_health
        self.dive_cooldown = 2000
        self.last_dive = 0
        self.diving = False
        self.original_y = y
        self.hover_speed = 2
        self.chase_speed = 4

    def move(self):
        """
        Update the flying enemy's position.

        If the player is detected, the flying enemy will either dive towards the player or hover around it.
        If the player is not detected, the flying enemy will hover around its starting position.

        :return: None
        """
        current_time = pygame.time.get_ticks()

        if self.detect_player():
            dx = self.game.player.rect.centerx - self.rect.centerx
            dy = self.game.player.rect.centery - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)

            if current_time - self.last_dive >= self.dive_cooldown:
                self.diving = True
                self.last_dive = current_time

            if self.diving:
                if distance > 10:
                    self.vel_x = dx / distance * self.chase_speed
                    self.vel_y = dy / distance * self.chase_speed
                else:
                    self.diving = False
            else:
                target_dist = 100

                if distance > target_dist:
                    self.vel_x = dx / distance * self.hover_speed
                    self.vel_y = dy / distance * self.hover_speed
                else:
                    angle = math.atan2(dy, dx)
                    circle_angle = angle + math.pi / 2
                    self.vel_x = math.cos(circle_angle) * self.hover_speed
                    self.vel_y = math.sin(circle_angle) * self.hover_speed
        else:
            dx = self.start_pos[0] - self.rect.centerx
            dy = self.start_pos[1] - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 5:
                self.vel_x = dx / distance * self.hover_speed
                self.vel_y = dy / distance * self.hover_speed
            else:
                self.vel_x = 0
                self.vel_y = 0

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y


class ShooterEnemy(Enemy):
    def __init__(self, game, x, y):
        """
        Initialize a ShooterEnemy instance.

        :param game: The game object that owns this enemy.
        :param x: The x-coordinate of the enemy's starting position.
        :param y: The y-coordinate of the enemy's starting position.

        Attributes:
        image: The visual representation of the shooter enemy.
        shoot_range: The range within which the enemy can shoot at the player.
        shoot_cooldown: The cooldown time between shots.
        last_shot: The time of the last shot fired.
        projectiles: A group of projectiles fired by the enemy.
        patrol_point: The starting point of the enemy's patrol path.
        patrol_range: The range of the patrol path.
        max_health: The maximum health of the shooter enemy.
        health: The current health of the shooter enemy.
        can_use_ladders: A flag indicating if the enemy can use ladders.
        retreat_range: The range at which the enemy retreats from the player.
        """

        super().__init__(game, x, y)
        self.image.fill(BLUE)
        self.shoot_range = 400
        self.shoot_cooldown = 1000
        self.last_shot = 0
        self.projectiles = pygame.sprite.Group()
        self.patrol_point = self.rect.x
        self.patrol_range = 100
        self.max_health = SHOOTER_ENEMIE_HEALTH
        self.health = self.max_health
        self.can_use_ladders = False
        self.shoot_range = 400
        self.retreat_range = 200

    def check_edge(self):
        """
        Check if the enemy is on the edge of a platform.

        :return: True if the enemy is on the edge of a platform, False otherwise.
        """
        edge_check = self.rect.copy()
        edge_check.x += self.patrol_direction * self.patrol_speed
        edge_check.y += 5

        has_ground = False
        for platform in self.game.platforms:
            if edge_check.colliderect(platform.rect):
                has_ground = True
                break
        return not has_ground

    def move(self):
        """
        Move the enemy based on player position and range conditions.
        """
        if self.detect_player():
            dx = self.game.player.rect.centerx - self.rect.centerx
            dy = self.game.player.rect.centery - self.rect.centery
            distance = math.sqrt(dx**2 + dy**2)

            if distance <= self.shoot_range:
                self.shoot()
                self.vel_x = 0
            else:
                target_speed = self.chase_speed * (1 if dx > 0 else -1)
                self.adjust_velocity(target_speed)
        else:
            if self.check_edge():
                self.patrol_direction *= -1
            target_speed = self.patrol_speed * self.patrol_direction
            self.adjust_velocity(target_speed)

        if self.on_ground:
            self.rect.x += self.vel_x
        self.rect.y += self.vel_y

    def adjust_velocity(self, target_speed):
        """Helper method to adjust velocity towards target speed"""
        if self.vel_x < target_speed:
            self.vel_x = min(self.vel_x + self.acceleration, target_speed)
        elif self.vel_x > target_speed:
            self.vel_x = max(self.vel_x - self.acceleration, target_speed)

    def shoot(self):
        """
        Shoot at the player if the cooldown has expired.

        This method checks if the cooldown since the last shot has expired. If it has,
        it calculates the angle between the enemy and the player, creates a new
        EnemyProjectile instance, and adds it to the game's sprite groups.

        Attributes:
        last_shot (int): The time of the last shot.
        shoot_cooldown (int): The cooldown time between shots.
        """
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot >= self.shoot_cooldown:
            logger.info(f"ShooterEnemy firing at player. Position: ({self.rect.centerx}, {self.rect.centery})")
            self.last_shot = current_time
            dx = self.game.player.rect.centerx - self.rect.centerx
            dy = self.game.player.rect.centery - self.rect.centery
            angle = math.atan2(dy, dx)

            projectile = EnemyProjectile(
                self.game, self.rect.centerx, self.rect.centery, angle
            )
            self.projectiles.add(projectile)
            self.game.all_sprites.add(projectile)

    def update(self):
        """
        Update the enemy.

        Calls the parent's update method to update the enemy's position.

        Then, updates each projectile in the enemy's projectiles group and kills any
        projectiles that are outside of the world.

        Finally, if the player is within the enemy's view range, the enemy will move
        towards the player. If the player is within the enemy's shoot range, the enemy
        will shoot at the player.

        :return: None
        """
        super().update()

        self.projectiles.update()

        for projectile in self.projectiles:
            if (
                projectile.rect.right < 0
                or projectile.rect.left > self.game.world_width
                or projectile.rect.bottom < 0
                or projectile.rect.top > self.game.world_height
            ):
                projectile.kill()

        if self.detect_player():
            distance = math.sqrt(
                (self.game.player.rect.centerx - self.rect.centerx) ** 2
                + (self.game.player.rect.centery - self.rect.centery) ** 2
            )
            if distance <= self.shoot_range:
                self.shoot()


class TankEnemy(Enemy):
    def __init__(self, game, x, y):
        """
        Initialize a TankEnemy instance.

        :param game: The game object that owns this enemy.
        :param x: The x-coordinate of the enemy's starting position.
        :param y: The y-coordinate of the enemy's starting position.
        """
        super().__init__(game, x, y)
        self.image = pygame.Surface((40, 40))
        self.image.fill(GREEN)
        self.max_health = TANK_ENEMIE_HEALTH
        self.health = self.max_health
        self.patrol_speed = 1
        self.chase_speed = 2
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def check_edge(self):
        """
        Check if the enemy is close to an edge.

        This method checks if the enemy is close to an edge by moving a temporary
        rectangle (edge_check) in the direction of the patrol direction. If the
        edge_check rectangle is not colliding with any platforms, the method
        returns True, indicating that the enemy is close to an edge. Otherwise, it
        returns False.

        :return: True if the enemy is close to an edge, False otherwise.
        """
        edge_check = self.rect.copy()
        edge_check.x += self.patrol_direction * self.patrol_speed
        edge_check.y += 5

        has_ground = False
        for platform in self.game.platforms:
            if edge_check.colliderect(platform.rect):
                has_ground = True
                break
        return not has_ground

    def move(self):
        """
        Move the enemy.

        If the player is in range, the enemy will chase the player. Otherwise, the
        enemy will patrol back and forth within its platform. If the enemy is close
        to an edge, it will turn around.

        :return: None
        """
        if self.detect_player():
            dx = self.game.player.rect.centerx - self.rect.centerx
            target_speed = self.chase_speed * (1 if dx > 0 else -1)
        else:
            if self.check_edge():
                self.patrol_direction *= -1
            target_speed = self.patrol_speed * self.patrol_direction

        if self.vel_x < target_speed:
            self.vel_x = min(self.vel_x + self.acceleration / 2, target_speed)
        elif self.vel_x > target_speed:
            self.vel_x = max(self.vel_x - self.acceleration / 2, target_speed)

        if self.on_ground:
            self.rect.x += self.vel_x
        self.rect.y += self.vel_y
