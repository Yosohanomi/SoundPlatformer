import pygame
from pygame import *

music_volume = 0.5
sfx_volume = 0.5


def play_sfx(path):
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(sfx_volume)
        sound.play()
    except Exception as e:
        print(f"Помилка завантаження/відтворення SFX {path}: {e}")


class SettingsMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_option = 0

        self.font = font.Font(None, 32)
        self.title_font = font.Font(None, 48)

    def _apply_music_volume(self):
        pygame.mixer.music.set_volume(music_volume)

        try:
            pygame.mixer.Channel(0).set_volume(music_volume)
        except Exception:
            pass

    def handle_input(self, events):
        global music_volume, sfx_volume
        for e in events:
            if e.type == KEYDOWN:
                # Перемикання між пунктами
                if e.key == K_UP:
                    self.selected_option = 0
                elif e.key == K_DOWN:
                    self.selected_option = 1

                # Регулювання гучності ВЛІВО
                elif e.key == K_LEFT:
                    if self.selected_option == 0:
                        music_volume = round(max(0.0, music_volume - 0.05), 2)
                        self._apply_music_volume()
                    else:
                        sfx_volume = round(max(0.0, sfx_volume - 0.05), 2)
                        play_sfx("assets/sounds/healspell1.aif")

                # Регулювання гучності ВПРАВО
                elif e.key == K_RIGHT:
                    if self.selected_option == 0:
                        music_volume = round(min(1.0, music_volume + 0.05), 2)
                        self._apply_music_volume()
                    else:
                        sfx_volume = round(min(1.0, sfx_volume + 0.05), 2)
                        play_sfx("assets/sounds/healspell1.aif")

    def draw(self, window):
        overlay = Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(210)
        overlay.fill((15, 15, 25))
        window.blit(overlay, (0, 0))

        title = self.title_font.render("НАЛАШТУВАННЯ ЗВУКУ", True, (255, 255, 255))
        window.blit(title, (self.screen_width // 2 - title.get_width() // 2, 130))

        # ---  РЯДОК МУЗИКИ ---
        m_color = (255, 215, 0) if self.selected_option == 0 else (180, 180, 180)
        m_text = self.font.render(f"Гучність музики: {int(music_volume * 100)}%", True, m_color)
        window.blit(m_text, (self.screen_width // 2 - 150, 220))

        draw.rect(window, (60, 60, 60), (self.screen_width // 2 - 150, 255, 300, 16))
        draw.rect(window, m_color, (self.screen_width // 2 - 150, 255, int(300 * music_volume), 16))

        # ---  РЯДОК ЗВУКІВ СВІТУ (SFX) ---
        s_color = (255, 215, 0) if self.selected_option == 1 else (180, 180, 180)
        s_text = self.font.render(f"Звуки світу (SFX): {int(sfx_volume * 100)}%", True, s_color)
        window.blit(s_text, (self.screen_width // 2 - 150, 310))

        draw.rect(window, (60, 60, 60), (self.screen_width // 2 - 150, 345, 300, 16))
        draw.rect(window, s_color, (self.screen_width // 2 - 150, 345, int(300 * sfx_volume), 16))

        # --- Підказки ---
        hint = self.font.render("↑ / ↓ — обрати пункт  |  ← / → — змінити гучність", True, (160, 160, 180))
        resume_hint = self.font.render("Натисни ESC, щоб повернутися в гру", True, (0, 220, 255))

        window.blit(hint, (self.screen_width // 2 - hint.get_width() // 2, 420))
        window.blit(resume_hint, (self.screen_width // 2 - resume_hint.get_width() // 2, 480))