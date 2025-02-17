import pygame
from settings import *
from player import Player
from platforms import (
    Platform,
    LadderPlatform,
    DeadlyPlatform,
    SlipperyPlatform,
    TeleporterPlatform,
)
from camera import Camera
from gun import Gun
from enemy import GroundEnemy, FlyingEnemy, ShooterEnemy, TankEnemy, Enemy
from menus import MainMenu, PauseMenu, LevelSelectMenu, SettingsMenu, GameOverMenu
from sound_manager import SoundManager
import json
import os
import math
from debug_logger import logger
import time


class Game:
    def __init__(self):
        """
        Initialize the game.

        Initialize pygame, set up display, clock, and game state. Load the first level and
        create the main menu, pause menu, settings menu, level select menu, and game over menu.

        :return: None
        """
        logger.info("Initializing game...")
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2D Platformer")
        self.clock = pygame.time.Clock()
        self.running = True
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.gun = None
        self.current_level = LEVEL_PATH + "ene.json"
        self.load_level(self.current_level)
        self.available_levels = self.get_available_levels()
        self.camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
        self.debug_mode = False
        self.state = "main_menu"

        self.sound_manager = SoundManager()
        self.main_menu = MainMenu(self)
        self.pause_menu = PauseMenu(self)
        self.settings_menu = SettingsMenu(self)
        self.level_select = LevelSelectMenu(self)
        self.game_over_menu = GameOverMenu(self)

        self.sound_manager.load_music("menu")
        self.sound_manager.play_music("menu", -1)
        logger.success("Game initialized successfully")
        self.frame_count = 0
        self.last_fps_check = time.time()
        self.fps_history = []

    def start_background_music(self):
        """
        Start the background music for the current state.

        If sound is enabled, this will load and play the music for the current state.

        :return: None
        """
        if self.sound_manager.sound_enabled:
            self.sound_manager.load_music("menu")
            self.sound_manager.play_music("menu", -1)

    def reset_level(self):
        """
        Reset the current level.

        This will clear all sprites, load the current level again, and set the game state to "playing".
        This is used when the player dies, and is also used when the user selects a new level from the level select menu.

        :return: None
        """
        self.all_sprites.empty()
        self.platforms.empty()
        if hasattr(self, "enemies"):
            self.enemies.empty()

        self.load_level(self.current_level)
        self.state = "playing"

    def handle_player_death(self):
        """
        Handle the player's death.

        When the player's health reaches 0, this is called to reset the game state to "game_over".
        This is currently called in the Player class's update method, but may be called elsewhere in the future.

        :return: None
        """
        self.state = "game_over"

    def get_available_levels(self):
        """
        Get a list of all available levels in the levels directory.

        :return: A sorted list of file paths to the available levels.
        """
        levels = []
        for file in os.listdir(LEVEL_PATH):
            if file.endswith(".json") and file != "settings.json":
                levels.append(LEVEL_PATH + file)
        return sorted(levels)

    def load_level(self, level_file):
        """
        Load a level from a JSON file.

        This method will load all the platform, player, and enemy information from the
        given JSON file and create the necessary objects. It will also clear the current
        level of enemies and platforms.

        :param level_file: The path to the JSON file containing the level information.
        :type level_file: str
        :return: None
        """
        start_time = time.time()
        logger.info(f"Loading level: {level_file}")
        with open(level_file, "r") as f:
            level_data = json.load(f)

        self.enemies.empty()
        self.enemy_projectiles.empty()

        if "enemy_spawns" in level_data:
            enemy_types_dict = {
                "GroundEnemy": GroundEnemy,
                "ShooterEnemy": ShooterEnemy,
                "FlyingEnemy": FlyingEnemy,
                "TankEnemy": TankEnemy,
            }

            enemy_spawns = level_data["enemy_spawns"]
            enemy_types = level_data.get("enemy_types", [])

            for spawn_pos, enemy_type in zip(enemy_spawns, enemy_types):
                if enemy_type in enemy_types_dict:
                    enemy = enemy_types_dict[enemy_type](
                        self, spawn_pos[0], spawn_pos[1]
                    )
                    self.all_sprites.add(enemy)
                    self.enemies.add(enemy)

        self.world_width = level_data.get("world_width", WORLD_WIDTH)
        self.world_height = level_data.get("world_height", WORLD_HEIGHT)
        player_spawn = level_data.get("player_spawn", (WIDTH // 2, HEIGHT // 2))

        self.player = Player(self, player_spawn)
        self.all_sprites.add(self.player)

        if level_data.get("gun_spawn"):
            x, y = level_data["gun_spawn"]
            self.gun = Gun(x, y)
            self.all_sprites.add(self.gun)

        platform_classes = {
            "Platform": Platform,
            "LadderPlatform": LadderPlatform,
            "DeadlyPlatform": DeadlyPlatform,
            "SlipperyPlatform": SlipperyPlatform,
            "TeleporterPlatform": TeleporterPlatform,
        }

        for plat in level_data["platforms"]:
            platform_class = platform_classes[plat["type"]]
            x, y, width, height = plat["x"], plat["y"], plat["width"], plat["height"]
            if width > 0 and height > 0:
                platform = platform_class(x, y, width, height)
                if plat["type"] == "TeleporterPlatform":
                    platform = platform_class(
                        x, y, width, height, plat.get("pair_id", 0)
                    )
                else:
                    platform = platform_class(x, y, width, height)
                self.all_sprites.add(platform)
                self.platforms.add(platform)
        logger.log_performance("Level load", start_time)
        logger.success(f"Level loaded successfully: {level_file}")

    def run(self):
        """
        Run the main game loop.

        This method is responsible for executing the main loop of the game.
        It manages the game state transitions and updates the game logic,
        including input handling, updating game entities, and rendering the
        game screen based on the current state. It also controls the
        background music based on the game state.

        The game loop runs continuously until the 'running' attribute is
        set to False. It uses a clock to manage the frame rate and updates
        the display at the end of each loop iteration.
        """

        last_state = None
        while self.running:
            self.clock.tick(FPS)

            if self.state != last_state:
                if self.state == "playing":
                    self.sound_manager.play_music("game", -1)
                elif self.state in [
                    "main_menu",
                    "pause",
                    "game_over",
                    "level_select",
                    "settings",
                ]:
                    self.sound_manager.play_music("menu", -1)
                last_state = self.state

            if self.state == "main_menu":
                self.main_menu.handle_input()
                self.main_menu.draw()
            elif self.state == "level_select":
                self.level_select.handle_input()
                self.level_select.draw()
            elif self.state == "settings":
                self.settings_menu.handle_input()
                self.settings_menu.draw()
            elif self.state == "pause":
                self.pause_menu.handle_input()
                self.pause_menu.draw()
            elif self.state == "playing":
                self.events()
                self.update()
                self.draw()
            elif self.state == "game_over":
                self.game_over_menu.draw(self.screen)
                self.game_over_menu.handle_input()

            pygame.display.flip()

    def update(self):
        """
        Update the game state.

        This method is responsible for updating the game state every frame. It updates all sprites, moves the camera, handles player-platform collisions, player-enemy collisions, projectile-platform collisions, projectile-enemy collisions and updates the player's projectiles.

        The method also checks for player death and kills the player if necessary.

        :return: None
        """
        if self.debug_mode:
            start_time = time.time()
            logger.start_profiling()
        self.all_sprites.update()
        self.camera.update(self.player)

        for platform in self.platforms:
            if isinstance(
                platform, TeleporterPlatform
            ) and self.player.rect.colliderect(platform.rect):
                self.player.handle_teleporter(platform, self.platforms)
                return

        self.enemy_projectiles.update()

        for enemy in self.enemies:
            if enemy.rect.colliderect(self.player.rect):
                current_time = pygame.time.get_ticks()
                if (
                    not self.player.is_invulnerable_to(enemy)
                    and current_time - enemy.last_damage_time >= enemy.damage_cooldown
                ):
                    enemy.last_damage_time = current_time
                    self.player.take_damage(10, enemy)
                    if self.player.health <= 0:
                        self.handle_player_death()
                        return

        for projectile in self.enemy_projectiles:
            if projectile.rect.colliderect(self.player.rect):
                if not self.player.is_invulnerable_to(projectile):
                    self.player.take_damage(projectile.damage, projectile)
                    projectile.kill()
                    if self.player.health <= 0:
                        self.handle_player_death()
                        return

        hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
        if self.player.platformtype != 2:
            self.player.ladder_y = self.player.rect.bottom
            self.player.platformtype = 0

        if hits:
            self.player.handle_platform_collision(hits)
            if self.gun and self.player.check_gun_collision(self.gun):
                self.gun.kill()
                self.gun = None

        for projectile in self.player.projectiles:
            if projectile.check_collisions(self.platforms):
                continue

            hit_enemy = None
            min_distance = float("inf")

            for enemy in self.enemies:
                if projectile.rect.colliderect(enemy.rect):
                    dx = enemy.rect.centerx - projectile.rect.centerx
                    dy = enemy.rect.centery - projectile.rect.centery
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < min_distance:
                        min_distance = distance
                        hit_enemy = enemy

            if hit_enemy:
                hit_enemy.take_damage(projectile.damage)
                projectile.kill()

        self.player.projectiles.update()
        self.log_game_state()
        if self.debug_mode:
            logger.stop_profiling()
            logger.log_performance("Game update", start_time)

    def events(self):
        """
        Handle game events.

        This method checks for pygame events such as QUIT or KEYDOWN. If the event
        type is QUIT, the game's running status is set to False. If the event type is
        KEYDOWN, it checks if the key is ESCAPE and if so, sets the game's state to
        "pause". If the key is 'c', it toggles the debug mode.

        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "pause"
                elif event.key == pygame.K_c:
                    self.debug_mode = not self.debug_mode

    def draw(self):
        """
        Draw the game state to the screen.

        This method is responsible for drawing the game state to the screen every
        frame. It draws all sprites, the player, the player's projectiles and the
        enemy projectiles. It also draws the debug information if the debug mode
        is enabled.

        :return: None
        """
        if self.debug_mode:
            start_time = time.time()
        self.screen.fill(SKY_BLUE)

        for sprite in self.all_sprites:
            if sprite != self.player:
                self.screen.blit(sprite.image, self.camera.apply(sprite))
                if isinstance(sprite, Enemy):
                    sprite.draw_health_bar(self.screen, self.camera)

        for projectile in self.enemy_projectiles:
            self.screen.blit(projectile.image, self.camera.apply(projectile))

        player_pos = self.camera.apply(self.player)
        self.player.draw(self.screen)
        self.player.draw_health_bar(self.screen)

        if self.debug_mode:
            self.draw_debug_info()

        pygame.display.flip()
        if self.debug_mode:
            logger.log_performance("Frame render", start_time)

    def draw_debug_info(self):
        """
        Draw debug information to the screen.

        This method is responsible for drawing debug information to the screen
        every frame. It draws the player's position, velocity, on ground status, in
        ladder status, platform type, camera position, exited sides, FPS, debug
        mode, player ladder y, player current ladder, player on ladder top, facing
        right, player projectiles, gun, gun position, enemies, state, current
        level, available levels, world width, world height and player frame.

        :return: None
        """
        font = pygame.font.SysFont(None, DEBUG_FONT_SIZE)
        debug_info = [
            f"Player X: {self.player.rect.x}",
            f"Player Y: {self.player.rect.y}",
            f"Velocity X: {self.player.vel_x}",
            f"Velocity Y: {self.player.vel_y}",
            f"On Ground: {self.player.on_ground}",
            f"In Ladder: {self.player.in_ladder}",
            f"Platform Type: {self.player.platformtype}",
            f"Camera X: {self.camera.x}",
            f"Camera Y: {self.camera.y}",
            f"Exited Top: {self.camera.exited_top}",
            f"Exited Bottom: {self.camera.exited_bottom}",
            f"Exited Left: {self.camera.exited_left}",
            f"Exited Right: {self.camera.exited_right}",
            f"FPS: {self.clock.get_fps()}",
            f"Debug Mode: {self.debug_mode}",
            f"Player Ladder Y: {self.player.ladder_y}",
            f"Player Current Ladder: {self.player.current_ladder}",
            f"Player On Ladder Top: {self.player.on_ladder_top}",
            f"Facing Right: {self.player.facing_right}",
            f"Player Projectiles: {len(self.player.projectiles)}",
            f"Gun: {self.gun is not None}",
            f"Gun X: {self.gun.rect.x if self.gun else None}",
            f"Gun Y: {self.gun.rect.y if self.gun else None}",
            f"Enemies: {len(self.enemies)}",
            f"State: {self.state}",
            f"Current Level: {self.current_level}",
            f"Available Levels: {self.available_levels}",
            f"World Width: {self.world_width}",
            f"World Height: {self.world_height}",
            f"Player Frame: {self.player.current_frame}",
        ]
        for i, info in enumerate(debug_info):
            text_surface = font.render(info, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, 10 + i * 20))

    def log_game_state(self):
        """Log current game state information"""
        logger.info(f"Current state: {self.state}", "GameState")
        logger.track_entity("Sprites", len(self.all_sprites))
        logger.track_entity("Platforms", len(self.platforms))
        logger.track_entity("Enemies", len(self.enemies))
        logger.track_entity("Projectiles", len(self.enemy_projectiles))
        
        current_time = time.time()
        self.frame_count += 1
        if current_time - self.last_fps_check >= 1.0:
            fps = self.frame_count / (current_time - self.last_fps_check)
            self.fps_history.append(fps)
            if len(self.fps_history) > 10:
                self.fps_history.pop(0)
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            logger.info(f"FPS: {fps:.1f} (avg: {avg_fps:.1f})", "Performance")
            self.frame_count = 0
            self.last_fps_check = current_time

    def quit(self):
        """
        Quit the game.

        This method is responsible for quitting the game. It calls
        pygame.quit() to uninitialize all pygame modules and
        quit the game.

        :return: None
        """
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
    game.quit()
