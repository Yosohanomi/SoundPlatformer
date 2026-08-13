import pygame


def load_teleport_frames(filepath, target_height=90):
    try:
        raw_img = pygame.image.load(filepath).convert_alpha()
        rect = raw_img.get_bounding_rect(min_alpha=50)
        cropped_all = raw_img.subsurface(rect)
        frame_w = cropped_all.get_width() // 3
        frame_h = cropped_all.get_height()

        frames = []
        for i in range(3):
            sub = cropped_all.subsurface((i * frame_w, 0, frame_w, frame_h))

            sub_rect = sub.get_bounding_rect(min_alpha=50)
            if sub_rect.width > 0 and sub_rect.height > 0:
                frame_trimmed = sub.subsurface(sub_rect)
            else:
                frame_trimmed = sub

            aspect_ratio = frame_trimmed.get_width() / frame_trimmed.get_height()
            new_w = int(target_height * aspect_ratio)
            scaled = pygame.transform.scale(frame_trimmed, (max(10, new_w), target_height))
            frames.append(scaled)

        return frames
    except Exception as e:
        print(f" Помилка завантаження порталів: {e}")
        return []


class Teleport(pygame.sprite.Sprite):
    def __init__(self, x, y, frames, activation_radius=130):
        super().__init__()
        self.frames = frames  # 3 кадри: [0 - закритий, 1 - піввідкритий, 2 - відкритий]
        self.current_frame = 0.0
        self.anim_speed = 0.15

        self.activation_radius = activation_radius

        if self.frames:
            self.image = self.frames[0]
        else:
            self.image = pygame.Surface((30, 80))
            self.image.fill((150, 0, 200))

        self.base_midbottom = (x, y)
        self.rect = self.image.get_rect(midbottom=self.base_midbottom)

    def update(self, player_rect):
        if not self.frames:
            return

        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance <= self.activation_radius:
            if self.current_frame < len(self.frames) - 1:
                self.current_frame += self.anim_speed
                if self.current_frame > len(self.frames) - 1:
                    self.current_frame = float(len(self.frames) - 1)
        else:
            if self.current_frame > 0:
                self.current_frame -= self.anim_speed
                if self.current_frame < 0:
                    self.current_frame = 0.0

        frame_idx = int(self.current_frame)
        self.image = self.frames[frame_idx]

        self.rect = self.image.get_rect(midbottom=self.base_midbottom)

    def is_fully_open(self):
        return int(self.current_frame) == len(self.frames) - 1