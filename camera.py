import pygame
from settings import *


class Camera:
    def __init__(self, width, height):
        """
        Constructor for the Camera class.

        Parameters:
        width (int): The width of the camera.
        height (int): The height of the camera.

        Attributes:
        camera (pygame.Rect): The camera rectangle.
        width (int): The width of the camera.
        height (int): The height of the camera.
        move (bool): A flag to indicate if the camera is moving.
        x (int): The x position of the camera.
        y (int): The y position of the camera.
        rect_size (int): The size of the rectangles used to draw the camera on the screen.
        exited_top (bool): A flag to indicate if the camera has exited the top of the screen.
        exited_bottom (bool): A flag to indicate if the camera has exited the bottom of the screen.
        exited_left (bool): A flag to indicate if the camera has exited the left of the screen.
        exited_right (bool): A flag to indicate if the camera has exited the right of the screen.
        """
        self.camera = pygame.Rect(0, 0, WIDTH, HEIGHT)
        self.width = width
        self.height = height
        self.move = True
        self.x = 0
        self.y = 0

        self.rect_size = 50

        self.update_rect_positions()

        self.exited_top = False
        self.exited_bottom = False
        self.exited_left = False
        self.exited_right = False

    def update_rect_positions(self):
        """
        Updates the rectangles used to draw the camera on the screen.

        This method is called whenever the camera is moved. It calculates the new positions of the rectangles and creates new surfaces and rectangles accordingly.

        Attributes:
        rect_size (int): The size of the rectangles used to draw the camera on the screen.
        center_x (int): The x position of the center of the screen.
        center_y (int): The y position of the center of the screen.
        rects (list): A list of tuples, where each tuple contains a surface and a rectangle used to draw the camera on the screen.
        """
        center_x = -1 * self.camera.x + WIDTH // 2
        center_y = -1 * self.camera.y + HEIGHT // 2

        self.rects = []
        for dx in [-self.rect_size, 0]:
            for dy in [-self.rect_size, 0]:
                surface = pygame.Surface((self.rect_size, self.rect_size))
                surface.fill(RED)
                surface.set_alpha(0)
                rect = surface.get_rect(topleft=(center_x + dx, center_y + dy))
                self.rects.append((surface, rect))

    def apply(self, entity):
        """
        Applies the camera to the given entity.

        This method moves the entity by the camera's position. If the entity is a pygame.Rect, it is moved directly. If the entity is not a pygame.Rect, it is assumed to have a rect attribute which is moved.

        Args:
            entity (pygame.Rect or object with a rect attribute): The entity to apply the camera to.

        Returns:
            pygame.Rect: The moved entity or its rect attribute.
        """
        if isinstance(entity, pygame.Rect):
            return entity.move(self.camera.topleft)
        else:
            return entity.rect.move(self.camera.topleft)

    def update(self, target):
        """
        Updates the camera to follow the target.

        Parameters:
            target (pygame.Rect or object with a rect attribute): The target to follow.

        This method moves the camera to keep the target in the center of the screen. It calculates the distance between the target's center and the camera's center, and then moves the camera by 1/10 of that distance. If the target is outside of the screen, it moves the camera to the edge of the screen.

        Attributes:
            x (int): The x position of the camera.
            y (int): The y position of the camera.
            exited_top (bool): A flag to indicate if the camera has exited the top of the screen.
            exited_bottom (bool): A flag to indicate if the camera has exited the bottom of the screen.
            exited_left (bool): A flag to indicate if the camera has exited the left of the screen.
            exited_right (bool): A flag to indicate if the camera has exited the right of the screen.
        """
        center_x = -self.camera.x + WIDTH // 2
        center_y = -self.camera.y + HEIGHT // 2
        distance_x = abs(target.rect.centerx - center_x)
        distance_y = abs(target.rect.centery - center_y)

        speed_x = distance_x // 10
        speed_y = distance_y // 10

        if target.rect.centerx < center_x:
            self.x += speed_x
        elif target.rect.centerx > center_x:
            self.x -= speed_x

        if target.rect.centery < center_y:
            self.y += speed_y
        elif target.rect.centery > center_y:
            self.y -= speed_y

        self.x = min(0, self.x)
        self.y = min(0, self.y)
        self.x = max(-(self.width - WIDTH), self.x)
        self.y = max(-(self.height - HEIGHT), self.y)

        self.camera = pygame.Rect(self.x, self.y, self.width, self.height)
        self.update_rect_positions()

        self.exited_top = False
        self.exited_bottom = False
        self.exited_left = False
        self.exited_right = False
