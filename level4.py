import os
import pygame
from pygame import *
from royals import RoyalNPC


def load_and_crop(filepath, target_size=None):
    try:
        img = pygame.image.load(filepath).convert_alpha()
        rect = img.get_bounding_rect(min_alpha=30)
        if rect.width > 0 and rect.height > 0:
            cropped = img.subsurface(rect)
        else:
            cropped = img

        if target_size:
            return pygame.transform.scale(cropped, target_size)
        return cropped
    except Exception as e:
        print(f"Помилка завантаження {filepath}: {e}")
        return None


class Level4:
    def __init__(self, screen_width, screen_height, gender="female", hp=100, coins=0, has_sword=False):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.gender = gender.lower()

        # Фізика та підлога
        self.ground_height = 80
        self.tile_size = 40
        floor_y = screen_height - self.ground_height
        self.ground_rect = Rect(0, floor_y, screen_width, self.ground_height)

        # Стан гравця
        self.max_hp = 100
        self.player_hp = min(hp, self.max_hp)
        self.coins = coins
        self.has_sword = has_sword

        self.player_rect = Rect(100, floor_y - 60, 32, 48)
        self.walk_speed = 4
        self.run_speed = 7
        self.facing_right = True
        self.is_jumping = False
        self.jump_velocity = 0
        self.gravity = 0.8

        # Анімація гравця
        self.player_frames = self._load_player_frames()
        self.anim_index = 0.0
        self.is_moving = False

        # Створення правителя
        self.royal = RoyalNPC(x=screen_width - 200, y_bottom=floor_y, player_gender=self.gender)
        self.npc_rect = self.royal.rect
        self.dialogue = self.royal.dialogue
        self.npc_title = self.royal.title

        self.font = font.Font(None, 28)
        self.title_font = font.Font(None, 42)
        self.completed = True
        self.current_voice_action = "NONE"

        # --- ЗАВАНТАЖЕННЯ АСЕТІВ ---
        project_dir = os.path.dirname(os.path.abspath(__file__))
        lvl_path = os.path.join(project_dir, "assets", "images", "lvl_bg")

        self.img_ground = load_and_crop(os.path.join(lvl_path, "royal_ground.png"), target_size=(40, 40))
        self.img_stone = load_and_crop(os.path.join(lvl_path, "royal_stone.png"), target_size=(90, 45))
        self.img_statue = load_and_crop(os.path.join(lvl_path, "statue.png"), target_size=(110, 150))
        self.img_church = load_and_crop(os.path.join(lvl_path, "church.png"), target_size=(380, 500))

    def _load_player_frames(self):
        base_dir = os.path.join("assets", "images", "characters")
        possible_paths = [
            os.path.join(base_dir, f"{self.gender}.png"),
            os.path.join(base_dir, self.gender, f"{self.gender}.png"),
            os.path.join("assets", "images", "characters", "player", f"{self.gender}.png"),
            os.path.join("assets", "images", "characters", "player", "character_model.png")
        ]

        sheet = None
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    sheet = pygame.image.load(path).convert_alpha()
                    break
                except Exception as e:
                    print(f"Помилка відкриття {path}: {e}")

        if not sheet:
            print(" Файл спрайтів гравця не знайдено.")
            return []

        sw, sh = sheet.get_size()
        cols = 12
        frame_w = sw // cols

        frames = []
        for col in range(min(4, cols)):
            sub_img = sheet.subsurface(Rect(col * frame_w, 0, frame_w, sh))

            bounding = sub_img.get_bounding_rect(min_alpha=30)
            if bounding.width > 0 and bounding.height > 0:
                sub_img = sub_img.subsurface(bounding)

            orig_w, orig_h = sub_img.get_size()
            target_h = self.player_rect.height
            target_w = int(orig_w * (target_h / orig_h))

            scaled_img = pygame.transform.scale(sub_img, (target_w, target_h))
            frames.append(scaled_img)

        return frames

    def handle_input(self, keys, events, audio_controller=None):
        voice_action = audio_controller.get_action() if audio_controller else None
        self.current_voice_action = voice_action if voice_action else "NONE"

        self.is_moving = False
        voice_speed = 0

        if voice_action == "WALK":
            voice_speed = self.walk_speed
        elif voice_action == "RUN":
            voice_speed = self.run_speed
        elif voice_action == "JUMP" and not self.is_jumping:
            self.is_jumping = True
            self.jump_velocity = -14

        if voice_speed > 0:
            self.is_moving = True
            if self.facing_right:
                self.player_rect.x += voice_speed
            else:
                self.player_rect.x -= voice_speed

        if keys[K_a] or keys[K_LEFT]:
            self.player_rect.x -= self.walk_speed
            self.facing_right = False
            self.is_moving = True
        if keys[K_d] or keys[K_RIGHT]:
            self.player_rect.x += self.walk_speed
            self.facing_right = True
            self.is_moving = True

        for e in events:
            if e.type == KEYDOWN and e.key == K_SPACE and not self.is_jumping:
                self.is_jumping = True
                self.jump_velocity = -14

        if self.player_rect.left < 0:
            self.player_rect.left = 0
        if self.player_rect.right > self.screen_width:
            self.player_rect.right = self.screen_width

    def update(self):
        # анімація уклону
        self.royal.update(self.player_rect)

        # Анімація бігу / спокою гравця
        if self.player_frames:
            if self.is_moving:
                self.anim_index = (self.anim_index + 0.15) % len(self.player_frames)
            else:
                self.anim_index = 0

        # Фізика стрибка
        if self.is_jumping:
            self.player_rect.y += self.jump_velocity
            self.jump_velocity += self.gravity

            if self.player_rect.bottom >= self.ground_rect.top:
                self.player_rect.bottom = self.ground_rect.top
                self.is_jumping = False
                self.jump_velocity = 0

    def draw(self, window):
        #  Задній фон
        window.fill((30, 25, 40))

        floor_y = self.screen_height - self.ground_height

        # Фонові споруди (церква)
        if self.img_church:
            church_x = 220
            church_y = floor_y - self.img_church.get_height() + 40
            window.blit(self.img_church, (church_x, church_y))

        # Статуя
        if self.img_statue:
            window.blit(self.img_statue, (100, floor_y - self.img_statue.get_height()))

        # Камені
        if self.img_stone:
            window.blit(self.img_stone, (580, floor_y - self.img_stone.get_height()))
            window.blit(self.img_stone, (780, floor_y - self.img_stone.get_height()))

        # Підлога
        if self.img_ground:
            tile_w = self.img_ground.get_width()
            tile_h = self.img_ground.get_height()
            for y in range(floor_y, self.screen_height, tile_h):
                for x in range(0, self.screen_width, tile_w):
                    window.blit(self.img_ground, (x, y))
        else:
            draw.rect(window, (180, 160, 60), self.ground_rect)

        # НПЦ (Правитель) ВІДМАЛЬОВКА
        self.royal.draw(window, self.player_rect)

        # Підпис над НПЦ
        npc_label = self.font.render(self.npc_title, True, (255, 235, 170))
        window.blit(npc_label, (self.royal.rect.x - 5, self.royal.rect.y - 28))

        # Гравець
        if self.player_frames:
            current_frame = self.player_frames[int(self.anim_index)]
            if not self.facing_right:
                rendered_sprite = pygame.transform.flip(current_frame, True, False)
            else:
                rendered_sprite = current_frame

            sprite_rect = rendered_sprite.get_rect(centerx=self.player_rect.centerx, bottom=self.player_rect.bottom)
            window.blit(rendered_sprite, sprite_rect)
        else:
            p_color = (70, 130, 220) if self.gender == "male" else (220, 100, 180)
            draw.rect(window, p_color, self.player_rect, border_radius=4)

        # Діалог
        if self.player_rect.inflate(160, 0).colliderect(self.royal.rect):
            dialog_rect = Rect(self.screen_width // 2 - 330, 110, 660, 90)
            draw.rect(window, (255, 252, 240), dialog_rect, border_radius=8)
            draw.rect(window, (220, 170, 30), dialog_rect, 4, border_radius=8)

            text_surf = self.font.render(self.dialogue, True, (30, 20, 40))
            window.blit(text_surf,
                        (dialog_rect.x + (dialog_rect.width - text_surf.get_width()) // 2, dialog_rect.y + 32))

        # Індикатор голосу
        info_surf = self.font.render(f"Голос: {self.current_voice_action}", True, (255, 255, 255))
        window.blit(info_surf, (20, 20))

        # Заголовок
        win_title = self.title_font.render("ГРУ УСПІШНО ПРОЙДЕНО!", True, (255, 220, 100))
        tx = self.screen_width // 2 - win_title.get_width() // 2
        window.blit(win_title, (tx, 30))