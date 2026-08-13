import os
import pygame
from pygame import *
from assets_manager import ParallaxBackground
from teleport import Teleport, load_teleport_frames
from enemies import Goblin


def load_and_crop(filepath, target_size=None):
    """
    Завантажує файл, відсікає порожні й напівпрозорі поля навколо спрайта
    та масштабує його до потрібного розміру.
    """
    try:
        img = pygame.image.load(filepath).convert_alpha()
        rect = img.get_bounding_rect(min_alpha=50)
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


class PotionLoot(pygame.sprite.Sprite):

    def __init__(self, x, y, sprite_img):
        super().__init__()
        if sprite_img:
            self.image = sprite_img
        else:
            self.image = pygame.Surface((28, 28))
            self.image.fill((50, 200, 50))

        self.rect = self.image.get_rect(topleft=(x, y))


class Level2:
    def __init__(self, screen_width, screen_height, gender="female", hp=100, coins=0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.gender = gender.lower()
        self.completed = False

        # 1. Задній фон
        self.bg = ParallaxBackground(self.screen_width, self.screen_height)
        self.bg.cloud_speed = 0.3

        # 2. Стан гравця
        self.max_hp = 100
        self.player_hp = min(hp, self.max_hp)
        self.coins = coins
        self.has_sword = False
        self.sword_price = 100
        self.invincible_timer = 0

        # 3. Шрифти
        self.font_ui = font.Font(None, 28)
        self.font_shop = font.Font(None, 32)

        # 4. Графічні ресурси
        base_path = "assets/images/lvl_bg/"

        self.img_ground = load_and_crop(base_path + "green_ground.png", target_size=(80, 80))
        self.img_dry_ground = load_and_crop(base_path + "dry_ground.png", target_size=(40, 40))
        self.img_shop = load_and_crop(base_path + "shop.png", target_size=(100, 100))
        self.img_yellow_flowers = load_and_crop(base_path + "yellow_flowers.png", target_size=(40, 25))

        # Завантаження зілля
        try:
            raw_potion = pygame.image.load("assets/images/items/Potion-of-Healing_512.png").convert_alpha()
            self.potion_sprite = pygame.transform.scale(raw_potion, (32, 32))
        except Exception as e:
            print(f"⚠️ Не вдалося завантажити картинку зілля: {e}")
            self.potion_sprite = None

        # Завантаження звуку
        try:
            self.heal_sound = pygame.mixer.Sound("assets/sounds/healspell1.aif")
            self.heal_sound.set_volume(0.9)
        except Exception as e:
            print(f"⚠️ Не вдалося завантажити звук: {e}")
            self.heal_sound = None

        # 5. Рельєф та платформи
        self.tile_size = 40
        self.ground_height = 70
        floor_y = self.screen_height - self.ground_height

        # Нижня земля (зелена)
        self.ground_platforms = [
            pygame.Rect(0, floor_y, self.screen_width, self.ground_height)
        ]

        # Гірки та підвищення (з сухих блоків)
        self.hill_platforms = [
            pygame.Rect(180, floor_y - 40, self.tile_size * 4, self.tile_size),  # Платформа для 1 моба
            pygame.Rect(440, floor_y - 40, 40, 40),
            pygame.Rect(480, floor_y - 80, 40, 80),
            pygame.Rect(520, floor_y - 120, 120, 120),  # Вершина гірки
            pygame.Rect(640, floor_y - 80, 40, 80),
            pygame.Rect(680, floor_y - 40, 40, 40)
        ]

        self.platforms = self.ground_platforms + self.hill_platforms

        # Крамниця
        self.shop_rect = pygame.Rect(910, floor_y - 100, 100, 100)

        # 6. Телепорт до боса
        teleport_frames = load_teleport_frames(base_path + "teleports.png", target_height=90)
        self.teleports = pygame.sprite.Group()
        self.teleports.add(Teleport(x=1140, y=floor_y, frames=teleport_frames))

        # 7. Гравець
        self.player_rect = pygame.Rect(60, floor_y - 60, 32, 48)
        self.vel_y = 0
        self.is_grounded = False
        self.gravity = 0.8
        self.facing_right = True

        # Анімація та завантаження спрайтів гравця
        self.player_frames = self._load_player_frames()
        self.anim_index = 0.0
        self.is_moving = False

        # 8. Моби та Лут
        self.mobs = pygame.sprite.Group()
        self.mobs.add(Goblin(x=200, y=floor_y - 40 - 48, start_x=180, end_x=320, target_height=48))  # Моб 1 на гірці
        self.mobs.add(Goblin(x=740, y=floor_y - 48, start_x=720, end_x=870, target_height=48))      # Моб 2 на землі

        self.loot_group = pygame.sprite.Group()

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
            print("Файл спрайтів гравця не знайдено.")
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
        voice_speed = 0
        self.is_moving = False

        if audio_controller:
            action = audio_controller.get_action()
            if action == "WALK":
                voice_speed = 4
            elif action == "RUN":
                voice_speed = 7
            elif action == "JUMP" and self.is_grounded:
                self.vel_y = -14
                self.is_grounded = False

        if voice_speed > 0:
            self.is_moving = True
            if self.facing_right:
                self.player_rect.x += voice_speed
            else:
                self.player_rect.x -= voice_speed

        if keys[K_LEFT] or keys[K_a]:
            self.player_rect.x -= 4
            self.facing_right = False
            self.is_moving = True
        if keys[K_RIGHT] or keys[K_d]:
            self.player_rect.x += 4
            self.facing_right = True
            self.is_moving = True

        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_f:
                    for mob in list(self.mobs):
                        if self.player_rect.colliderect(mob.rect.inflate(40, 20)):
                            mob_facing_right = (mob.direction == 1)
                            player_behind = (self.player_rect.x < mob.rect.x and mob_facing_right) or \
                                            (self.player_rect.x > mob.rect.x and not mob_facing_right)

                            if player_behind:
                                potion = PotionLoot(mob.rect.centerx - 16, mob.rect.bottom - 32, self.potion_sprite)
                                self.loot_group.add(potion)
                                mob.kill()

                if e.key == K_e:
                    if self.player_rect.colliderect(self.shop_rect.inflate(40, 20)):
                        if not self.has_sword and self.coins >= self.sword_price:
                            self.coins -= self.sword_price
                            self.has_sword = True
                            print("Ви купили меч!")

    def update(self):
        self.bg.update()
        self.mobs.update()
        self.teleports.update(self.player_rect)

        self.vel_y += self.gravity
        self.player_rect.y += self.vel_y

        self.is_grounded = False
        for plat in self.platforms:
            if self.player_rect.colliderect(plat):
                if self.vel_y > 0:
                    self.player_rect.bottom = plat.top
                    self.vel_y = 0
                    self.is_grounded = True
                elif self.vel_y < 0:
                    self.player_rect.top = plat.bottom
                    self.vel_y = 0

        # Анімація бігу / спокою
        if self.player_frames:
            if self.is_moving:
                self.anim_index = (self.anim_index + 0.15) % len(self.player_frames)
            else:
                self.anim_index = 0

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        if self.invincible_timer == 0:
            for mob in self.mobs:
                if self.player_rect.colliderect(mob.rect):
                    self.player_hp = max(0, self.player_hp - mob.damage)
                    self.invincible_timer = 60

        for potion in list(self.loot_group):
            if self.player_rect.colliderect(potion.rect):
                self.player_hp = min(self.max_hp, self.player_hp + 10)
                self.coins += 100

                if self.heal_sound:
                    self.heal_sound.play()

                potion.kill()

        for tp in self.teleports:
            if tp.is_fully_open() and self.player_rect.colliderect(tp.rect):
                print("Перехід на 3 рівень (Бос)!")
                self.completed = True

        self.player_rect.clamp_ip(pygame.Rect(0, 0, self.screen_width, self.screen_height))

    def draw(self, window):
        #  Фон
        self.bg.draw(window)

        floor_y = self.screen_height - self.ground_height

        # Нижня зелена земля
        if self.img_ground:
            tile_w = self.img_ground.get_width()
            for x in range(0, self.screen_width, tile_w):
                window.blit(self.img_ground, (x, floor_y))
        else:
            for plat in self.ground_platforms:
                draw.rect(window, (34, 139, 34), plat)

        # Жовті квіти на зеленій землі
        if self.img_yellow_flowers:
            flower_h = self.img_yellow_flowers.get_height()
            window.blit(self.img_yellow_flowers, (110, floor_y - flower_h))
            window.blit(self.img_yellow_flowers, (380, floor_y - flower_h))
            window.blit(self.img_yellow_flowers, (780, floor_y - flower_h))
            window.blit(self.img_yellow_flowers, (1040, floor_y - flower_h))

        #  Гірки з сухих блоків
        for plat in self.hill_platforms:
            if self.img_dry_ground:
                for x in range(plat.x, plat.x + plat.width, self.tile_size):
                    for y in range(plat.y, plat.y + plat.height, self.tile_size):
                        window.blit(self.img_dry_ground, (x, y))
            else:
                draw.rect(window, (139, 115, 85), plat)

        #  Крамниця (Шоп)
        if self.img_shop:
            window.blit(self.img_shop, self.shop_rect.topleft)
        else:
            draw.rect(window, (120, 70, 30), self.shop_rect, border_radius=6)

        shop_title = self.font_shop.render("КРАМНИЦЯ", True, (255, 215, 0))
        window.blit(shop_title, (self.shop_rect.x - 5, self.shop_rect.y - 30))

        if not self.has_sword:
            hint = self.font_ui.render(f"Тисни 'E' — МЕЧ ({self.sword_price} монет)", True, (255, 255, 255))
            window.blit(hint, (self.shop_rect.x - 60, self.shop_rect.y - 55))
        else:
            hint = self.font_ui.render("МЕЧ КУПЛЕНО! ⚔️", True, (100, 255, 100))
            window.blit(hint, (self.shop_rect.x - 20, self.shop_rect.y - 55))

        #  Телепорт (перехід до Боса)
        self.teleports.draw(window)

        boss_lbl = self.font_ui.render("БОС ->", True, (255, 100, 100))
        window.blit(boss_lbl, (1115, floor_y - 115))

        #  Малювання зілля та мобів
        self.loot_group.draw(window)
        self.mobs.draw(window)

        for mob in self.mobs:
            mob_hint = self.font_ui.render("Тисни 'F' зі спини!", True, (255, 120, 120))
            window.blit(mob_hint, (mob.rect.x - 20, mob.rect.y - 25))

        #  Відмальовка Персонажа
        if self.invincible_timer % 10 < 5:
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
                draw.rect(window, p_color, self.player_rect)

        #  HUD
        draw.rect(window, (60, 60, 60), (20, 20, 200, 24), border_radius=4)
        hp_width = int((self.player_hp / self.max_hp) * 196)
        if hp_width > 0:
            draw.rect(window, (40, 200, 80), (22, 22, hp_width, 20), border_radius=4)

        hp_text = self.font_ui.render(f"HP: {self.player_hp}/{self.max_hp}", True, (255, 255, 255))
        window.blit(hp_text, (230, 22))

        coins_text = self.font_ui.render(f"💰 Монети: {self.coins}", True, (255, 215, 0))
        window.blit(coins_text, (400, 22))