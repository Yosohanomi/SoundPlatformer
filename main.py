import pygame
from pygame import *
import sys

# Імпортує контролер мікрофона
from audio_input import AudioController

from gender_menu import GenderMenu
from settings_menu import SettingsMenu
import settings_menu
from level1 import Level1
from level2 import Level2
from level3 import Level3
from level4 import Level4

music_channel = None


def play_bg_music(path):
    global music_channel
    try:
        track = pygame.mixer.Sound(path)
        if music_channel is None:
            music_channel = pygame.mixer.Channel(0)

        music_channel.stop()
        music_channel.set_volume(settings_menu.music_volume)
        music_channel.play(track, loops=-1)
        print(f"Музика заграла: {path}")
    except Exception as e:
        print(f"Помилка завантаження {path}: {e}")


def draw_start_menu(window, screen_width, screen_height, font_obj):
    window.fill((15, 20, 30))

    # Назва гри
    title_font = font.Font(None, 60)
    title = title_font.render("2D VOICE PLATFORMER", True, (255, 215, 0))
    window.blit(title, (screen_width // 2 - title.get_width() // 2, 200))

    # Кнопка PLAY
    play_rect = Rect(screen_width // 2 - 100, 350, 200, 60)
    draw.rect(window, (40, 160, 80), play_rect, border_radius=10)
    draw.rect(window, (255, 255, 255), play_rect, 3, border_radius=10)

    play_text = font_obj.render("PLAY", True, (255, 255, 255))
    window.blit(
        play_text,
        (
            play_rect.centerx - play_text.get_width() // 2,
            play_rect.centery - play_text.get_height() // 2,
        ),
    )

    return play_rect


def main():
    pygame.init()
    pygame.mixer.init()

    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 700

    window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("2D Voice-Controlled Game")
    clock = pygame.time.Clock()
    menu_font = font.Font(None, 40)

    # ІНІЦІАЛІЗАЦІЯ МІКРОФОНА
    audio_controller = AudioController()

    # Об'єкти меню
    gender_menu = GenderMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    settings_ui = SettingsMenu(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Початкові параметри гравця для збереження між рівнями
    game_state = "START_MENU"
    previous_state = "START_MENU"

    current_level = None
    level_number = 1
    player_gender = "female"
    player_hp = 100
    player_coins = 0
    has_sword = False
    current_track = ""

    play_bg_music("assets/sounds/lsc_title.mp3")
    current_track = "title"

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            # Вихід з гри
            if event.type == QUIT:
                audio_controller.stop()
                running = False
                pygame.quit()
                sys.exit()

            # Виклик/закриття налаштувань
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                if game_state != "SETTINGS":
                    previous_state = game_state
                    game_state = "SETTINGS"
                    if current_track != "title":
                        play_bg_music("assets/sounds/lsc_title.mp3")
                        current_track = "title"
                else:
                    game_state = previous_state
                    if game_state == "PLAYING":
                        target_track = "boss" if level_number == 3 else "ingame"
                        if current_track != target_track:
                            path = (
                                "assets/sounds/lsc_boss.mp3"
                                if level_number == 3
                                else "assets/sounds/lsc_ingame.mp3"
                            )
                            play_bg_music(path)
                            current_track = target_track

        #  ЛОГІКА СТАНІВ ГРИ

        # КНОПКА PLAY
        if game_state == "START_MENU":
            play_btn = draw_start_menu(
                window, SCREEN_WIDTH, SCREEN_HEIGHT, menu_font
            )

            for event in events:
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if play_btn.collidepoint(event.pos):
                        game_state = "SETTINGS"
                        previous_state = "GENDER_MENU"
                        settings_ui.is_finished = False

        # МЕНЮ НАЛАШТУВАНЬ (ЗВУК ТА МІКРОФОН)
        elif game_state == "SETTINGS":
            settings_ui.handle_input(events)

            if previous_state == "PLAYING" and current_level:
                current_level.draw(window)

            settings_ui.draw(window)

            if getattr(settings_ui, "is_finished", False):
                settings_ui.is_finished = False
                game_state = previous_state

        # МЕНЮ ВИБОРУ СТАТІ
        elif game_state == "GENDER_MENU":
            gender_menu.handle_input(events)
            gender_menu.draw(window)

            if gender_menu.is_finished:
                player_gender = gender_menu.selected_gender
                level_number = 1

                current_level = Level1(
                    SCREEN_WIDTH, SCREEN_HEIGHT, gender=player_gender
                )
                game_state = "PLAYING"

                play_bg_music("assets/sounds/lsc_ingame.mp3")
                current_track = "ingame"

        # ОСНОВНИЙ ІГРОВИЙ ЦИКЛ
        elif game_state == "PLAYING":
            keys = pygame.key.get_pressed()

            current_level.handle_input(
                keys, events, audio_controller=audio_controller
            )
            current_level.update()

            # ЛОГІКА ПЕРЕХОДУ МІЖ РІВНЯМИ
            if current_level.completed:
                player_hp = getattr(current_level, "player_hp", player_hp)
                player_coins = getattr(current_level, "coins", player_coins)
                has_sword = getattr(current_level, "has_sword", has_sword)

                if level_number == 1:
                    print(">>> Перехід на Level 2 (Крамниця)...")
                    level_number = 2
                    current_level = Level2(
                        SCREEN_WIDTH,
                        SCREEN_HEIGHT,
                        gender=player_gender,
                        hp=player_hp,
                        coins=player_coins,
                    )

                elif level_number == 2:
                    print(">>> Перехід на Level 3 (Фінальний бос)...")
                    level_number = 3
                    current_level = Level3(
                        SCREEN_WIDTH,
                        SCREEN_HEIGHT,
                        gender=player_gender,
                        hp=player_hp,
                        coins=player_coins,
                        has_sword=has_sword,
                    )

                    play_bg_music("assets/sounds/lsc_boss.mp3")
                    current_track = "boss"

                elif level_number == 3:
                    print(">>> Перехід на Level 4 (Епілог/Фінал)...")
                    level_number = 4
                    current_level = Level4(
                        SCREEN_WIDTH, SCREEN_HEIGHT, gender=player_gender
                    )

                    play_bg_music("assets/sounds/lsc_ingame.mp3")
                    current_track = "ingame"

            current_level.draw(window)

        pygame.display.flip()
        clock.tick(60)

    # Вихід
    audio_controller.stop()
    pygame.quit()

if __name__ == "__main__":
    main()