import os
import pygame
from typing import Dict, Optional


class SoundManager:

    def __init__(self):
        """
        Initialize the SoundManager class.

        This constructor initializes the sound manager by setting up the pygame mixer,
        enabling sound, and initializing the sound cache. It attempts to pre-initialize
        and initialize the pygame mixer with specified parameters. If initialization fails,
        a warning is printed. The constructor also sets up default music paths, initializes 
        the current music and volume settings, and ensures the necessary directories for 
        assets exist.

        Attributes:
            sound_enabled (bool): Indicates if the sound is enabled.
            mixer_initialized (bool): Indicates if the mixer has been initialized.
            sound_cache (Dict[str, pygame.mixer.Sound]): A cache for loaded sound effects.
            default_music (str): The default music file path.
            music_paths (Dict[str, str]): Paths to different music types.
            current_music (Optional[str]): The currently playing music type.
            music_volume (float): Volume level for music, ranging from 0.0 to 1.0.
            sound_volume (float): Volume level for sound effects, ranging from 0.0 to 1.0.
        """

        self.sound_enabled = False
        self.mixer_initialized = False
        self.sound_cache: Dict[str, pygame.mixer.Sound] = {}


        try:
            pygame.mixer.pre_init(44100, -16, 2, 2048)
            pygame.mixer.init()
            self.sound_enabled = True
            self.mixer_initialized = True
        except pygame.error as e:
            print(f"Warning: Sound initialization failed - {str(e)}")
            return

        self.default_music = "assets/music/game_soundtrack.mp3"
        self.music_paths = {
            "menu": self.default_music,
            "game": self.default_music,
        }

        self.current_music: Optional[str] = None
        self.music_volume = 0.7
        self.sound_volume = 0.5

        os.makedirs("assets/music", exist_ok=True)
        os.makedirs("assets/sounds", exist_ok=True)

    def check_audio_system(self) -> bool:
        """
        Check if the audio system is initialized and functional.

        If the audio system is not initialized, attempt to initialize it. If the
        initialization fails, print an error message and return False.

        :return: True if the audio system is initialized and functional, False otherwise.
        """
        if not self.mixer_initialized:
            try:
                pygame.mixer.quit()
                pygame.mixer.init(44100, -16, 2, 2048)
                self.mixer_initialized = True
                self.sound_enabled = True
                return True
            except pygame.error as e:
                print(f"Audio system check failed: {str(e)}")
                return False
        return True

    def load_music(self, music_type: str) -> bool:
        """
        Load the music for the given type.

        If the sound is not enabled, return False immediately. If the given music type
        is not in the music paths dictionary, return False. Otherwise, attempt to load
        the music using pygame. If the loading fails, print an error message and
        return False.

        :param music_type: The type of music to load.
        :type music_type: str
        :return: True if the music was loaded successfully, False otherwise.
        """
        if not self.sound_enabled:
            return False

        if music_type in self.music_paths:
            try:
                pygame.mixer.music.load(self.music_paths[music_type])
                return True
            except pygame.error as e:
                print(f"Error loading music: {self.music_paths[music_type]} - {str(e)}")
                return False
        return False

    def play_music(self, music_type, loops=-1):
        """Play music of specified type"""
        if not (self.sound_enabled and self.mixer_initialized):
            return False

        try:
            if music_type not in self.music_paths:
                print(f"Error: Music type '{music_type}' not found in music_paths")
                return False

            if self.current_music == music_type:
                return True

            music_path = self.music_paths[music_type]
            pygame.mixer.music.stop()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops)
            self.current_music = music_type
            return True

        except pygame.error as e:
            print(f"Error playing music {music_type}: {str(e)}")
            return False

    def play_sound(self, sound_name: str) -> bool:
        """
        Play a sound effect by name.

        This method plays a sound effect specified by the sound name. If the sound is
        not already cached, it will be loaded and cached for future use. The sound is
        played at the current sound volume level.

        :param sound_name: The name or path of the sound effect to play.
        :type sound_name: str
        :return: True if the sound was played successfully, False otherwise.
        :rtype: bool
        """

        if not self.sound_enabled:
            return False

        try:
            if sound_name not in self.sound_cache:
                self.sound_cache[sound_name] = pygame.mixer.Sound(sound_name)

            sound = self.sound_cache[sound_name]
            sound.set_volume(self.sound_volume)
            sound.play()
            return True
        except pygame.error as e:
            print(f"Error playing sound {sound_name}: {str(e)}")
            return False

    def stop_music(self) -> None:
        """
        Stop the current music from playing.

        If sound is enabled, this will stop the currently playing music and
        set the current music to None.

        :return: None
        """
        if self.sound_enabled:
            pygame.mixer.music.stop()
            self.current_music = None

    def set_music_volume(self, volume: float) -> None:
        """
        Set the volume of the current music.

        This method sets the volume of the currently playing music to the
        given level. If the volume is outside the range of 0.0 to 1.0, it will
        be clamped to the nearest end of the range.

        :param volume: The volume level to set the music to.
        :type volume: float
        :return: None
        """
        if not self.sound_enabled:
            return
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except pygame.error:
            print("Warning: Could not set music volume")

    def set_sound_volume(self, volume: float) -> None:
        """
        Set the volume of sound effects.

        This method sets the volume for all cached sound effects to the specified level.
        The volume should be within the range of 0.0 to 1.0, and will be clamped to this range if necessary.
        If sound is not enabled, the method will return immediately without making changes.

        :param volume: The volume level to set for sound effects.
        :type volume: float
        :return: None
        """

        if not self.sound_enabled:
            return
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sound_cache.values():
            sound.set_volume(self.sound_volume)

    def pause_music(self) -> None:
        """
        Pause the current music from playing.

        If sound is enabled, this will pause the currently playing music.
        If sound is not enabled, the method will return immediately without making changes.

        :return: None
        """
        if self.sound_enabled:
            pygame.mixer.music.pause()

    def unpause_music(self) -> None:
        """
        Unpause the currently paused music.

        If sound is enabled, this will resume the music that was previously paused.
        If sound is not enabled, the method will return immediately without making changes.

        :return: None
        """

        if self.sound_enabled:
            pygame.mixer.music.unpause()

    def fade_out(self, duration: int = 1000) -> None:
        """
        Gradually reduce the volume of the current music to silence.

        This method fades out the currently playing music over the specified duration.
        If sound is enabled, the music will fade out smoothly to silence, after
        which the current music is set to None.

        :param duration: The fadeout duration in milliseconds, default is 1000.
        :type duration: int
        :return: None
        """

        if self.sound_enabled:
            pygame.mixer.music.fadeout(duration)
            self.current_music = None

    def cleanup(self) -> None:
        """
        Clean up the sound manager.

        This method is used to clean up resources used by the sound manager.
        It clears the sound cache and uninitializes the pygame mixer if it was initialized.

        :return: None
        """

        self.sound_cache.clear()
        if self.mixer_initialized:
            pygame.mixer.quit()
