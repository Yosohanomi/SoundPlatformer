import os
import pygame
from pygame import *


class GenderMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_gender = "female"
        self.is_finished = False

        self.font_title = font.Font(None, 48)
        self.font_btn = font.Font(None, 32)

        self.card_w = 180
        self.card_h = 240
        center_y = self.screen_height // 2 - 20

        self.male_rect = pygame.Rect(
            self.screen_width // 2 - self.card_w - 30,
            center_y,
            self.card_w,
            self.card_h
        )

        self.female_rect = pygame.Rect(
            self.screen_width // 2 + 30,
            center_y,
            self.card_w,
            self.card_h
        )

        self.confirm_rect = pygame.Rect(
            self.screen_width // 2 - 110,
            self.screen_height - 90,
            220,
            50
        )

        self.male_sprite = self._load_preview_sprite("male")
        self.female_sprite = self._load_preview_sprite("female")

    @property
    def finished(self):
        return self.is_finished

    @finished.setter
    def finished(self, value):
        self.is_finished = value

    def _load_preview_sprite(self, gender):
        base_dir = os.path.join("assets", "images", "characters")

        possible_paths = [
            os.path.join(base_dir, f"{gender}.png"),
            os.path.join(base_dir, gender, f"{gender}.png"),
            os.path.join("assets", "images", "characters", "player", f"{gender}.png")
        ]

        sheet = None
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    sheet = pygame.image.load(path).convert_alpha()
                    break
                except Exception as e:
                    print(f"Помилка читання {path}: {e}")

        if not sheet:
            return None

        sw, sh = sheet.get_size()
        cols = 12
        frame_w = sw // cols

        crop_rect = Rect(0, 0, frame_w, sh)
        sub_img = sheet.subsurface(crop_rect)

        bounding = sub_img.get_bounding_rect(min_alpha=10)
        if bounding.width > 0 and bounding.height > 0:
            sub_img = sub_img.subsurface(bounding)

        orig_w, orig_h = sub_img.get_size()
        target_h = 130
        target_w = int(orig_w * (target_h / orig_h))

        return pygame.transform.scale(sub_img, (target_w, target_h))

    def handle_input(self, events):
        for e in events:
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = e.pos

                if self.male_rect.collidepoint(mouse_pos):
                    self.selected_gender = "male"
                elif self.female_rect.collidepoint(mouse_pos):
                    self.selected_gender = "female"
                elif self.confirm_rect.collidepoint(mouse_pos):
                    self.is_finished = True

            elif e.type == KEYDOWN:
                if e.key in (K_LEFT, K_a):
                    self.selected_gender = "male"
                elif e.key in (K_RIGHT, K_d):
                    self.selected_gender = "female"
                elif e.key in (K_RETURN, K_SPACE):
                    self.is_finished = True

    handle_events = handle_input

    def draw(self, window):
        window.fill((20, 24, 33))

        header_bg = pygame.Rect(self.screen_width // 2 - 220, 40, 440, 60)
        draw.rect(window, (30, 36, 50), header_bg, border_radius=12)
        draw.rect(window, (70, 80, 110), header_bg, width=2, border_radius=12)

        title_surf = self.font_title.render("ОБЕРІТЬ ПЕРСОНАЖА", True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=header_bg.center)
        window.blit(title_surf, title_rect)

        bg_m = (38, 44, 60) if self.selected_gender != "male" else (48, 56, 80)
        draw.rect(window, bg_m, self.male_rect, border_radius=14)

        if self.male_sprite:
            spr_rect = self.male_sprite.get_rect(center=(self.male_rect.centerx, self.male_rect.y + 90))
            window.blit(self.male_sprite, spr_rect)

        m_lbl = self.font_btn.render("Хлопець", True, (230, 230, 240))
        window.blit(m_lbl, m_lbl.get_rect(center=(self.male_rect.centerx, self.male_rect.bottom - 30)))

        # --- КАРТКА ДІВЧИНИ ---
        bg_f = (38, 44, 60) if self.selected_gender != "female" else (48, 56, 80)
        draw.rect(window, bg_f, self.female_rect, border_radius=14)

        if self.female_sprite:
            spr_rect = self.female_sprite.get_rect(center=(self.female_rect.centerx, self.female_rect.y + 90))
            window.blit(self.female_sprite, spr_rect)

        f_lbl = self.font_btn.render("Дівчина", True, (230, 230, 240))
        window.blit(f_lbl, f_lbl.get_rect(center=(self.female_rect.centerx, self.female_rect.bottom - 30)))

        # --- РАМКА ВИБРАНОГО ПЕРСОНАЖА ---
        active_rect = self.male_rect if self.selected_gender == "male" else self.female_rect
        draw.rect(window, (255, 215, 0), active_rect, width=4, border_radius=14)

        # --- КНОПКА "ПОЧАТИ" ---
        hover = self.confirm_rect.collidepoint(pygame.mouse.get_pos())
        btn_color = (70, 180, 80) if hover else (50, 140, 60)
        draw.rect(window, btn_color, self.confirm_rect, border_radius=10)
        draw.rect(window, (255, 255, 255), self.confirm_rect, width=2, border_radius=10)

        btn_lbl = self.font_btn.render("ПОЧАТИ ГРУ", True, (255, 255, 255))
        window.blit(btn_lbl, btn_lbl.get_rect(center=self.confirm_rect.center))