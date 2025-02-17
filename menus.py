import pygame
from settings import *
import json


class Menu:
    def __init__(self, game):
        """
        Initialize a Menu instance.

        :param game: The current game instance.
        :type game: Game
        """
        self.game = game
        self.mid_w = WIDTH // 2
        self.mid_h = HEIGHT // 2
        self.font = pygame.font.Font(None, 40)
        self.selected_option = 0
        self.sound_manager = game.sound_manager

    def draw_text(self, text, size, x, y, color=(255, 255, 255)):
        """
        Draw a given text to the screen at the specified position.

        :param text: The text to draw.
        :param size: The font size to use.
        :param x: The x-coordinate of the text.
        :param y: The y-coordinate of the text.
        :param color: The color of the text, defaults to (255, 255, 255).
        :return: None
        """
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.game.screen.blit(text_surface, text_rect)


class MainMenu(Menu):
    def __init__(self, game):
        """
        Initialize a MainMenu instance.

        :param game: The current game instance.
        :type game: Game
        """
        super().__init__(game)
        self.options = ["Play", "Level Select", "Settings", "Quit"]

    def draw(self):
        """
        Draw the main menu on the screen.

        This will draw the title, and each of the options in the menu with a gold highlight
        if the option is selected, or a white highlight if the option is not selected.

        :return: None
        """
        self.game.screen.fill((0, 0, 0))
        self.draw_text("SIGMA TURTLE", 60, self.mid_w, self.mid_h - 100)

        for i, option in enumerate(self.options):
            color = GOLD if i == self.selected_option else WHITE
            self.draw_text(option, 40, self.mid_w, self.mid_h + i * 50, color)

    def handle_input(self):
        """
        Handle all user input events.

        This method is responsible for capturing all user input events and
        performing the desired actions. It handles mouse clicks, mouse movement,
        key presses, and other events.

        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.options[self.selected_option] == "Play":
                        self.game.state = "playing"
                    elif self.options[self.selected_option] == "Level Select":
                        self.game.level_select.refresh_levels()
                        self.game.state = "level_select"
                    elif self.options[self.selected_option] == "Settings":
                        self.game.state = "settings"
                    elif self.options[self.selected_option] == "Quit":
                        self.game.running = False
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(
                        self.options
                    )
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(
                        self.options
                    )


class LevelSelectMenu(Menu):
    def __init__(self, game):
        """
        Initialize a LevelSelectMenu instance.

        :param game: The current game instance.
        :type game: Game
        """
        super().__init__(game)
        self.refresh_levels()

    def refresh_levels(self):
        """
        Refresh the list of available levels.

        This method will fetch the list of available levels and store them in the options
        list. If there are no levels found, or if there is an error loading the levels, it
        will display an appropriate error message.

        :return: None
        """
        try:
            self.options = self.game.get_available_levels()
            if not self.options:
                self.options = ["No levels found"]
            self.selected_option = 0
        except Exception as e:
            print(f"Error refreshing levels: {e}")
            self.options = ["Error loading levels"]
            self.selected_option = 0

    def draw(self):
        """
        Draw the level select menu on the screen.

        This will draw the title, and each of the options in the menu with a gold highlight
        if the option is selected, or a white highlight if the option is not selected. If there
        are no levels found, or if there is an error loading the levels, it will display an
        appropriate error message.

        :return: None
        """
        try:
            self.game.screen.fill((0, 0, 0))
            self.draw_text("SELECT LEVEL", 60, self.mid_w, 100)

            if self.options[0] in ["No levels found", "Error loading levels"]:
                self.draw_text(self.options[0], 40, self.mid_w, self.mid_h)
                self.draw_text("Press ESC to return", 30, self.mid_w, self.mid_h + 50)
                return

            start_y = 200
            visible_options = 6
            scroll_offset = (self.selected_option // visible_options) * visible_options

            for i in range(
                scroll_offset, min(scroll_offset + visible_options, len(self.options))
            ):
                color = GOLD if i == self.selected_option else WHITE
                self.draw_text(
                    self.options[i],
                    40,
                    self.mid_w,
                    start_y + (i - scroll_offset) * 50,
                    color,
                )

            if scroll_offset > 0:
                self.draw_text("/\\", 40, self.mid_w, start_y - 40)
            if scroll_offset + visible_options < len(self.options):
                self.draw_text("\\/", 40, self.mid_w, start_y + visible_options * 50)
        except Exception as e:
            print(f"Error drawing level select: {e}")
            self.game.state = "main_menu"

    def handle_input(self):
        """
        Handle all user input events.

        This method is responsible for capturing all user input events and
        performing the desired actions. It handles mouse clicks, mouse movement,
        key presses, and other events.

        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.state = "main_menu"
                elif self.options[0] not in ["No levels found", "Error loading levels"]:
                    if event.key == pygame.K_RETURN:
                        try:
                            self.game.current_level = self.options[self.selected_option]
                            self.game.reset_level()
                            self.game.state = "playing"
                        except Exception as e:
                            print(f"Error loading level: {e}")
                            self.game.state = "main_menu"
                    elif event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(
                            self.options
                        )
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(
                            self.options
                        )


class PauseMenu(Menu):

    def __init__(self, game):
        """
        Initialize a PauseMenu instance.

        :param game: The current game instance.
        :type game: Game
        """
        super().__init__(game)
        self.options = ["Resume", "Restart Level", "Settings", "Main Menu"]

    def draw(self):
        """
        Draw the pause menu on the screen.

        This will draw a black overlay with 50% opacity, and then draw the title and
        each of the options in the menu with a gold highlight if the option is selected,
        or a white highlight if the option is not selected.

        :return: None
        """
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.game.screen.blit(overlay, (0, 0))

        self.draw_text("PAUSED", 60, self.mid_w, self.mid_h - 100)

        for i, option in enumerate(self.options):
            color = GOLD if i == self.selected_option else WHITE
            self.draw_text(option, 40, self.mid_w, self.mid_h + i * 50, color)

    def handle_input(self):
        """
        Handle all user input events.

        This method is responsible for capturing all user input events and
        performing the desired actions. It handles mouse clicks, mouse movement,
        key presses, and other events.

        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.state = "playing"
                elif event.key == pygame.K_RETURN:
                    if self.options[self.selected_option] == "Resume":
                        self.game.state = "playing"
                    elif self.options[self.selected_option] == "Restart Level":
                        self.game.reset_level()
                    elif self.options[self.selected_option] == "Settings":
                        self.game.state = "settings"
                    elif self.options[self.selected_option] == "Main Menu":
                        self.game.state = "main_menu"
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(
                        self.options
                    )
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(
                        self.options
                    )


class SettingsMenu(Menu):
    def __init__(self, game):
        """
        Initialize the SettingsMenu class.

        This constructor sets up the options for the settings menu, loads the
        current settings from file, and applies them to the game.

        :param game: The Game object that this menu is a part of.
        :type game: Game
        """
        super().__init__(game)
        self.options = [
            "Music Volume: {}%",
            "Sound Volume: {}%",
            "Display: {}",
            "Debug Mode: {}",
            "Back",
        ]
        self.settings = self.load_settings()
        self.apply_settings()

    def apply_settings(self):
        """
        Apply the current settings to the game.

        This method updates the game's sound volume, debug mode, and display mode 
        based on the current settings. It adjusts the music volume according to the 
        'music_volume' setting, toggles the game's debug mode based on the 'debug' 
        setting, and sets the display mode to fullscreen or windowed based on the 
        'fullscreen' setting.
        
        :return: None
        """

        self.sound_manager.set_music_volume(self.settings["music_volume"] / 100.0)
        self.game.debug_mode = self.settings["debug"]
        if self.settings["fullscreen"]:
            pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((WIDTH, HEIGHT))

    def load_settings(self):
        """
        Load the current settings from a JSON file.

        This method attempts to load the settings from "settings.json". If the file
        does not exist, it returns a dictionary with default settings.

        :return: A dictionary containing the current settings.
        :rtype: Dict[str, Union[int, bool]]
        """

        try:
            with open("settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "music_volume": 100,
                "sound_volume": 100,
                "fullscreen": False,
                "debug": False,
            }

    def save_settings(self):
        """
        Save the current settings to a JSON file.

        This method saves the current settings to a file named "settings.json" in
        the current working directory. If the file already exists, it will be
        overwritten.

        :return: None
        """
        with open("settings.json", "w") as f:
            json.dump(self.settings, f, indent=4)

    def draw(self):
        """
        Draw the settings menu to the screen.

        This method is responsible for drawing the settings menu to the screen every
        frame. It draws the title, options, and a selected option indicator.

        :return: None
        """
        self.game.screen.fill((0, 0, 0))
        self.draw_text("SETTINGS", 60, self.mid_w, 100)

        display_mode = "Fullscreen" if self.settings["fullscreen"] else "Windowed"
        debug_status = "On" if self.settings["debug"] else "Off"
        formatted_options = [
            self.options[0].format(self.settings["music_volume"]),
            self.options[1].format(self.settings["sound_volume"]),
            self.options[2].format(display_mode),
            self.options[3].format(debug_status),
            self.options[4],
        ]

        for i, option in enumerate(formatted_options):
            color = GOLD if i == self.selected_option else WHITE
            self.draw_text(option, 40, self.mid_w, 200 + i * 50, color)

    def update_music_volume(self, volume):
        """
        Update the music volume in the sound manager.

        This method adjusts the music volume based on the given percentage
        value. The volume is expected to be in the range of 0 to 100, and is
        converted to a range of 0.0 to 1.0 before being set in the sound manager.

        :param volume: The desired music volume as a percentage (0-100).
        :type volume: int
        :return: None
        """

        self.sound_manager.set_volume(volume / 100.0)

    def handle_input(self):
        """
        Handle game events.

        This method checks for pygame events such as QUIT, KEYDOWN, and UP. If the event
        type is QUIT, the game's running status is set to False. If the event type is
        KEYDOWN, it updates the selected option based on the key pressed. If the key is
        ESCAPE or RETURN when the selected option is the last one, it saves the current
        settings to file, applies them to the game, and sets the game's state to "main_menu".
        If the key is UP or DOWN, it updates the selected option accordingly. If the key is
        LEFT or RIGHT, it updates the music volume, sound volume, display mode, or debug mode
        based on the selected option.

        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or (
                    event.key == pygame.K_RETURN
                    and self.selected_option == len(self.options) - 1
                ):
                    self.save_settings()
                    self.apply_settings()
                    self.game.state = "main_menu"
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(
                        self.options
                    )
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(
                        self.options
                    )
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    if self.selected_option == 0:
                        change = -10 if event.key == pygame.K_LEFT else 10
                        self.settings["music_volume"] = max(
                            0, min(100, self.settings["music_volume"] + change)
                        )
                        self.sound_manager.set_music_volume(
                            self.settings["music_volume"] / 100.0
                        )

                    elif self.selected_option == 1:
                        change = -10 if event.key == pygame.K_LEFT else 10
                        self.settings["sound_volume"] = max(
                            0, min(100, self.settings["sound_volume"] + change)
                        )

                    elif self.selected_option == 2:
                        self.settings["fullscreen"] = not self.settings["fullscreen"]
                        if self.settings["fullscreen"]:
                            pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                        else:
                            pygame.display.set_mode((WIDTH, HEIGHT))

                    elif self.selected_option == 3:
                        self.settings["debug"] = not self.settings["debug"]
                        self.game.debug_mode = self.settings["debug"]


class GameOverMenu(Menu):
    def __init__(self, game):
        """
        Initialize the GameOverMenu class.

        This constructor sets up the options for the game over menu.

        :param game: The Game object that this menu is a part of.
        :type game: Game
        """
        super().__init__(game)
        self.options = ["Restart Level", "Main Menu"]

    def draw(self, surface):
        """
        Draw the game over menu on the screen.

        This method is responsible for drawing the game over menu to the screen every
        frame. It draws the title, options, and a selected option indicator.

        :param surface: The surface to draw on.
        :type surface: pygame.Surface
        :return: None
        """
        surface.fill((0, 0, 0))
        self.draw_text("GAME OVER", 60, self.mid_w, self.mid_h - 100, (255, 0, 0))

        for i, option in enumerate(self.options):
            color = GOLD if i == self.selected_option else WHITE
            self.draw_text(option, 40, self.mid_w, self.mid_h + i * 50, color)

    def handle_input(self):
        """
        Handle all user input events.

        This method is responsible for capturing all user input events and
        performing the desired actions. It handles mouse clicks, mouse movement,
        key presses, and other events.

        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.options[self.selected_option] == "Restart Level":
                        self.game.reset_level()
                    elif self.options[self.selected_option] == "Main Menu":
                        self.game.state = "main_menu"
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(
                        self.options
                    )
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(
                        self.options
                    )
