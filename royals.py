import os
import pygame
from pygame import Rect


class RoyalNPC:
    def __init__(self, x, y_bottom, player_gender="female"):
        self.is_king = (str(player_gender).lower() == "female")
        self.prefix = "king" if self.is_king else "queen"
        self.title = "Король" if self.is_king else "Королева"
        self.dialogue = (
            "Дякую, що врятувала моє королівство від злих монстрів!"
            if self.is_king
            else "Дякую, що врятував моє королівство від злих монстрів!"
        )

        self.target_height = 90
        self.idle_frame = None
        self.bow_frames = []

        self._load_sprites()

        # Початкові розміри та хітбокс
        sample_surf = self.idle_frame if self.idle_frame else (self.bow_frames[0] if self.bow_frames else None)
        width = sample_surf.get_width() if sample_surf else 50

        # Фіксує
        self.rect = Rect(x, y_bottom - self.target_height, width, self.target_height)

        self.bow_index = 0.0
        self.bow_speed = 0.08

    def _find_file(self, prefixes):
        project_dir = os.path.dirname(os.path.abspath(__file__))

        for filename in prefixes:
            possible_paths = [
                os.path.join(project_dir, "assets", "images", "characters", "royal", filename),
                os.path.join("assets", "images", "characters", "royal", filename),
                os.path.join("assets", "images", "characters", filename),
                os.path.join(project_dir, filename),
                filename
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    return p
        return None

    def _load_sprites(self):
        idle_names = [f"{self.prefix}_idle_2.png", f"{self.prefix}_idle_3.png", f"{self.prefix}_idle.png"]
        idle_path = self._find_file(idle_names)

        if idle_path:
            img = pygame.image.load(idle_path).convert_alpha()
            b_rect = img.get_bounding_rect(min_alpha=1)
            if b_rect.width > 0 and b_rect.height > 0:
                img = img.subsurface(b_rect)

            orig_w, orig_h = img.get_size()
            tw = max(1, int(orig_w * (self.target_height / orig_h)))
            self.idle_frame = pygame.transform.scale(img, (tw, self.target_height))

        bow_names = [f"{self.prefix}_bow_4.png", f"{self.prefix}_bow_3.png", f"{self.prefix}_bow_2.png",
                     f"{self.prefix}_bow.png"]
        bow_path = self._find_file(bow_names)

        if bow_path:
            try:
                sheet = pygame.image.load(bow_path).convert_alpha()

                sheet_b = sheet.get_bounding_rect(min_alpha=1)
                if sheet_b.width > 0 and sheet_b.height > 0:
                    sheet = sheet.subsurface(sheet_b)

                full_w, full_h = sheet.get_size()
                frame_w = full_w // 2

                self.bow_frames = []
                for i in range(2):
                    frame_rect = Rect(i * frame_w, 0, frame_w, full_h)
                    sub_img = sheet.subsurface(frame_rect)

                    orig_w, orig_h = sub_img.get_size()
                    tw = max(1, int(orig_w * (self.target_height / orig_h)))
                    scaled = pygame.transform.scale(sub_img, (tw, self.target_height))
                    self.bow_frames.append(scaled)

            except Exception as e:
                print(f"Помилка завантаження {bow_path}: {e}")

    def update(self, player_rect):
        distance = abs(player_rect.centerx - self.rect.centerx)
        is_near = distance < 250

        if is_near and self.bow_frames:
            if self.bow_index < len(self.bow_frames) - 1:
                self.bow_index += self.bow_speed
                if self.bow_index >= len(self.bow_frames) - 1:
                    self.bow_index = len(self.bow_frames) - 1
        else:
            self.bow_index = 0.0

    def draw(self, window, player_rect):
        distance = abs(player_rect.centerx - self.rect.centerx)
        is_near = distance < 250

        if is_near and self.bow_frames:
            current_surf = self.bow_frames[int(self.bow_index)]
        elif self.idle_frame:
            current_surf = self.idle_frame
        else:
            current_surf = None

        if current_surf:
            draw_rect = current_surf.get_rect(bottomleft=self.rect.bottomleft)
            window.blit(current_surf, draw_rect)
        else:
            pygame.draw.rect(window, (255, 215, 0), self.rect, border_radius=4)