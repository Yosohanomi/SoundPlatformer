import os
import pygame
from pygame import *
import math
from assets_manager import ParallaxBackground


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
        print(f"⚠️ Помилка завантаження {filepath}: {e}")
        return None


# --- КЛАС КУЛІ ---
class MagicBullet:
    def __init__(self, x, y, target_x, target_y, bullet_img=None, speed=5):
        self.rect = Rect(x - 16, y - 16, 32, 32)
        self.raw_image = bullet_img

        # тимчасовий замінник
        if self.raw_image is None:
            self.raw_image = pygame.Surface((32, 32), pygame.SRCALPHA)
            draw.ellipse(self.raw_image, (255, 120, 0), (0, 0, 32, 32))

        self.image = pygame.transform.scale(self.raw_image, (36, 36))
        self.angle = 0  # Кут обертання

        # вектор руху напряму до гравця
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)
        if distance == 0:
            distance = 1

        self.vx = (dx / distance) * speed
        self.vy = (dy / distance) * speed
        self.damage = 12

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.angle = (self.angle + 12) % 360

    def draw(self, window):
        # Обертання відносно центру кулі
        rotated_img = pygame.transform.rotate(self.image, self.angle)
        new_rect = rotated_img.get_rect(center=self.rect.center)
        window.blit(rotated_img, new_rect.topleft)


# --- КЛАС ТРЕТЬОГО РІВНЯ ТА БОСА ---
class Level3:
    def __init__(self, screen_width, screen_height, gender="female", hp=100, coins=0, has_sword=False):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.gender = gender.lower()

        # Задній фон
        self.bg = ParallaxBackground(self.screen_width, self.screen_height)
        self.bg.cloud_speed = 0.3

        #  Арена та поверхня
        self.ground_height = 80
        floor_y = screen_height - self.ground_height
        self.ground_rect = Rect(0, floor_y, screen_width, self.ground_height)

        #  Графічні ресурси карти
        lvl_path = "assets/images/lvl_bg/"
        self.img_purple_ground = load_and_crop(lvl_path + "boss_purple_ground.png", target_size=(80, 80))
        self.img_purple_tree = load_and_crop(lvl_path + "boss_purple_tree.png", target_size=(70, 90))
        self.img_red_flower = load_and_crop(lvl_path + "boss_red_flower.png", target_size=(30, 35))
        self.img_dry_flower = load_and_crop(lvl_path + "boss_dry_flower.png", target_size=(35, 45))

        #  Графічні ресурси боса та куль
        boss_path = "assets/images/characters/boss/"

        # Кулі
        try:
            self.bullet_sprite = pygame.image.load(boss_path + "fire_circles.gif").convert_alpha()
        except Exception:
            try:
                self.bullet_sprite = pygame.image.load(boss_path + "fire_circles.png").convert_alpha()
            except Exception:
                self.bullet_sprite = None

        # 3 фаз боса
        self.boss_phase_images = []
        try:
            sheet = pygame.image.load(boss_path + "threeformsPJ2.png").convert_alpha()
            w = sheet.get_width() // 3
            h = sheet.get_height()

            for i in range(3):
                frame = sheet.subsurface((i * w, 0, w, h))
                crop_rect = frame.get_bounding_rect(min_alpha=30)
                if crop_rect.width > 0 and crop_rect.height > 0:
                    cropped_frame = frame.subsurface(crop_rect)
                else:
                    cropped_frame = frame
                scaled_frame = pygame.transform.scale(cropped_frame, (100, 120))
                self.boss_phase_images.append(scaled_frame)
        except Exception as e:
            print(f"Не вдалося завантажити threeformsPJ2.png: {e}")
            self.boss_phase_images = [None, None, None]

        # Стан та анімація гравця
        self.max_hp = 100
        self.player_hp = min(hp, self.max_hp)
        self.coins = coins
        self.has_sword = has_sword

        # Базова шкода або підсилена мечем
        self.attack_damage = 110 if self.has_sword else 50

        self.player_rect = Rect(100, floor_y - 60, 32, 48)
        self.walk_speed = 4
        self.run_speed = 7
        self.is_jumping = False
        self.jump_velocity = 0
        self.gravity = 0.8
        self.facing_right = True

        self.player_frames = self._load_player_frames()
        self.anim_index = 0.0
        self.is_moving = False
        self.invincible_timer = 0

        self.is_game_over = False
        self.current_voice_action = "NONE"

        # Характеристики Боса
        self.boss_rect = Rect(screen_width - 180, floor_y - 120, 100, 120)
        self.boss_hp = 3500
        self.boss_max_hp = 3500
        self.boss_speed = 2
        self.boss_phase = 1

        self.last_melee_attack = 0
        self.melee_cooldown = 1000
        self.is_boss_idle = False
        self.idle_start_time = 0

        self.last_bullet_attack = 0
        self.bullet_cooldown = 1000

        self.bullets = []
        self.font = font.Font(None, 26)
        self.boss_font = font.Font(None, 36)
        self.completed = False

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
        if self.is_game_over:
            for e in events:
                if e.type == KEYDOWN and e.key == K_r:
                    self.__init__(self.screen_width, self.screen_height, self.gender, 100, self.coins, self.has_sword)
            return

        self.is_moving = False
        voice_action = audio_controller.get_action() if audio_controller else None
        self.current_voice_action = voice_action if voice_action else "NONE"

        # Голосові команди
        if voice_action == "JUMP" and not self.is_jumping:
            self.is_jumping = True
            self.jump_velocity = -15

        if voice_action == "WALK":
            self.is_moving = True
            if self.facing_right:
                self.player_rect.x += self.walk_speed
            else:
                self.player_rect.x -= self.walk_speed

        if voice_action == "RUN":
            self.is_moving = True
            if self.facing_right:
                self.player_rect.x += self.run_speed
            else:
                self.player_rect.x -= self.run_speed

        # Клавіатура
        if keys[K_a] or keys[K_LEFT]:
            self.player_rect.x -= self.walk_speed
            self.facing_right = False
            self.is_moving = True
        if keys[K_d] or keys[K_RIGHT]:
            self.player_rect.x += self.walk_speed
            self.facing_right = True
            self.is_moving = True

        if self.player_rect.left < 0:
            self.player_rect.left = 0
        if self.player_rect.right > self.screen_width:
            self.player_rect.right = self.screen_width

        for e in events:
            if e.type == KEYDOWN and e.key == K_SPACE and not self.is_jumping:
                self.is_jumping = True
                self.jump_velocity = -15

            if e.type == KEYDOWN and e.key == K_f:
                self.attack()

    def attack(self):
        if self.is_game_over or self.boss_hp <= 0:
            return

        attack_rect = self.player_rect.inflate(70, 20)
        if attack_rect.colliderect(self.boss_rect):
            self.boss_hp -= self.attack_damage
            print(f" Удар по босу! Залишилось HP: {self.boss_hp}/{self.boss_max_hp}")
            if self.boss_hp <= 0:
                self.boss_hp = 0
                print(" БОСА ПОДОЛАНО!")
                self.completed = True

    def apply_damage_to_player(self, amount):
        if self.invincible_timer == 0 and not self.is_game_over:
            self.player_hp = max(0, self.player_hp - amount)
            self.invincible_timer = 45  # Час невагомості/блимання
            if self.player_hp <= 0:
                self.is_game_over = True

    def update_boss_logic(self, current_time):
        if self.boss_hp <= 0:
            return

        # Зміна фаз
        if self.boss_hp > 2200:
            self.boss_phase = 1
        elif self.boss_hp > 1000:
            self.boss_phase = 2
        else:
            self.boss_phase = 3

        # Фаза 1
        if self.boss_phase == 1:
            if self.is_boss_idle:
                if current_time - self.idle_start_time >= self.melee_cooldown:
                    self.is_boss_idle = False
            else:
                if self.boss_rect.x < self.player_rect.x:
                    self.boss_rect.x += self.boss_speed
                else:
                    self.boss_rect.x -= self.boss_speed

                if self.boss_rect.colliderect(self.player_rect):
                    self.apply_damage_to_player(10)
                    self.is_boss_idle = True
                    self.idle_start_time = current_time

        # Фаза 2
        elif self.boss_phase == 2:
            if self.player_rect.centerx < self.screen_width // 2:
                if self.boss_rect.right < self.screen_width - 40:
                    self.boss_rect.x += self.boss_speed
            else:
                if self.boss_rect.left > 40:
                    self.boss_rect.x -= self.boss_speed

            if current_time - self.last_bullet_attack >= self.bullet_cooldown:
                bullet = MagicBullet(self.boss_rect.centerx, self.boss_rect.centery,
                                     self.player_rect.centerx, self.player_rect.centery,
                                     bullet_img=self.bullet_sprite, speed=5)
                self.bullets.append(bullet)
                self.last_bullet_attack = current_time

        # Фаза 3
        elif self.boss_phase == 3:
            if self.is_boss_idle:
                if current_time - self.idle_start_time >= self.melee_cooldown:
                    self.is_boss_idle = False
            else:
                if self.boss_rect.x < self.player_rect.x:
                    self.boss_rect.x += self.boss_speed
                else:
                    self.boss_rect.x -= self.boss_speed

                if self.boss_rect.colliderect(self.player_rect):
                    self.apply_damage_to_player(12)
                    self.is_boss_idle = True
                    self.idle_start_time = current_time

            if current_time - self.last_bullet_attack >= self.bullet_cooldown:
                b1 = MagicBullet(self.boss_rect.centerx, self.boss_rect.centery,
                                 self.player_rect.centerx, self.player_rect.centery,
                                 bullet_img=self.bullet_sprite, speed=6)
                b2 = MagicBullet(self.boss_rect.centerx, self.boss_rect.centery,
                                 self.player_rect.centerx, self.player_rect.centery - 60,
                                 bullet_img=self.bullet_sprite, speed=6)
                self.bullets.append(b1)
                self.bullets.append(b2)
                self.last_bullet_attack = current_time

    def update(self):
        if self.is_game_over:
            return

        self.bg.update()
        current_time = time.get_ticks()

        # Анімація бігу / спокою
        if self.player_frames:
            if self.is_moving:
                self.anim_index = (self.anim_index + 0.15) % len(self.player_frames)
            else:
                self.anim_index = 0

        # Зменшення таймера незахищеності
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # Фізика стрибка
        if self.is_jumping:
            self.player_rect.y += self.jump_velocity
            self.jump_velocity += self.gravity

            if self.player_rect.bottom >= self.ground_rect.top:
                self.player_rect.bottom = self.ground_rect.top
                self.is_jumping = False
                self.jump_velocity = 0

        self.update_boss_logic(current_time)

        # Оновлення куль
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.rect.colliderect(self.player_rect):
                self.apply_damage_to_player(bullet.damage)
                self.bullets.remove(bullet)
            elif bullet.rect.x < -50 or bullet.rect.x > self.screen_width + 50 or bullet.rect.y > self.screen_height:
                self.bullets.remove(bullet)

    def draw(self, window):
        #  Задній фон
        self.bg.draw(window)

        floor_y = self.screen_height - self.ground_height

        # Фіолетова земля
        if self.img_purple_ground:
            tile_w = self.img_purple_ground.get_width()
            for x in range(0, self.screen_width, tile_w):
                window.blit(self.img_purple_ground, (x, floor_y))
        else:
            draw.rect(window, (60, 40, 70), self.ground_rect)

        #  Дерева та квіти на арені
        if self.img_purple_tree:
            window.blit(self.img_purple_tree, (120, floor_y - self.img_purple_tree.get_height()))
            window.blit(self.img_purple_tree, (650, floor_y - self.img_purple_tree.get_height()))

        if self.img_red_flower:
            window.blit(self.img_red_flower, (280, floor_y - self.img_red_flower.get_height()))
            window.blit(self.img_red_flower, (850, floor_y - self.img_red_flower.get_height()))

        if self.img_dry_flower:
            window.blit(self.img_dry_flower, (420, floor_y - self.img_dry_flower.get_height()))
            window.blit(self.img_dry_flower, (1020, floor_y - self.img_dry_flower.get_height()))

        # Відображення Боса залежно від поточної фази
        if self.boss_hp > 0:
            current_boss_img = self.boss_phase_images[self.boss_phase - 1]
            if current_boss_img:
                window.blit(current_boss_img, self.boss_rect.topleft)
            else:
                boss_color = (200, 30, 30) if self.boss_phase == 1 else (
                    (220, 100, 0) if self.boss_phase == 2 else (255, 0, 120))
                draw.rect(window, boss_color, self.boss_rect)

            # HP Боса
            draw.rect(window, (50, 50, 50), (self.screen_width // 2 - 200, 20, 400, 25), border_radius=5)
            hp_bar_width = int((self.boss_hp / self.boss_max_hp) * 396)
            if hp_bar_width > 0:
                draw.rect(window, (220, 30, 30), (self.screen_width // 2 - 198, 22, hp_bar_width, 21), border_radius=4)

            b_text = self.boss_font.render(f"БОС (Фаза {self.boss_phase}): {self.boss_hp} / {self.boss_max_hp}", True,
                                           (255, 255, 255))
            window.blit(b_text, (self.screen_width // 2 - 160, 22))
        else:
            win_text = self.boss_font.render("ПЕРЕМОГА! БОСА ЗНЕШКОДЖЕНО!", True, (100, 255, 100))
            window.blit(win_text, (self.screen_width // 2 - 220, 150))

        # Магічні кулі
        for bullet in self.bullets:
            bullet.draw(window)

        # Відмальовка Персонажа
        if not self.is_game_over:
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

            # Підказка для атаки
            attack_hint = self.font.render("Тисни 'F' для удару!", True, (255, 255, 200))
            window.blit(attack_hint, (self.player_rect.x - 20, self.player_rect.y - 30))
        else:
            game_over_surf = self.font.render("GAME OVER! Натисни R для перезапуску", True, (255, 50, 50))
            window.blit(game_over_surf, (self.screen_width // 2 - 180, self.screen_height // 2))

        # HUD Гравця (HP та монети)
        draw.rect(window, (60, 60, 60), (20, 20, 180, 22), border_radius=4)
        p_hp_width = int((self.player_hp / self.max_hp) * 176)
        if p_hp_width > 0:
            draw.rect(window, (40, 200, 80), (22, 22, p_hp_width, 18), border_radius=4)

        p_hp_text = self.font.render(f"HP: {self.player_hp}/{self.max_hp}", True, (255, 255, 255))
        window.blit(p_hp_text, (210, 22))

        info_surf = self.font.render(f"Голос: {self.current_voice_action}", True, (200, 200, 255))
        window.blit(info_surf, (20, 50))