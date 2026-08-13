import os
import pygame
from pygame import *

BASE_DIR = os.path.join("assets", "images", "characters")

GENDER_FILES = {
    "female": os.path.join(BASE_DIR, "female.png"),
    "male": os.path.join(BASE_DIR, "male.png")
}


def load_character_sheet(gender):
    file_path = GENDER_FILES.get(gender)

    if not file_path or not os.path.exists(file_path):
        alt_path = os.path.join(BASE_DIR, gender, f"{gender}.png")
        if os.path.exists(alt_path):
            file_path = alt_path

    if file_path and os.path.exists(file_path):
        try:
            return image.load(file_path).convert_alpha()
        except Exception as e:
            print(f"Помилка завантаження спрайтшиту {file_path}: {e}")

    blank = Surface((64, 64), SRCALPHA)
    draw.rect(blank, (200, 150, 100), (20, 10, 24, 44))
    return blank


class Player(sprite.Sprite):
    def __init__(self, gender, x=200, y=400, scale_factor=1.35):
        super().__init__()
        self.gender = gender
        self.scale_factor = scale_factor

        self.sheet = load_character_sheet(self.gender)

        self.frames = []
        self.load_frames()

        self.current_frame = 0
        if self.frames:
            self.image = self.frames[0]
        else:
            self.image = Surface((40, 60), SRCALPHA)
            self.image.fill((100, 100, 250))

        self.rect = self.image.get_rect(midbottom=(x, y))

        self.hp = 3
        self.coins = 0
        self.facing_right = True

    def load_frames(self):

        sw, sh = self.sheet.get_size()
        cols = 12
        frame_w = sw // cols

        for col in range(cols):
            x = col * frame_w
            sub_surface = self.sheet.subsurface(Rect(x, 0, frame_w, sh))

            bounding_box = sub_surface.get_bounding_rect(min_alpha=10)
            if bounding_box.width > 0 and bounding_box.height > 0:
                cropped_frame = sub_surface.subsurface(bounding_box)
            else:
                cropped_frame = sub_surface

            orig_w, orig_h = cropped_frame.get_size()
            new_w = max(1, int(orig_w * self.scale_factor))
            new_h = max(1, int(orig_h * self.scale_factor))
            scaled_frame = transform.scale(cropped_frame, (new_w, new_h))

            self.frames.append(scaled_frame)

    def update(self):
        if self.frames:
            walk_frames = self.frames[:4]
            self.current_frame = (self.current_frame + 0.15) % len(walk_frames)

            frame = walk_frames[int(self.current_frame)]

            if not self.facing_right:
                self.image = transform.flip(frame, True, False)
            else:
                self.image = frame

            old_midbottom = self.rect.midbottom
            self.rect = self.image.get_rect(midbottom=old_midbottom)