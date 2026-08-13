import os
import pygame
from pygame import Rect, sprite


class Goblin(sprite.Sprite):
    def __init__(self, x, y, start_x, end_x, speed=2, target_height=48):
        super().__init__()

        self.start_x = start_x
        self.end_x = end_x
        self.speed = speed
        self.direction = 1

        self.hp = 80
        self.damage = 10
        self.target_height = target_height

        self.frames = self._load_first_row_frames()
        self.anim_index = 0.0
        self.anim_speed = 0.15

        if self.frames:
            self.image = self.frames[0]
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            self.image = pygame.Surface((36, 48))
            self.image.fill((50, 180, 50))
            self.rect = self.image.get_rect(topleft=(x, y))

    def _load_first_row_frames(self):
        project_dir = os.path.dirname(os.path.abspath(__file__))

        filepath = os.path.join(project_dir, "assets", "images", "characters", "goblin.soldier.png")

        try:
            sheet = pygame.image.load(filepath).convert_alpha()
        except Exception as e:
            print(f"⚠️ Помилка завантаження {filepath}: {e}")
            return []

        sw, sh = sheet.get_size()
        cols = 10
        rows = 4

        frame_w = sw // cols
        frame_h = sh // rows

        frames = []
        for col in range(cols):
            sub_img = sheet.subsurface(Rect(col * frame_w, 0, frame_w, frame_h))

            bounding = sub_img.get_bounding_rect(min_alpha=30)
            if bounding.width > 0 and bounding.height > 0:
                sub_img = sub_img.subsurface(bounding)

            orig_w, orig_h = sub_img.get_size()
            target_w = int(orig_w * (self.target_height / orig_h))
            scaled_img = pygame.transform.scale(sub_img, (target_w, self.target_height))

            frames.append(scaled_img)

        return frames

    def update(self):
        self.rect.x += self.speed * self.direction

        if self.rect.right >= self.end_x:
            self.direction = -1
        elif self.rect.left <= self.start_x:
            self.direction = 1

        if self.frames:
            self.anim_index = (self.anim_index + self.anim_speed) % len(self.frames)
            current_frame = self.frames[int(self.anim_index)]

            if self.direction == -1:
                self.image = pygame.transform.flip(current_frame, True, False)
            else:
                self.image = current_frame