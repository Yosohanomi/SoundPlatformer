import pygame


class ParallaxBackground:

    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height

        try:
            self.mountains = pygame.image.load(
                "assets/images/lvl_bg/2015-02-26 [DB32](Generic Platformer)(Mountains).png").convert_alpha()
            self.mountains = pygame.transform.scale(self.mountains, (self.width, self.height))
        except Exception as e:
            print(f"Помилка завантаження гір: {e}")
            self.mountains = None

        try:
            self.clouds = pygame.image.load(
                "assets/images/lvl_bg/2015-02-26 [DB32](Generic Platformer)(Clouds).png").convert_alpha()
            self.clouds = pygame.transform.scale(self.clouds, (self.width, self.height))
        except Exception as e:
            print(f"Помилка завантаження хмар: {e}")
            self.clouds = None

        self.cloud_x1 = 0
        self.cloud_x2 = self.width
        self.cloud_speed = 0.5

    def update(self):
        self.cloud_x1 -= self.cloud_speed
        self.cloud_x2 -= self.cloud_speed

        if self.cloud_x1 <= -self.width:
            self.cloud_x1 = self.width
        if self.cloud_x2 <= -self.width:
            self.cloud_x2 = self.width

    def draw(self, window):
        if self.mountains:
            window.blit(self.mountains, (0, 0))

        if self.clouds:
            window.blit(self.clouds, (int(self.cloud_x1), 0))
            window.blit(self.clouds, (int(self.cloud_x2), 0))


class SpriteSheet:

    def __init__(self, filename):
        self.sheet = pygame.image.load(filename).convert_alpha()

    def get_image(self, x, y, width, height, scale=1.0, colorkey=None):
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, width, height))

        if colorkey is not None:
            image.set_colorkey(colorkey)

        if scale != 1.0:
            image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        return image