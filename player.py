import time
import pygame
from settings import *
from sprite_loader import SpriteLoader
from platforms import (
    Platform,
    LadderPlatform,
    DeadlyPlatform,
    SlipperyPlatform,
    TeleporterPlatform,
)
from gun import Gun, Projectile
from debug_logger import logger


class Player(pygame.sprite.Sprite):
    def __init__(self, game, spawn_point):
        """
        Initialize a player object.

        :param game: The game object.
        :param spawn_point: The position at which the player will spawn.
        """
        super().__init__()
        self.game = game

        self.sprite_loader = SpriteLoader()
        scale = 2.0
        self.walking_frames = self.sprite_loader.get_player_frames(scale)
        self.ladder_frames = self.sprite_loader.get_ladder_frames(
            scale
        )

        self.current_frame = 0
        self.animation_delay = 100
        self.ladder_animation_delay = 150
        self.last_update = pygame.time.get_ticks()

        self.base_image = self.walking_frames[0]
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = spawn_point
        self.facing_right = True
        self.vel_y = 0
        self.vel_x = 0
        self.acceleration = 0.1
        self.slippery_acceleration = 0.9
        self.max_speed = 5
        self.slippery_max_speed = 100
        self.jump_power = -13
        self.sticky_jump_power = self.jump_power * 0.3
        self.gravity = 0.8
        self.on_ground = False
        self.platformtype = None
        self.ladder_y = 0
        self.ladder_x = 0
        self.slipperniess = 0.99
        self.in_ladder = False
        self.current_ladder = None
        self.on_ladder_top = False
        self.ladder_exit_threshold = 20
        self.has_gun = False
        self.facing_right = True
        self.projectiles = pygame.sprite.Group()
        self.gun_offset_x = 20
        self.gun_offset_y = 0
        self.gun_image = pygame.Surface((20, 10))
        self.gun_image.fill((255, 215, 0))
        self.base_image = self.image.copy()
        self.max_health = 100
        self.health = self.max_health
        self.healthbar_width = 200
        self.healthbar_height = 20

        self.invulnerable = False
        self.invulnerable_timers = {}
        self.invulnerable_duration = 1000
        self.flash_interval = 100
        self.last_flash = 0
        self.visible = True

        self.normal_width = self.rect.width
        self.normal_height = self.rect.height
        self.ladder_width = 19 * scale
        self.ladder_height = 30 * scale

    def is_invulnerable_to(self, source):
        """
        Check if the player is invulnerable to the given source.

        :param source: The source (e.g. enemy, projectile) to check invulnerability against.
        :return: True if the player is invulnerable to the source, False otherwise.
        """
        source_id = id(source)
        current_time = pygame.time.get_ticks()

        if source_id in self.invulnerable_timers:
            if (
                current_time - self.invulnerable_timers[source_id]
                < self.invulnerable_duration
            ):
                return True
            else:
                del self.invulnerable_timers[source_id]
        return False

    def update(self):
        """
        Update the player's state for the current frame.

        This method updates the player's position, animations, and visibility based on
        the current game state and player inputs. It handles the player's movement on
        ladders, adjusts the player's image based on the direction and animation frame,
        and manages the player's invulnerability status and flickering effect when invulnerable.

        Additionally, it processes player input, applies gravity when not on a ladder
        or when moving downwards, and moves the player. The player's projectiles are also
        updated, checking for collisions with platforms and enemies.
        """
        if self.game.debug_mode:
            start_time = time.time()
            
        current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()

        old_centerx = self.rect.centerx
        old_bottom = self.rect.bottom
        
        if self.in_ladder:

            self.rect.width = self.ladder_width
            self.rect.height = self.ladder_height
            self.rect.centerx = old_centerx
            self.rect.bottom = old_bottom
        else:
            self.rect.width = self.normal_width
            self.rect.height = self.normal_height
            self.rect.centerx = old_centerx
            self.rect.bottom = old_bottom

        is_moving_horizontally = abs(self.vel_x) > 0.5
        is_moving_vertically = (self.in_ladder and 
                              (keys[pygame.K_UP] or keys[pygame.K_DOWN]))
        
        if self.in_ladder:
            if is_moving_horizontally:
                if current_time - self.last_update > self.animation_delay:
                    self.last_update = current_time
                    self.current_frame = (self.current_frame + 1) % 5
                    self.base_image = self.walking_frames[self.current_frame]
                    if not self.facing_right:
                        self.image = pygame.transform.flip(self.base_image, True, False)
                    else:
                        self.image = self.base_image
            elif is_moving_vertically:
                if current_time - self.last_update > self.ladder_animation_delay:
                    self.last_update = current_time
                    self.current_frame = (self.current_frame + 1) % 2
                    self.base_image = self.ladder_frames[self.current_frame]
                    self.image = self.base_image
            else:
                self.current_frame = 0
                self.base_image = self.ladder_frames[0]
                self.image = self.base_image
        else:
            if is_moving_horizontally:
                if current_time - self.last_update > self.animation_delay:
                    self.last_update = current_time
                    self.current_frame = (self.current_frame + 1) % 5
                    self.base_image = self.walking_frames[self.current_frame]
                    if not self.facing_right:
                        self.image = pygame.transform.flip(self.base_image, True, False)
                    else:
                        self.image = self.base_image
            else:
                self.current_frame = 0
                self.base_image = self.walking_frames[0]
                if not self.facing_right:
                    self.image = pygame.transform.flip(self.base_image, True, False)
                else:
                    self.image = self.base_image

        if self.invulnerable_timers:
            if current_time - self.last_flash >= self.flash_interval:
                self.visible = not self.visible
                self.last_flash = current_time
                self.image.set_alpha(255 if self.visible else 128)
        else:
            self.visible = True
            self.image.set_alpha(255)

        self.invulnerable_timers = {
            enemy_id: timestamp 
            for enemy_id, timestamp in self.invulnerable_timers.items()
            if current_time - timestamp < self.invulnerable_duration
        }

        self.handle_input()
        if not self.in_ladder or self.vel_y > 0:
            self.apply_gravity()
        self.move()

        for projectile in self.projectiles:
            if projectile.check_collisions(self.game.platforms):
                continue

            for enemy in self.game.enemies:
                if projectile.rect.colliderect(enemy.rect):
                    enemy.take_damage(projectile.damage)
                    projectile.kill()

        if self.game.debug_mode:
            logger.log_performance("Player update", start_time)
            logger.trace(
                f"Player State: pos=({self.rect.x}, {self.rect.y}), "
                f"vel=({self.vel_x:.2f}, {self.vel_y:.2f}), "
                f"on_ground={self.on_ground}, in_ladder={self.in_ladder}, "
                f"health={self.health}"
            )

    def cooldown(cooldown_period):
        """
        A decorator that adds a cooldown period to a function.

        When the decorated function is called, it will first check if the time elapsed
        since the last call exceeds the cooldown period. If it does, the function will
        be called and the last call time will be updated. Otherwise, the function will
        not be called and None will be returned.

        :param cooldown_period: The time in milliseconds that the function must wait
        after being called before it can be called again.
        """
        def decorator(func):
            last_called = [0]

            def wrapper(*args, **kwargs):
                """
                Wrapper function to enforce a cooldown period on the decorated function.

                This function checks the time elapsed since the last call to the decorated function.
                If the elapsed time is greater than or equal to the specified cooldown period, the
                decorated function is executed, and the last call time is updated. Otherwise, the
                function is not executed, and None is returned.

                :param args: Positional arguments to pass to the decorated function.
                :param kwargs: Keyword arguments to pass to the decorated function.
                :return: The result of the decorated function if the cooldown period has passed; otherwise, None.
                """

                current_time = pygame.time.get_ticks()
                if current_time - last_called[0] >= cooldown_period:
                    last_called[0] = current_time
                    return func(*args, **kwargs)
                else:
                    return None

            return wrapper

        return decorator

    def take_damage(self, amount, source=None):
        """
        Inflict damage to the player and handle invulnerability and death.

        This method reduces the player's health by the specified amount. If the player
        is invulnerable to the given damage source, the method returns immediately
        without reducing health. Otherwise, it updates the player's health and sets
        the player to be temporarily invulnerable to the source of damage.

        The player's transparency is adjusted to indicate damage. If health drops to
        zero or below, the player's death is handled by calling the appropriate game
        method.

        :param amount: The amount of damage to inflict on the player.
        :type amount: int
        :param source: The source of the damage, which may be used to determine invulnerability.
        :type source: object or None
        """
        try:
            if source and self.is_invulnerable_to(source):
                logger.info(f"Player immune to damage from {source.__class__.__name__}")
                return

            self.health -= amount
            logger.warning(f"Player took {amount} damage from {source.__class__.__name__}. Health: {self.health}/{self.max_health}")

            if source:
                self.invulnerable_timers[id(source)] = pygame.time.get_ticks()

            self.image.set_alpha(128)

            if self.health <= 0:
                self.game.handle_player_death()
                
            logger.warning(
                f"Player took {amount} damage from {source.__class__.__name__ if source else 'Unknown'}. "
                f"Health: {self.health}/{self.max_health}. "
                f"Position: ({self.rect.x}, {self.rect.y})"
            )
        except Exception as e:
            logger.error("Error in player take_damage", exc_info=e)

    def draw_health_bar(self, surface):
        """
        Draw the player's health bar on the screen.

        This method calculates the player's current health ratio and draws two rectangles
        on the specified surface to represent the health bar. The background of the health
        bar is red, and the foreground, representing the current health, is green.

        :param surface: The surface on which to draw the health bar.
        :type surface: pygame.Surface
        """

        health_ratio = self.health / self.max_health
        pygame.draw.rect(
            surface, (255, 0, 0), (10, 10, self.healthbar_width, self.healthbar_height)
        )
        pygame.draw.rect(
            surface,
            (0, 255, 0),
            (10, 10, self.healthbar_width * health_ratio, self.healthbar_height),
        )

    def handle_input(self):
        """
        Handle all user input events.

        This method is responsible for capturing all user input events and
        performing the desired actions. It handles player movement, jumping,
        shooting, and ladder interaction.

        :return: None
        """
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            if self.on_ladder_top or (self.in_ladder and self.on_ground):
                self.jump()
                self.in_ladder = False
                self.current_ladder = None
                return
        if keys[pygame.K_f]:
            if self.has_gun:
                self.shoot()
        if self.in_ladder and self.current_ladder:
            LADDER_SPEED = 5
            ladder_rect = self.current_ladder.rect

            if keys[pygame.K_UP]:
                new_y = self.rect.y - LADDER_SPEED
                if new_y + self.rect.height > ladder_rect.top:
                    self.rect.y = new_y
                    self.vel_y = 0
                    if self.rect.bottom <= ladder_rect.top + 5:
                        self.on_ladder_top = True
                    else:
                        self.on_ladder_top = False

            elif keys[pygame.K_DOWN]:
                self.on_ladder_top = False
                new_y = self.rect.y + LADDER_SPEED
                if new_y < ladder_rect.bottom:
                    self.rect.y = new_y
                    self.vel_y = 0

            if keys[pygame.K_LEFT]:
                self.facing_right = False
                self.vel_x = -self.max_speed
            elif keys[pygame.K_RIGHT]:
                self.facing_right = True
                self.vel_x = self.max_speed
            else:
                self.vel_x = 0

            if not self.rect.colliderect(self.current_ladder.rect):
                self.in_ladder = False
                self.current_ladder = None
                self.on_ladder_top = False
                return

            return

        if keys[pygame.K_SPACE] and self.on_ground and not self.in_ladder:
            self.jump()

        if keys[pygame.K_LEFT]:
            if self.platformtype != 4:
                if self.vel_x > 0:
                    self.vel_x = 0
                if self.vel_x > -self.max_speed:
                    self.vel_x -= self.acceleration
            else:
                if self.vel_x > -self.slippery_max_speed:
                    self.vel_x -= self.slippery_acceleration

        if keys[pygame.K_RIGHT]:
            self.facing_right = True
            self.image = self.base_image.copy()
            if self.platformtype != 4:
                if self.vel_x < 0:
                    self.vel_x = 0
                if self.vel_x < self.max_speed:
                    self.vel_x += self.acceleration
            else:
                if self.vel_x < self.slippery_max_speed:
                    self.vel_x += self.slippery_acceleration
        if keys[pygame.K_LEFT]:
            self.facing_right = False
            self.image = pygame.transform.flip(self.base_image, True, False)
        elif keys[pygame.K_RIGHT]:
            self.facing_right = True
            self.image = self.base_image.copy()

    def draw(self, surface):
        """
        Draw the player to the specified surface.

        This method is responsible for drawing the player's image to the specified
        surface, taking into account the player's position, visibility, and gun
        (if any). If the game is in debug mode, it also draws a red rectangle
        around the player.

        :param surface: The surface on which to draw the player.
        :type surface: pygame.Surface
        :return: None
        """
        screen_pos = self.game.camera.apply(self)

        if self.visible:
            alpha = 255 if self.visible else 128
            self.image.set_alpha(alpha)
            surface.blit(self.image, screen_pos)

        if self.has_gun:
            if self.facing_right:
                gun_x = screen_pos.x + self.rect.width + 5
                gun_img = self.gun_image
            else:
                gun_x = screen_pos.x - 5 - self.gun_image.get_width()
                gun_img = pygame.transform.flip(self.gun_image, True, False)

            gun_y = (
                screen_pos.y + self.rect.height // 2 - self.gun_image.get_height() // 2
            )
            surface.blit(gun_img, (gun_x, gun_y))

        if self.game.debug_mode:
            pygame.draw.rect(surface, (255, 0, 0), screen_pos, 1)

    @cooldown(300)
    def jump(self):
        """
        Jump from the ground.

        If the player is on the ground, this method makes the player jump. If
        the player is on a ladder, it makes the player jump with the sticky jump
        power. The on_ground flag is set to False, the on_ladder_top flag is set
        to False, the in_ladder flag is set to False, and the current_ladder is
        set to None.
        """
        if self.platformtype == 3:
            self.vel_y = self.sticky_jump_power
        else:
            self.vel_y = self.jump_power
        self.on_ground = False
        self.on_ladder_top = False
        self.in_ladder = False
        self.current_ladder = None

    @cooldown(200)
    def shoot(self):
        """
        Shoot a projectile in the direction the player is facing.

        If the player does not have a gun, this method does nothing.

        :return: None
        """
        logger.info(f"Player shooting. Position: ({self.rect.centerx}, {self.rect.centery})")

        if not self.has_gun:
            logger.warning("Attempted to shoot without gun")
            return

        if self.facing_right:
            spawn_x = self.rect.centerx + 30
        else:
            spawn_x = self.rect.centerx - 30

        spawn_y = self.rect.centery
        direction = 1 if self.facing_right else -1

        projectile = Projectile(self.game, spawn_x, spawn_y, direction)
        print(f"Creating projectile at: ({spawn_x}, {spawn_y})")

        self.projectiles.add(projectile)
        self.game.all_sprites.add(projectile)
        print(
            f"Projectile groups: player={len(self.projectiles)}, game={len(self.game.all_sprites)}"
        )

    def apply_gravity(self):
        """
        Apply gravity to the player's vertical velocity.

        This method increases the player's vertical velocity by the gravity
        value unless the player is on a ladder and not moving downwards.
        The vertical velocity is capped at a maximum value of 10.
        """

        if not self.in_ladder or self.vel_y > 0:
            self.vel_y += self.gravity
            if self.vel_y > 10:
                self.vel_y = 10

    def move(self):
        """
        Move the player horizontally and vertically.

        This method moves the player's position according to the player's
        horizontal and vertical velocities. If the player is not on a ladder or
        is moving downwards, the player's y position is updated. If the player is
        not moving left or right and is not on a ladder, the player's horizontal
        velocity is set to 0.

        :return: None
        """
        self.rect.x += self.vel_x
        if not self.in_ladder or self.vel_y > 0:
            self.rect.y += self.vel_y

        keys = pygame.key.get_pressed()
        if (
            not keys[pygame.K_LEFT]
            and not keys[pygame.K_RIGHT]
            and self.platformtype != 4
        ):
            self.vel_x = 0

    def handle_platform_collision(self, platforms):
        """
        Handle collisions between the player and platforms.

        This method checks for collisions with various types of platforms such as
        TeleporterPlatform, LadderPlatform, DeadlyPlatform, and SlipperyPlatform.
        It adjusts the player's position and state based on the type of collision.

        If the player collides with a TeleporterPlatform, it teleports the player
        to the paired teleporter after a cooldown period. If the player collides
        with a LadderPlatform, it allows the player to climb the ladder. Collisions
        with DeadlyPlatform result in the player's death. SlipperyPlatform affects
        the player's movement speed.

        The method also handles setting the player's on_ground, in_ladder, and
        on_ladder_top flags, as well as adjusting the player's velocity based on
        collision overlaps.

        :param platforms: A list of platforms to check for collisions with.
        :type platforms: list
        :return: None
        """

        keys = pygame.key.get_pressed()
        was_in_ladder = self.in_ladder
        self.on_ground = False
        old_ladder = self.current_ladder

        for platform in platforms:
            if isinstance(platform, TeleporterPlatform):
                if self.rect.colliderect(platform.rect):
                    current_time = pygame.time.get_ticks()
                    if current_time - platform.last_teleport >= platform.cooldown:
                        for other in platforms:
                            if (
                                isinstance(other, TeleporterPlatform)
                                and other.pair_id == platform.pair_id
                                and other != platform
                            ):
                                self.vel_x = 0
                                self.vel_y = 0
                                self.rect.centerx = other.rect.centerx
                                self.rect.bottom = other.rect.top
                                platform.last_teleport = current_time
                                other.last_teleport = current_time
                                return
        touching_ladder = False
        for platform in platforms:
            if isinstance(platform, TeleporterPlatform):
                continue
            if isinstance(platform, LadderPlatform) and self.rect.colliderect(
                platform.rect
            ):
                if isinstance(platform, DeadlyPlatform):
                    self.game.handle_player_death()
                    break
                touching_ladder = True
                if not self.in_ladder:
                    self.rect.centerx = platform.rect.centerx
                self.in_ladder = True
                self.platformtype = 2
                self.current_ladder = platform
                break

        if not touching_ladder:
            self.in_ladder = False
            self.current_ladder = None
            self.on_ladder_top = False

        for platform in platforms:
            if isinstance(platform, TeleporterPlatform):
                if self.rect.colliderect(platform.rect):
                    current_time = pygame.time.get_ticks()
                    if current_time - platform.last_teleport >= platform.cooldown:
                        for other in platforms:
                            if (
                                isinstance(other, TeleporterPlatform)
                                and other.pair_id == platform.pair_id
                                and other != platform
                            ):
                                self.vel_x = 0
                                self.vel_y = 0
                                self.rect.centerx = other.rect.centerx
                                self.rect.bottom = other.rect.top
                                platform.last_teleport = current_time
                                other.last_teleport = current_time
                                return
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if isinstance(platform, TeleporterPlatform):
                    continue
                else:
                    overlap_left = self.rect.right - platform.rect.left
                    overlap_right = platform.rect.right - self.rect.left
                    overlap_top = self.rect.bottom - platform.rect.top
                    overlap_bottom = platform.rect.bottom - self.rect.top

                    min_overlap = min(
                        overlap_left, overlap_right, overlap_top, overlap_bottom
                    )

                    if isinstance(platform, LadderPlatform):
                        if min_overlap == overlap_top and self.vel_y >= 0:
                            self.on_ladder_top = True
                            if not keys[pygame.K_DOWN]:
                                self.rect.bottom = platform.rect.top
                                self.vel_y = 0
                                self.on_ground = True
                        continue

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
                    elif min_overlap == overlap_right and self.vel_x < 0:
                        self.rect.left = platform.rect.right
                        self.vel_x = 0

                    if not self.in_ladder:
                        if isinstance(platform, DeadlyPlatform):
                            self.game.handle_player_death()
                            return
                        elif isinstance(platform, SlipperyPlatform):
                            self.platformtype = 4
                        else:
                            self.platformtype = 1

    def handle_teleporter(self, platform, all_platforms):
        """
        Handle teleporting the player when they collide with a TeleporterPlatform.

        If the player has collided with a TeleporterPlatform and the cooldown period
        has passed, this method teleports the player to the paired teleporter.

        :param platform: The TeleporterPlatform that the player has collided with.
        :type platform: TeleporterPlatform
        :param all_platforms: The list of all platforms in the level.
        :type all_platforms: list
        :return: None
        """
        current_time = pygame.time.get_ticks()
        if current_time - platform.last_teleport >= platform.cooldown:
            for other in all_platforms:
                if (
                    isinstance(other, TeleporterPlatform)
                    and other.pair_id == platform.pair_id
                    and other != platform
                ):
                    self.vel_x = 0
                    self.vel_y = 0
                    self.rect.centerx = other.rect.centerx
                    self.rect.bottom = other.rect.top
                    platform.last_teleport = current_time
                    other.last_teleport = current_time
                    break

    def check_gun_collision(self, gun):
        """
        Check if the player has collided with a Gun object.

        :param gun: The Gun object to check for collision with.
        :type gun: Gun
        :return: True if the player has collided with the gun, False otherwise.
        """
        if pygame.sprite.collide_rect(self, gun):
            self.has_gun = True
            return True
        return False
