import pygame
import json
import os
from settings import *


class LevelEditor:
    def __init__(self):
        """
        Initializes the LevelEditor class.

        This constructor sets up the pygame environment, initializes the screen
        and clock, sets up camera controls, and loads level data. It also initializes
        various attributes for platform and enemy management, minimap, and user input handling.

        Attributes:
            screen (pygame.Surface): The display surface.
            clock (pygame.time.Clock): The clock object for managing frame rate.
            level_name (str): The name of the level being edited.
            camera_x (int): The x-coordinate of the camera.
            camera_y (int): The y-coordinate of the camera.
            zoom (float): The zoom level of the camera.
            camera_vel_x (float): The x-velocity of the camera.
            camera_vel_y (float): The y-velocity of the camera.
            camera_acceleration (float): The acceleration of the camera.
            camera_friction (float): The friction applied to the camera's movement.
            camera_max_speed (float): The maximum speed of the camera.
            minimap_size (int): The size of the minimap.
            minimap_margin (int): The margin size around the minimap.
            minimap_background (pygame.Surface): The background surface for the minimap.
            platform_types (list): The list of platform types available.
            current_type (int): The current platform type index.
            enemy_types (list): The list of enemy types available.
            current_enemy_type (int): The current enemy type index.
            selected_platform (dict): The currently selected platform.
            creating_platform (bool): Flag indicating if a platform is being created.
            dragging (bool): Flag indicating if a platform is being dragged.
            resizing (bool): Flag indicating if a platform is being resized.
            drag_start (tuple): The starting position of a drag action.
            platforms (list): The list of platforms in the level.
            world_width (int): The width of the world.
            world_height (int): The height of the world.
            player_spawn (tuple): The spawn position of the player.
            gun_spawn (tuple): The spawn position of the gun.
            enemy_spawns (list): The list of enemy spawn positions.
            font (pygame.font.Font): The font used for rendering text.
            colors (dict): The colors associated with each platform type.
            resize_handle_size (int): The size of the resize handles.
            handle_being_dragged (any): The handle currently being dragged.
            next_teleporter_id (int): The ID for the next teleporter.
            creating_teleporter_pair (bool): Flag indicating if a teleporter pair is being created.
            first_teleporter (any): The first teleporter in a pair.
        """

        pygame.init()
        self.screen = pygame.display.set_mode((EDITOR_WIDTH, EDITOR_HEIGHT))
        pygame.display.set_caption("Level Editor")
        self.clock = pygame.time.Clock()

        self.level_name = input("Enter the level name: ")
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0

        self.camera_vel_x = 0
        self.camera_vel_y = 0
        self.camera_acceleration = 0.5
        self.camera_friction = 0.9
        self.camera_max_speed = 15

        self.minimap_size = 200
        self.minimap_margin = 10
        self.minimap_background = pygame.Surface((self.minimap_size, self.minimap_size))
        self.minimap_background.fill((200, 200, 200))
        self.minimap_background.set_alpha(200)

        self.platform_types = [
            "Platform",
            "LadderPlatform",
            "DeadlyPlatform",
            "SlipperyPlatform",
            "TeleporterPlatform",
        ]
        self.current_type = 0
        self.enemy_types = ["GroundEnemy", "ShooterEnemy", "FlyingEnemy", "TankEnemy"]
        self.current_enemy_type = 0
        self.selected_platform = None
        self.creating_platform = False
        self.dragging = False
        self.resizing = False
        self.drag_start = None

        try:
            with open(f"{LEVEL_PATH}{self.level_name}.json", "r") as f:
                level_data = json.load(f)
                self.platforms = level_data["platforms"]
                self.world_width = level_data["world_width"]
                self.world_height = level_data["world_height"]
                self.player_spawn = level_data.get("player_spawn")
                self.gun_spawn = level_data.get("gun_spawn")
                self.enemy_spawns = level_data.get("enemy_spawns", [])

                if self.enemy_spawns and isinstance(self.enemy_spawns[0], list):
                    self.enemy_spawns = [
                        {
                            "type": self.enemy_types[i % len(self.enemy_types)],
                            "pos": spawn,
                        }
                        for i, spawn in enumerate(self.enemy_spawns)
                    ]
        except FileNotFoundError:
            self.world_width = int(input("Enter the world width: "))
            self.world_height = int(input("Enter the world height: "))
            self.platforms = []
            self.player_spawn = None
            self.gun_spawn = None
            self.enemy_spawns = []

        self.font = pygame.font.SysFont(None, 24)

        self.colors = {
            "Platform": (0, 0, 0),
            "LadderPlatform": (0, 255, 0),
            "DeadlyPlatform": (255, 0, 0),
            "SlipperyPlatform": (0, 0, 255),
            "TeleporterPlatform": (148, 0, 211),
        }

        self.resize_handle_size = RESIZE_HANDLE_SIZE
        self.handle_being_dragged = None
        self.next_teleporter_id = 0
        self.creating_teleporter_pair = False
        self.first_teleporter = None

    def get_resize_handles(self, plat):
        """
        Returns a dictionary of 4 pygame.Rects, representing the positions of the
        resize handles for the given platform. The keys of the dictionary are
        "top-left", "top-right", "bottom-left", and "bottom-right", indicating
        the position of the handle relative to the platform.
        """
        sx, sy = self.world_to_screen(plat["x"], plat["y"])
        w = plat["width"] * self.zoom
        h = plat["height"] * self.zoom

        return {
            "top-left": pygame.Rect(
                sx - self.resize_handle_size // 2,
                sy - self.resize_handle_size // 2,
                self.resize_handle_size,
                self.resize_handle_size,
            ),
            "top-right": pygame.Rect(
                sx + w - self.resize_handle_size // 2,
                sy - self.resize_handle_size // 2,
                self.resize_handle_size,
                self.resize_handle_size,
            ),
            "bottom-left": pygame.Rect(
                sx - self.resize_handle_size // 2,
                sy + h - self.resize_handle_size // 2,
                self.resize_handle_size,
                self.resize_handle_size,
            ),
            "bottom-right": pygame.Rect(
                sx + w - self.resize_handle_size // 2,
                sy + h - self.resize_handle_size // 2,
                self.resize_handle_size,
                self.resize_handle_size,
            ),
        }

    def world_to_screen(self, x, y):
        """
        Converts world coordinates to screen coordinates.

        This method translates the given world coordinates (x, y) to screen 
        coordinates based on the current camera position and zoom level.

        Parameters:
        x (int or float): The x-coordinate in the world space.
        y (int or float): The y-coordinate in the world space.

        Returns:
        tuple: A tuple (screen_x, screen_y) representing the coordinates on the screen.
        """

        screen_x = (x - self.camera_x) * self.zoom
        screen_y = (y - self.camera_y) * self.zoom
        return screen_x, screen_y

    def screen_to_world(self, x, y):
        """
        Converts screen coordinates to world coordinates.

        This method translates the given screen coordinates (x, y) to world
        coordinates based on the current camera position and zoom level.

        Parameters:
        x (int or float): The x-coordinate in the screen space.
        y (int or float): The y-coordinate in the screen space.

        Returns:
        tuple: A tuple (world_x, world_y) representing the coordinates in the world space.
        """
        world_x = x / self.zoom + self.camera_x
        world_y = y / self.zoom + self.camera_y
        return world_x, world_y

    def snap_to_grid(self, x, y):
        """
        Snaps the given coordinates to the grid.

        This method takes in coordinates and returns the closest coordinates
        that are aligned with the grid. The grid size is determined by the
        GRID_SIZE constant.

        Parameters:
        x (int or float): The x-coordinate to snap to the grid.
        y (int or float): The y-coordinate to snap to the grid.

        Returns:
        tuple: A tuple (snapped_x, snapped_y) representing the coordinates
        snapped to the grid.
        """
        return (round(x / GRID_SIZE) * GRID_SIZE, round(y / GRID_SIZE) * GRID_SIZE)

    def draw(self):
        """
        Draws the game state to the screen.

        This method is responsible for drawing the game state to the screen every
        frame. It draws all sprites, the player, the player's projectiles and the
        enemy projectiles. It also draws the debug information if the debug mode
        is enabled.

        :return: None
        """
        self.screen.fill((255, 255, 255))

        for x in range(0, self.world_width, GRID_SIZE):
            screen_x, _ = self.world_to_screen(x, 0)
            pygame.draw.line(
                self.screen, (200, 200, 200), (screen_x, 0), (screen_x, EDITOR_HEIGHT)
            )

        for y in range(0, self.world_height, GRID_SIZE):
            _, screen_y = self.world_to_screen(0, y)
            pygame.draw.line(
                self.screen, (200, 200, 200), (0, screen_y), (EDITOR_WIDTH, screen_y)
            )

        for i, plat in enumerate(self.platforms):
            screen_x, screen_y = self.world_to_screen(plat["x"], plat["y"])
            width = plat["width"] * self.zoom
            height = plat["height"] * self.zoom

            color = self.colors[plat["type"]]
            pygame.draw.rect(self.screen, color, (screen_x, screen_y, width, height))

            if plat == self.selected_platform:
                pygame.draw.rect(
                    self.screen, (255, 255, 0), (screen_x, screen_y, width, height), 2
                )

        drawn_pairs = set()
        for plat in self.platforms:
            if plat["type"] == "TeleporterPlatform":
                pair_id = plat.get("pair_id")
                if pair_id is not None and pair_id not in drawn_pairs:
                    for other in self.platforms:
                        if (
                            other["type"] == "TeleporterPlatform"
                            and other.get("pair_id") == pair_id
                            and other != plat
                        ):
                            start_x = plat["x"] + plat["width"] / 2
                            start_y = plat["y"] + plat["height"] / 2
                            end_x = other["x"] + other["width"] / 2
                            end_y = other["y"] + other["height"] / 2

                            start_screen_x, start_screen_y = self.world_to_screen(
                                start_x, start_y
                            )
                            end_screen_x, end_screen_y = self.world_to_screen(
                                end_x, end_y
                            )

                            pygame.draw.line(
                                self.screen,
                                (148, 0, 211),
                                (start_screen_x, start_screen_y),
                                (end_screen_x, end_screen_y),
                                2,
                            )
                            drawn_pairs.add(pair_id)
                            break

        for spawn in self.enemy_spawns:
            if isinstance(spawn, tuple) or isinstance(spawn, list):

                screen_x, screen_y = self.world_to_screen(*spawn)
                color = (200, 0, 0)
            else:
                screen_x, screen_y = self.world_to_screen(*spawn["pos"])
                color = {
                    "GroundEnemy": (200, 0, 0),
                    "ShooterEnemy": (200, 100, 0),
                    "FlyingEnemy": (200, 0, 100),
                    "TankEnemy": (100, 0, 200),
                }[spawn["type"]]

            pygame.draw.rect(
                self.screen, color, (int(screen_x) - 5, int(screen_y) - 5, 10, 10)
            )

        if self.selected_platform:
            handles = self.get_resize_handles(self.selected_platform)
            for handle in handles.values():
                pygame.draw.rect(self.screen, (255, 255, 0), handle)

        if self.gun_spawn:
            screen_x, screen_y = self.world_to_screen(*self.gun_spawn)
            pygame.draw.rect(
                self.screen,
                (255, 215, 0),
                (int(screen_x) - 5, int(screen_y) - 5, 10, 10),
            )

        if self.player_spawn:
            screen_x, screen_y = self.world_to_screen(*self.player_spawn)
            player_width = 40 * self.zoom
            player_height = 40 * self.zoom
            pygame.draw.rect(
                self.screen,
                (255, 0, 0),
                (
                    screen_x - player_width / 2,
                    screen_y - player_height / 2,
                    player_width,
                    player_height,
                ),
                2,
            )
        self.draw_text(
            f"Platform: {self.platform_types[self.current_type]}", (0, 0, 0), 10, 10
        )
        self.draw_text(f"Zoom: {self.zoom:.1f}", (0, 0, 0), 10, 30)
        self.draw_text("P: Set player spawn  I: Set gun spawn", (0, 0, 0), 10, 50)
        self.draw_text(
            f"Enemy Type: {self.enemy_types[self.current_enemy_type]}",
            (0, 0, 0),
            10,
            70,
        )

    def draw_text(self, text, color, x, y):
        """
        Draw text to the screen at the given position.

        :param text: The text to draw.
        :param color: The color of the text.
        :param x: The x-coordinate of the text.
        :param y: The y-coordinate of the text.
        :return: None
        """
        img = self.font.render(text, True, color)
        self.screen.blit(img, (x, y))

    def handle_input(self):
        """
        Handle all user input events.

        This method is responsible for capturing all user input events and
        performing the desired actions. It handles mouse clicks, mouse movement,
        key presses, and other events.

        :return: True if the editor should continue running, False if the user
            wants to quit.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    world_x, world_y = self.screen_to_world(*event.pos)

                    self.selected_platform = None
                    for plat in reversed(self.platforms):
                        if (
                            world_x >= plat["x"]
                            and world_x <= plat["x"] + plat["width"]
                            and world_y >= plat["y"]
                            and world_y <= plat["y"] + plat["height"]
                        ):
                            self.selected_platform = plat
                            self.drag_start = (world_x - plat["x"], world_y - plat["y"])
                            break

                    if self.platform_types[self.current_type] == "TeleporterPlatform":
                        if not self.creating_teleporter_pair:
                            x, y = self.snap_to_grid(world_x, world_y)
                            self.first_teleporter = {
                                "type": "TeleporterPlatform",
                                "x": x,
                                "y": y,
                                "width": 40,
                                "height": 60,
                                "color": self.colors["TeleporterPlatform"],
                                "pair_id": self.next_teleporter_id,
                            }
                            self.platforms.append(self.first_teleporter)
                            self.creating_teleporter_pair = True
                        else:
                            x, y = self.snap_to_grid(world_x, world_y)
                            second_teleporter = {
                                "type": "TeleporterPlatform",
                                "x": x,
                                "y": y,
                                "width": 40,
                                "height": 60,
                                "color": self.colors["TeleporterPlatform"],
                                "pair_id": self.next_teleporter_id,
                            }
                            self.platforms.append(second_teleporter)
                            self.next_teleporter_id += 1
                            self.creating_teleporter_pair = False
                            self.first_teleporter = None

                    if not self.selected_platform:
                        x, y = self.snap_to_grid(world_x, world_y)
                        initial_width = (
                            10
                            if self.platform_types[self.current_type]
                            == "LadderPlatform"
                            else GRID_SIZE
                        )
                        self.selected_platform = {
                            "type": self.platform_types[self.current_type],
                            "x": x,
                            "y": y,
                            "width": initial_width,
                            "height": 0,
                            "color": self.colors[
                                self.platform_types[self.current_type]
                            ],
                        }
                        self.platforms.append(self.selected_platform)
                        self.creating_platform = True

                if event.button in (4, 5):
                    old_world_x, old_world_y = self.screen_to_world(*event.pos)

                    old_zoom = self.zoom
                    if event.button == 4:
                        self.zoom = min(2.0, self.zoom * 1.1)
                    else:
                        self.zoom = max(0.5, self.zoom / 1.1)

                    screen_x, screen_y = event.pos
                    new_world_x = screen_x / self.zoom + self.camera_x
                    new_world_y = screen_y / self.zoom + self.camera_y

                    self.camera_x += old_world_x - new_world_x
                    self.camera_y += old_world_y - new_world_y

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.creating_platform:
                    if (
                        self.selected_platform["width"] == 0
                        or self.selected_platform["height"] == 0
                    ):
                        self.platforms.remove(self.selected_platform)
                    self.creating_platform = False
                self.dragging = False
                self.resizing = False

            elif event.type == pygame.MOUSEMOTION:
                world_x, world_y = self.screen_to_world(*event.pos)
                if self.creating_platform and self.selected_platform:
                    x, y = self.snap_to_grid(world_x, world_y)
                    if self.platform_types[self.current_type] != "LadderPlatform":
                        self.selected_platform["width"] = abs(
                            x - self.selected_platform["x"]
                        )
                    self.selected_platform["height"] = abs(
                        y - self.selected_platform["y"]
                    )

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    self.save_level()
                elif event.key == pygame.K_t:
                    self.current_type = (self.current_type + 1) % len(
                        self.platform_types
                    )
                elif event.key == pygame.K_p:
                    self.player_spawn = self.screen_to_world(*pygame.mouse.get_pos())
                elif event.key == pygame.K_i:
                    self.gun_spawn = self.screen_to_world(*pygame.mouse.get_pos())
                elif event.key == pygame.K_e:
                    self.enemy_spawns.append(
                        self.screen_to_world(*pygame.mouse.get_pos())
                    )
                elif event.key == pygame.K_r:
                    self.current_enemy_type = (self.current_enemy_type + 1) % len(
                        self.enemy_types
                    )
                elif event.key == pygame.K_e:
                    pos = self.screen_to_world(*pygame.mouse.get_pos())
                    self.enemy_spawns.append(
                        {"type": self.enemy_types[self.current_enemy_type], "pos": pos}
                    )
                elif event.key == pygame.K_DELETE:
                    if self.selected_platform:
                        try:
                            if self.selected_platform in self.platforms:
                                self.platforms.remove(self.selected_platform)
                            self.selected_platform = None
                        except ValueError:
                            print(
                                "Warning: Could not delete platform - not found in list"
                            )
                            self.selected_platform = None
                        else:
                            mouse_pos = pygame.mouse.get_pos()
                            world_pos = self.screen_to_world(*mouse_pos)
                            for spawn in self.enemy_spawns[:]:
                                if isinstance(spawn, dict):
                                    spawn_screen = self.world_to_screen(*spawn["pos"])
                                else:
                                    spawn_screen = self.world_to_screen(*spawn)

                                if (
                                    abs(spawn_screen[0] - mouse_pos[0]) < 10
                                    and abs(spawn_screen[1] - mouse_pos[1]) < 10
                                ):
                                    self.enemy_spawns.remove(spawn)
                                    break

            if event.type == pygame.MOUSEMOTION and event.buttons[1]:
                self.camera_x -= event.rel[0] / self.zoom
                self.camera_y -= event.rel[1] / self.zoom

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if self.selected_platform:
                    handles = self.get_resize_handles(self.selected_platform)
                    for handle_name, handle_rect in handles.items():
                        if handle_rect.collidepoint(event.pos):
                            self.handle_being_dragged = handle_name
                            return True

            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                pass

            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_being_dragged = None

            elif event.type == pygame.MOUSEMOTION:

                if self.handle_being_dragged and self.selected_platform:
                    world_x, world_y = self.screen_to_world(*event.pos)
                    x, y = self.snap_to_grid(world_x, world_y)

                    min_size = MIN_PLATFORM_SIZE

                    if self.platform_types[self.current_type] != "LadderPlatform":
                        if "right" in self.handle_being_dragged:
                            new_width = max(min_size, x - self.selected_platform["x"])
                            self.selected_platform["width"] = new_width
                        if "left" in self.handle_being_dragged:
                            old_right = (
                                self.selected_platform["x"]
                                + self.selected_platform["width"]
                            )
                            new_x = min(x, old_right - min_size)
                            self.selected_platform["x"] = new_x
                            self.selected_platform["width"] = old_right - new_x

                    if "bottom" in self.handle_being_dragged:
                        new_height = max(min_size, y - self.selected_platform["y"])
                        self.selected_platform["height"] = new_height
                    if "top" in self.handle_being_dragged:
                        old_bottom = (
                            self.selected_platform["y"]
                            + self.selected_platform["height"]
                        )
                        new_y = min(y, old_bottom - min_size)
                        self.selected_platform["y"] = new_y
                        self.selected_platform["height"] = old_bottom - new_y
                elif (
                    self.selected_platform
                    and event.buttons[0]
                    and not self.creating_platform
                ):
                    world_x, world_y = self.screen_to_world(*event.pos)
                    x, y = self.snap_to_grid(
                        world_x - self.drag_start[0], world_y - self.drag_start[1]
                    )
                    self.selected_platform["x"] = x
                    self.selected_platform["y"] = y

        return True

    def update_camera(self):
        """
        Update the camera's state for the current frame.

        This method updates the camera's velocity and position based on the current
        state of the arrow keys. The camera's velocity is accelerated/decelerated
        based on the camera's acceleration, and the camera's position is updated
        based on the velocity and friction.

        The camera's velocity is limited to a maximum speed, and the camera's
        position is limited to the boundaries of the level. The camera's position
        is also adjusted based on the current zoom level.

        :return: None
        """
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.camera_vel_x -= self.camera_acceleration
        if keys[pygame.K_RIGHT]:
            self.camera_vel_x += self.camera_acceleration
        if keys[pygame.K_UP]:
            self.camera_vel_y -= self.camera_acceleration
        if keys[pygame.K_DOWN]:
            self.camera_vel_y += self.camera_acceleration

        self.camera_vel_x = max(
            -self.camera_max_speed, min(self.camera_max_speed, self.camera_vel_x)
        )
        self.camera_vel_y = max(
            -self.camera_max_speed, min(self.camera_max_speed, self.camera_vel_y)
        )

        self.camera_vel_x *= self.camera_friction
        self.camera_vel_y *= self.camera_friction
        self.camera_x += self.camera_vel_x / self.zoom
        self.camera_y += self.camera_vel_y / self.zoom

    def draw_minimap(self):
        """
        Draws the minimap displaying the level layout and camera view.

        This function renders a minimap at the bottom-left corner of the screen,
        showing a scaled-down view of the level's platforms. It also outlines the
        current camera view within the minimap.

        The minimap's dimensions are determined by the minimap size and the aspect
        ratio of the level. Platforms are drawn proportionally, and the camera's
        view is represented by a red rectangle.

        :return: None
        """

        max_size = self.minimap_size
        world_aspect = self.world_width / self.world_height

        if world_aspect > 1:
            minimap_width = max_size
            minimap_height = max_size / world_aspect
        else:
            minimap_height = max_size
            minimap_width = max_size * world_aspect

        minimap_x = self.minimap_margin
        minimap_y = EDITOR_HEIGHT - self.minimap_margin - minimap_height

        self.minimap_background = pygame.Surface((minimap_width, minimap_height))
        self.minimap_background.fill((200, 200, 200))
        self.minimap_background.set_alpha(200)
        self.screen.blit(self.minimap_background, (minimap_x, minimap_y))

        scale_x = minimap_width / self.world_width
        scale_y = minimap_height / self.world_height

        for plat in self.platforms:
            mini_x = minimap_x + plat["x"] * scale_x
            mini_y = minimap_y + plat["y"] * scale_y
            mini_w = max(1, plat["width"] * scale_x)
            mini_h = max(1, plat["height"] * scale_y)
            pygame.draw.rect(
                self.screen, plat["color"], (mini_x, mini_y, mini_w, mini_h)
            )

        view_x = minimap_x + (self.camera_x * scale_x)
        view_y = minimap_y + (self.camera_y * scale_y)
        view_w = (EDITOR_WIDTH / self.zoom) * scale_x
        view_h = (EDITOR_HEIGHT / self.zoom) * scale_y
        pygame.draw.rect(self.screen, (255, 0, 0), (view_x, view_y, view_w, view_h), 1)

        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            (minimap_x, minimap_y, minimap_width, minimap_height),
            1,
        )

    def save_level(self):
            """
            Saves the current level to a JSON file.

            This method saves the current level by saving the level's platforms, world size,
            player and gun spawn positions, and enemy spawn positions and types to a
            JSON file. The file is saved in the directory specified by the LEVEL_PATH
            constant, with the filename being the level name followed by the ".json"
            extension.

            :return: None
            """
            processed_spawns = []
            processed_types = []

            for spawn in self.enemy_spawns:
                if isinstance(spawn, dict):
                    processed_spawns.append(spawn["pos"])
                    processed_types.append(spawn["type"])
                else:
                    processed_spawns.append(spawn)
                    processed_types.append(self.enemy_types[self.current_enemy_type])

            level_data = {
                "platforms": self.platforms,
                "world_width": self.world_width,
                "world_height": self.world_height,
                "player_spawn": self.player_spawn,
                "gun_spawn": self.gun_spawn,
                "enemy_spawns": processed_spawns,
                "enemy_types": processed_types,
            }

            filepath = f"{LEVEL_PATH}{self.level_name}.json"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(level_data, f, indent=4)
            print(f"Level saved to {filepath}")

    def run(self):
        """
        Runs the main loop of the level editor.

        This method is responsible for handling input events, updating the camera, drawing the
        level editor screen, drawing the minimap, and controlling the frame rate of the
        editor. It loops until the user closes the window.

        :return: None
        """
        running = True
        while running:
            running = self.handle_input()
            self.update_camera()
            self.draw()
            self.draw_minimap()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()
