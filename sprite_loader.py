import pygame
import json
import os


class SpriteLoader:
    def __init__(self):
        """
        Initialize the SpriteLoader.
        
        Load the spritesheet image and associated JSON data from the "assets/sprites" directory.
        If the file is not found or JSON data is malformed, fall back to a default red square.

        :raises FileNotFoundError: If the spritesheet or JSON file is not found.
        :raises KeyError: If the JSON file does not contain 'frames' data.
        """
        try:
            spritesheet_path = os.path.join("assets", "sprites", "spritesheet.png")
            json_path = os.path.join("assets", "sprites", "spritesheet.json")

            if not os.path.exists(spritesheet_path):
                raise FileNotFoundError(f"Spritesheet not found at {spritesheet_path}")
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"JSON data not found at {json_path}")

            self.spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
            with open(json_path, "r") as f:
                self.sprite_data = json.load(f)

            if "frames" not in self.sprite_data:
                raise KeyError("No 'frames' data in spritesheet JSON")

            self.sprite_cache = {}

        except Exception as e:
            print(f"Error initializing SpriteLoader: {e}")
            self.spritesheet = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.spritesheet.fill((255, 0, 0, 128))
            self.sprite_data = {"frames": {}}
            self.sprite_cache = {}

    def get_sprite(self, sprite_name, scale=1):
        """
        Get a sprite from the spritesheet.

        Args:
            sprite_name (str): The name of the sprite to retrieve.
            scale (int, optional): The scale factor to apply to the sprite. Defaults to 1.

        Returns:
            pygame.Surface: The retrieved sprite scaled to the specified size.

        Raises:
            Exception: If there's an error loading the sprite.
        """
        cache_key = (sprite_name, scale)
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key].copy()

        try:
            if sprite_name not in self.sprite_data["frames"]:
                print(f"Warning: Sprite '{sprite_name}' not found")
                return pygame.Surface((32, 32), pygame.SRCALPHA)

            frame = self.sprite_data["frames"][sprite_name]["frame"]
            sprite = pygame.Surface((frame["w"], frame["h"]), pygame.SRCALPHA)
            sprite.blit(
                self.spritesheet,
                (0, 0),
                (frame["x"], frame["y"], frame["w"], frame["h"]),
            )

            if scale != 1:
                new_w = int(frame["w"] * scale)
                new_h = int(frame["h"] * scale)
                sprite = pygame.transform.scale(sprite, (new_w, new_h))

            self.sprite_cache[cache_key] = sprite
            return sprite.copy()

        except Exception as e:
            print(f"Error loading sprite '{sprite_name}': {e}")
            return pygame.Surface((32, 32), pygame.SRCALPHA)

    def get_player_frames(self, scale=1):

        """
        Retrieve a list of player frame sprites from the spritesheet.

        Args:
            scale (int, optional): The scale factor to apply to each sprite. Defaults to 1.

        Returns:
            list of pygame.Surface: A list of scaled player frame sprites.
        """

        return [self.get_sprite(f"player{i}.png", scale) for i in range(5)]

    def get_ladder_frames(self, scale=1):
        """
        Retrieve a list of ladder frame sprites from the spritesheet.

        Args:
            scale (int, optional): The scale factor to apply to each sprite. Defaults to 1.

        Returns:
            list of pygame.Surface: A list of scaled ladder frame sprites.
        """
        return [self.get_sprite(f"ladder{i}.png", scale) for i in range(2)]
