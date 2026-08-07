import os
import pygame
import sys
import random
import time
import numpy as np
import cv2  # <-- для видео (заставки/меню, взято из AkanoID)
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *

# Инициализация Pygame и OpenGL
pygame.init()

# ============================== КОНСТАНТЫ ==============================
WIDTH, HEIGHT = 1260, 800
FPS = 60

# Параметры поля Тетриса
COLS, ROWS = 10, 20
CELL = 32
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
BOARD_X = (WIDTH - BOARD_W) // 2 - 90
BOARD_Y = (HEIGHT - BOARD_H) // 2 + 10

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
BROWN = (165, 42, 42)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
GRAY = (50, 50, 50)
LIGHT_BLUE = (100, 100, 200)
DARK_RED = (139, 0, 0)
COLORS = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN, PINK, BROWN]

# Создание окна с OpenGL
pygame.display.gl_set_attribute(GL_ACCELERATED_VISUAL, 1)
pygame.display.set_mode((WIDTH, HEIGHT), HWSURFACE | DOUBLEBUF | OPENGL)
pygame.display.set_caption("Tetris9K - my game")
info = pygame.display.Info()
print(info)
clock = pygame.time.Clock()

# Настройка OpenGL
glViewport(0, 0, WIDTH, HEIGHT)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

# Включение смешивания для прозрачности
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Глобальная переменная для состояния музыки
music_playing = True
current_music = None

# Глобальные переменные для настроек (уровень = стартовая скорость падения, как в классическом Тетрисе)
selected_level = 1
max_level = 20

# Глобальная переменная для игрового фона
game_background_texture = None

# ============================== ЗВУКИ ==============================
try:
    # Звук перемещения фигуры
    move_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.1)) for x in range(1500)]))
    move_sound.set_volume(0.2)
    # Звук поворота фигуры
    rotate_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.17)) for x in range(2200)]))
    rotate_sound.set_volume(0.3)
    # Звук приземления фигуры
    lock_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.2)) for x in range(2205)]))
    lock_sound.set_volume(0.35)
    # Звук очистки линии(й)
    line_clear_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.05)) for x in range(6615)]))
    line_clear_sound.set_volume(0.55)
    # Звук тетриса (очистка 4 линий разом)
    tetris_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.03)) for x in range(9000)]))
    tetris_sound.set_volume(0.65)
    # Звук хард-дропа
    hard_drop_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.25)) for x in range(1600)]))
    hard_drop_sound.set_volume(0.4)
    # Звук повышения уровня
    level_up_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.15)) for x in range(4200)]))
    level_up_sound.set_volume(0.6)
    # Звук удержания фигуры (hold)
    hold_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.3)) for x in range(1800)]))
    hold_sound.set_volume(0.35)
    # Звук завершения игры
    game_over_sound = pygame.mixer.Sound(buffer=bytearray([127 + int(127 * np.sin(x * 0.08)) for x in range(8000)]))
    game_over_sound.set_volume(0.6)

    def load_background_music():
        music_files = [
            'music.mp3', 'background.mp3', 'game_music.mp3',
            'soundtrack.mp3', 'tetris_music.mp3'
        ]
        for music_file in music_files:
            if os.path.exists(music_file):
                try:
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.set_volume(0.5)
                    print(f"Загружена музыка: {music_file}")
                    return True
                except Exception as e:
                    print(f"Ошибка загрузки {music_file}: {e}")
        print("MP3 файлы не найдены. Музыка недоступна.")
        return False

    music_loaded = load_background_music()

except Exception as e:
    print(f"Ошибка загрузки звуков: {e}")

    class DummySound:
        def play(self): pass
        def set_volume(self, vol): pass
        def stop(self): pass

    move_sound = DummySound()
    rotate_sound = DummySound()
    lock_sound = DummySound()
    line_clear_sound = DummySound()
    tetris_sound = DummySound()
    hard_drop_sound = DummySound()
    level_up_sound = DummySound()
    hold_sound = DummySound()
    game_over_sound = DummySound()
    music_loaded = False

# Функция для управления музыкой
def toggle_music():
    global music_playing
    music_playing = not music_playing
    if music_playing:
        if music_loaded:
            pygame.mixer.music.play(loops=-1)
    else:
        pygame.mixer.music.stop()

# ============================== ТЕКСТУРЫ / OPENGL РИСОВАНИЕ ==============================
# (взято из AkanoID без изменений — используется для заставки, фона и UI)

def load_texture(image_path):
    try:
        surface = pygame.image.load(image_path)
        surface = surface.convert_alpha()
        texture_data = pygame.image.tostring(surface, "RGBA", False)
        width = surface.get_width()
        height = surface.get_height()
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        return texture_id, width, height
    except Exception as e:
        print(f"Ошибка загрузки изображения {image_path}: {e}")
        return None, 0, 0

def draw_texture(texture_id, x, y, width, height, alpha=1.0):
    if texture_id is None:
        return
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor4f(1.0, 1.0, 1.0, alpha)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(x, y)
    glTexCoord2f(1.0, 0.0); glVertex2f(x + width, y)
    glTexCoord2f(1.0, 1.0); glVertex2f(x + width, y + height)
    glTexCoord2f(0.0, 1.0); glVertex2f(x, y + height)
    glEnd()
    glDisable(GL_TEXTURE_2D)

def draw_rect(x, y, width, height, color, alpha=1.0):
    r, g, b = color[0]/255.0, color[1]/255.0, color[2]/255.0
    glColor4f(r, g, b, alpha)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

def draw_circle(x, y, radius, color, segments=32):
    r, g, b = color[0]/255.0, color[1]/255.0, color[2]/255.0
    glColor3f(r, g, b)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    for i in range(segments + 1):
        angle = 2 * np.pi * i / segments
        glVertex2f(x + radius * np.cos(angle), y + radius * np.sin(angle))
    glEnd()

def draw_gradient_rect(x, y, width, height, color1, color2):
    r1, g1, b1 = color1[0]/255.0, color1[1]/255.0, color1[2]/255.0
    r2, g2, b2 = color2[0]/255.0, color2[1]/255.0, color2[2]/255.0
    glBegin(GL_QUADS)
    glColor3f(r1, g1, b1)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glColor3f(r2, g2, b2)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

def draw_rounded_rect(x, y, width, height, radius, color, alpha=1.0):
    # Защита: радиус не может быть больше половины меньшей стороны, иначе
    # внутренние прямоугольники "схлопываются" и геометрия самопересекается.
    radius = max(0.0, min(radius, width / 2.0, height / 2.0))
    r, g, b = color[0]/255.0, color[1]/255.0, color[2]/255.0
    glColor4f(r, g, b, alpha)
    glBegin(GL_QUADS)
    glVertex2f(x + radius, y)
    glVertex2f(x + width - radius, y)
    glVertex2f(x + width - radius, y + height)
    glVertex2f(x + radius, y + height)
    glEnd()
    glBegin(GL_QUADS)
    glVertex2f(x, y + radius)
    glVertex2f(x + width, y + radius)
    glVertex2f(x + width, y + height - radius)
    glVertex2f(x, y + height - radius)
    glEnd()
    segments = 12
    # Внимание: в системе координат экрана Y растёт вниз, поэтому для каждого
    # угла дуга должна идти строго между двумя своими смежными сторонами.
    # (В исходном коде AkanoID эти диапазоны углов были перепутаны для 3 из 4
    # углов, что и давало "лепестковый" артефакт вместо ровного скругления.)
    corners = [
        (x + radius, y + radius, np.pi, 3 * np.pi / 2),                  # верхний левый
        (x + width - radius, y + radius, -np.pi / 2, 0),                 # верхний правый
        (x + width - radius, y + height - radius, 0, np.pi / 2),         # нижний правый
        (x + radius, y + height - radius, np.pi / 2, np.pi),             # нижний левый
    ]
    for cx, cy, a_start, a_end in corners:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for i in range(segments + 1):
            angle = a_start + (a_end - a_start) * i / segments
            glVertex2f(cx + radius * np.cos(angle), cy + radius * np.sin(angle))
        glEnd()

def draw_rounded_rect_shaded(x, y, width, height, radius, color, alpha=1.0,
                              light_amount=0.55, dark_amount=0.55):
    """Скруглённый прямоугольник с полноценным вертикальным градиентом
    (светлый верх -> тёмный низ), а не просто мелким полупрозрачным бликом.
    Такой градиент даёт хорошо заметный объём на ЛЮБОМ цвете, в отличие от
    маленького пятна-блика, которое на некоторых цветах почти не видно."""
    radius = max(0.0, min(radius, width / 2.0, height / 2.0))
    light = lighten_color(color, light_amount)
    dark = tuple(int(v * (1.0 - dark_amount)) for v in color)

    def lerp(c1, c2, t):
        return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))

    def set_color(c):
        glColor4f(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, alpha)

    # Центральная вертикальная полоса (без скруглённых уголков слева/справа) -
    # полный градиент от светлого верха до тёмного низа
    glBegin(GL_QUADS)
    set_color(light); glVertex2f(x + radius, y)
    set_color(light); glVertex2f(x + width - radius, y)
    set_color(dark);  glVertex2f(x + width - radius, y + height)
    set_color(dark);  glVertex2f(x + radius, y + height)
    glEnd()

    # Центральная горизонтальная полоса (без скруглённых уголков сверху/снизу) -
    # цвет в её верхнем и нижнем крае берётся из той же градиентной шкалы,
    # чтобы стык с вертикальной полосой был плавным, без видимых границ
    t_top = radius / height
    t_bot = (height - radius) / height
    top_color = lerp(light, dark, t_top)
    bot_color = lerp(light, dark, t_bot)
    glBegin(GL_QUADS)
    set_color(top_color); glVertex2f(x, y + radius)
    set_color(top_color); glVertex2f(x + width, y + radius)
    set_color(bot_color); glVertex2f(x + width, y + height - radius)
    set_color(bot_color); glVertex2f(x, y + height - radius)
    glEnd()

    segments = 12
    corners = [
        (x + radius, y + radius, np.pi, 3 * np.pi / 2, t_top),                  # верхний левый
        (x + width - radius, y + radius, -np.pi / 2, 0, t_top),                 # верхний правый
        (x + width - radius, y + height - radius, 0, np.pi / 2, t_bot),         # нижний правый
        (x + radius, y + height - radius, np.pi / 2, np.pi, t_bot),             # нижний левый
    ]
    for cx, cy, a_start, a_end, t in corners:
        set_color(lerp(light, dark, t))
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for i in range(segments + 1):
            angle = a_start + (a_end - a_start) * i / segments
            glVertex2f(cx + radius * np.cos(angle), cy + radius * np.sin(angle))
        glEnd()

_font_cache = {}
_text_texture_cache = {}

def _get_font(size):
    font = _font_cache.get(size)
    if font is None:
        font = pygame.font.SysFont('Arial', size, bold=True)
        _font_cache[size] = font
    return font

def draw_text(text, x, y, color=WHITE, size=24, mirrored=False):
    cache_key = (text, size, color, mirrored)
    cached = _text_texture_cache.get(cache_key)
    if cached is None:
        font = _get_font(size)
        text_surface = font.render(text, True, color)
        if mirrored:
            text_surface = pygame.transform.flip(text_surface, False, False)
        text_data = pygame.image.tostring(text_surface, "RGBA", False)
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_surface.get_width(), text_surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        cached = (tex_id, text_surface.get_width(), text_surface.get_height())
        _text_texture_cache[cache_key] = cached
        if len(_text_texture_cache) > 300:
            old_key, (old_tex, _, _) = _text_texture_cache.popitem()
            glDeleteTextures([old_tex])

    tex_id, w, h = cached
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x, y)
    glTexCoord2f(1, 0); glVertex2f(x + w, y)
    glTexCoord2f(1, 1); glVertex2f(x + w, y + h)
    glTexCoord2f(0, 1); glVertex2f(x, y + h)
    glEnd()
    glDisable(GL_TEXTURE_2D)

def lighten_color(color, amount=0.55):
    """Осветляет цвет, смешивая его с белым, а не прибавляя число к каналам.
    Это гарантирует заметный блик даже там, где 1-2 канала цвета уже максимальны
    (циан, зелёный, жёлтый, синий, красный) - раньше в таких случаях блик
    почти сливался с основным цветом, и фигура выглядела "плоской"."""
    return tuple(int(v + (255 - v) * amount) for v in color)


class Particle:
    def __init__(self, x, y, color, velocity=None, size=3, lifetime=60):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.velocity = velocity if velocity else [random.uniform(-2, 2), random.uniform(-2, 2)]

    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.lifetime -= 1
        self.size *= 0.95
        return self.lifetime > 0

    def draw(self):
        alpha = self.lifetime / self.max_lifetime
        r, g, b = self.color[0]/255.0, self.color[1]/255.0, self.color[2]/255.0
        glColor4f(r, g, b, alpha)
        glPointSize(self.size)
        glBegin(GL_POINTS)
        glVertex2f(self.x, self.y)
        glEnd()

def draw_background():
    global game_background_texture
    if game_background_texture is not None:
        draw_texture(game_background_texture, 0, 0, WIDTH, HEIGHT)
    else:
        glClearColor(0.05, 0.05, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glBegin(GL_QUADS)
        glColor3f(0.05, 0.05, 0.15)
        glVertex2f(0, 0)
        glVertex2f(WIDTH, 0)
        glColor3f(0.1, 0.1, 0.2)
        glVertex2f(WIDTH, HEIGHT)
        glVertex2f(0, HEIGHT)
        glEnd()
        glPointSize(1.5)
        glBegin(GL_POINTS)
        for i in range(100):
            x = (i * 137) % WIDTH
            y = (i * 97) % HEIGHT
            intensity = 0.3 + 0.7 * (i % 3) / 2
            flicker = np.sin(pygame.time.get_ticks() * 0.001 + i) * 0.2 + 0.8
            glColor3f(intensity * flicker, intensity * flicker, intensity * flicker + 0.1)
            glVertex2f(x, y)
        glEnd()
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for i in range(50):
            x = (i * 73) % WIDTH
            y = (pygame.time.get_ticks() * 0.05 + i * 20) % HEIGHT
            color_val = (i % 3) / 2
            alpha = 0.3 + 0.4 * np.sin(pygame.time.get_ticks() * 0.002 + i)
            glColor4f(color_val, color_val * 0.7, 1.0, alpha)
            glVertex2f(x, y)
        glEnd()

# ============================== ЛОГИКА ТЕТРИСА ==============================

# Стандартные фигуры (SRS-подобные состояния поворота 0/R/2/L), координаты в клетках 4x4
SHAPES = {
    'I': {
        'color': CYAN,
        'rotations': [
            [(0, 1), (1, 1), (2, 1), (3, 1)],
            [(2, 0), (2, 1), (2, 2), (2, 3)],
            [(0, 2), (1, 2), (2, 2), (3, 2)],
            [(1, 0), (1, 1), (1, 2), (1, 3)],
        ]
    },
    'O': {
        'color': YELLOW,
        'rotations': [
            [(1, 0), (2, 0), (1, 1), (2, 1)],
        ] * 4
    },
    'T': {
        'color': PURPLE,
        'rotations': [
            [(1, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (1, 2)],
            [(1, 0), (0, 1), (1, 1), (1, 2)],
        ]
    },
    'S': {
        'color': GREEN,
        'rotations': [
            [(1, 0), (2, 0), (0, 1), (1, 1)],
            [(1, 0), (1, 1), (2, 1), (2, 2)],
            [(1, 1), (2, 1), (0, 2), (1, 2)],
            [(0, 0), (0, 1), (1, 1), (1, 2)],
        ]
    },
    'Z': {
        'color': RED,
        'rotations': [
            [(0, 0), (1, 0), (1, 1), (2, 1)],
            [(2, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (1, 2), (2, 2)],
            [(1, 0), (0, 1), (1, 1), (0, 2)],
        ]
    },
    'J': {
        'color': BLUE,
        'rotations': [
            [(0, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (2, 0), (1, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (2, 2)],
            [(1, 0), (1, 1), (0, 2), (1, 2)],
        ]
    },
    'L': {
        'color': ORANGE,
        'rotations': [
            [(2, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (1, 2), (2, 2)],
            [(0, 1), (1, 1), (2, 1), (0, 2)],
            [(0, 0), (1, 0), (1, 1), (1, 2)],
        ]
    },
}
PIECE_KEYS = list(SHAPES.keys())

# Скорость падения (кадров на клетку) по уровню - чем выше уровень, тем быстрее
def frames_per_drop(level):
    level = max(1, min(20, level))
    base = 48
    speed = base - (level - 1) * 2.2
    return max(4, speed)

SCORE_TABLE = {1: 100, 2: 300, 3: 500, 4: 800}


class TetrisPiece:
    def __init__(self, kind, col=3, row=-1, rotation=0):
        self.kind = kind
        self.color = SHAPES[kind]['color']
        self.rotation = rotation
        self.col = col
        self.row = row
        # Плавающие координаты для плавной анимации падения/движения -
        # логика (col/row) остаётся целочисленной для коллизий, а visual_*
        # "догоняет" её каждый кадр, создавая плавное скольжение.
        self.visual_col = float(col)
        self.visual_row = float(row)

    def snap_visual(self):
        """Мгновенно синхронизировать визуальную позицию с логической (без анимации)."""
        self.visual_col = float(self.col)
        self.visual_row = float(self.row)

    def ease_visual(self, factor_col=0.45, factor_row=0.35):
        """Один шаг плавной анимации в сторону текущей логической позиции."""
        self.visual_col += (self.col - self.visual_col) * factor_col
        self.visual_row += (self.row - self.visual_row) * factor_row
        if abs(self.col - self.visual_col) < 0.01:
            self.visual_col = float(self.col)
        if abs(self.row - self.visual_row) < 0.01:
            self.visual_row = float(self.row)

    def cells(self, rotation=None):
        rot = self.rotation if rotation is None else rotation
        return SHAPES[self.kind]['rotations'][rot % 4]

    def occupied(self, rotation=None, col=None, row=None):
        rot = self.rotation if rotation is None else rotation
        c0 = self.col if col is None else col
        r0 = self.row if row is None else row
        return [(c0 + cx, r0 + cy) for (cx, cy) in self.cells(rot)]


class SevenBag:
    """Генератор фигур по системе '7-bag' - как в современном Тетрисе:
    каждая из 7 фигур выпадает ровно один раз за 'мешок', порядок случайный."""
    def __init__(self):
        self.bag = []

    def next(self):
        if not self.bag:
            self.bag = PIECE_KEYS[:]
            random.shuffle(self.bag)
        return self.bag.pop()


class LineClearEffect:
    """Анимация вспышки очищаемой линии перед её исчезновением."""
    def __init__(self, row, y):
        self.row = row
        self.y = y
        self.lifetime = 14
        self.max_lifetime = 14

    def update(self):
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self):
        alpha = self.lifetime / self.max_lifetime
        draw_rect(BOARD_X, self.y, BOARD_W, CELL, WHITE, alpha=alpha * 0.9)


class TetrisBoard:
    def __init__(self, start_level=1):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.bag = SevenBag()
        self.hold_kind = None
        self.hold_used = False
        self.next_queue = [self.bag.next() for _ in range(3)]
        self.current = None
        self.spawn_piece()
        self.start_level = start_level
        self.level = start_level
        self.score = 0
        self.lines_cleared = 0
        self.combo = -1
        self.drop_timer = 0
        self.lock_timer = 0
        self.locking = False
        self.soft_drop = False
        self.game_over = False
        self.clear_effects = []
        self.particles = []
        self.das_timer = {'left': 0, 'right': 0}
        self.last_move_dir = None

    # ---------------- spawn / queue ----------------
    def spawn_piece(self):
        kind = self.next_queue.pop(0)
        self.next_queue.append(self.bag.next())
        piece = TetrisPiece(kind, col=3, row=-1, rotation=0)
        if kind == 'I':
            piece.row = -1
        if kind == 'O':
            piece.col = 4
        piece.snap_visual()
        self.current = piece
        self.hold_used = False
        self.lock_timer = 0
        self.locking = False
        if self.collides(piece):
            self.game_over = True
            game_over_sound.play()

    def hold(self):
        if self.hold_used or self.current is None:
            return
        hold_sound.play()
        if self.hold_kind is None:
            self.hold_kind = self.current.kind
            self.spawn_piece()
        else:
            new_kind = self.hold_kind
            self.hold_kind = self.current.kind
            self.current = TetrisPiece(new_kind, col=3, row=-1, rotation=0)
            if new_kind == 'O':
                self.current.col = 4
            self.current.snap_visual()
            self.lock_timer = 0
            self.locking = False
        self.hold_used = True

    # ---------------- collision helpers ----------------
    def collides(self, piece, col=None, row=None, rotation=None):
        for (cx, cy) in piece.occupied(rotation, col, row):
            if cx < 0 or cx >= COLS or cy >= ROWS:
                return True
            if cy >= 0 and self.grid[cy][cx] is not None:
                return True
        return False

    def try_move(self, dcol, drow):
        p = self.current
        if not self.collides(p, col=p.col + dcol, row=p.row + drow):
            p.col += dcol
            p.row += drow
            if self.locking:
                self.lock_timer = 0
            return True
        return False

    def try_rotate(self, direction=1):
        p = self.current
        new_rot = (p.rotation + direction) % 4
        # простые смещения (wall-kicks) для проверки нескольких позиций
        kicks = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]
        for (dx, dy) in kicks:
            if not self.collides(p, col=p.col + dx, row=p.row + dy, rotation=new_rot):
                p.col += dx
                p.row += dy
                p.rotation = new_rot
                rotate_sound.play()
                if self.locking:
                    self.lock_timer = 0
                return True
        return False

    def ghost_row(self):
        p = self.current
        row = p.row
        while not self.collides(p, row=row + 1):
            row += 1
        return row

    def hard_drop(self):
        p = self.current
        drop_dist = self.ghost_row() - p.row
        p.row = self.ghost_row()
        self.score += drop_dist * 2
        hard_drop_sound.play()
        self.lock_piece()

    def soft_drop_step(self):
        if not self.try_move(0, 1):
            return False
        self.score += 1
        return True

    # ---------------- locking / clearing ----------------
    def lock_piece(self):
        p = self.current
        for (cx, cy) in p.occupied():
            if 0 <= cy < ROWS and 0 <= cx < COLS:
                self.grid[cy][cx] = p.color
        lock_sound.play()
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        full_rows = [r for r in range(ROWS) if all(self.grid[r][c] is not None for c in range(COLS))]
        if not full_rows:
            self.combo = -1
            return
        for r in full_rows:
            self.clear_effects.append(LineClearEffect(r, BOARD_Y + r * CELL))
            for c in range(COLS):
                color = self.grid[r][c]
                self.particles.append(Particle(
                    BOARD_X + c * CELL + CELL / 2, BOARD_Y + r * CELL + CELL / 2,
                    color if color else WHITE,
                    [random.uniform(-2.5, 2.5), random.uniform(-3.5, -0.5)], 4, 40
                ))

        n = len(full_rows)
        new_grid = [row for r, row in enumerate(self.grid) if r not in full_rows]
        for _ in range(n):
            new_grid.insert(0, [None for _ in range(COLS)])
        self.grid = new_grid

        self.combo += 1
        base = SCORE_TABLE.get(n, 100 * n)
        combo_bonus = max(0, self.combo) * 50
        self.score += base * self.level + combo_bonus
        self.lines_cleared += n

        if n >= 4:
            tetris_sound.play()
        else:
            line_clear_sound.play()

        new_level = self.start_level + self.lines_cleared // 10
        if new_level != self.level:
            self.level = min(20, new_level)
            level_up_sound.play()

    # ---------------- update / input ----------------
    def update(self, dt_frames=1):
        if self.game_over:
            self.particles = [pt for pt in self.particles if pt.update()]
            self.clear_effects = [e for e in self.clear_effects if e.update()]
            return

        self.particles = [pt for pt in self.particles if pt.update()]
        self.clear_effects = [e for e in self.clear_effects if e.update()]

        p = self.current
        on_ground = self.collides(p, row=p.row + 1)

        if on_ground:
            self.locking = True
            self.lock_timer += dt_frames
            if self.lock_timer >= 30:
                self.lock_piece()
                # self.current is now a brand-new piece (already snapped to its
                # spawn position), so easing it here is a harmless no-op.
                self.current.ease_visual()
                return
        else:
            self.locking = False
            self.lock_timer = 0
            self.drop_timer += dt_frames
            threshold = frames_per_drop(self.level) if not self.soft_drop else 2
            if self.drop_timer >= threshold:
                self.drop_timer = 0
                self.try_move(0, 1)

        # Плавно "подтягиваем" визуальную позицию фигуры к её логической
        # клетке — именно это даёт плавное скольжение при падении и сдвигах,
        # вместо мгновенных прыжков на целую клетку.
        self.current.ease_visual()

    def draw(self):
        # Панель поля
        draw_rounded_rect(BOARD_X - 6, BOARD_Y - 6, BOARD_W + 12, BOARD_H + 12, 8, (10, 10, 18), alpha=0.55)
        draw_rect(BOARD_X, BOARD_Y, BOARD_W, BOARD_H, (0, 0, 0), alpha=0.35)

        # Сетка
        for c in range(COLS + 1):
            x = BOARD_X + c * CELL
            glColor4f(1, 1, 1, 0.06)
            glBegin(GL_LINES)
            glVertex2f(x, BOARD_Y)
            glVertex2f(x, BOARD_Y + BOARD_H)
            glEnd()
        for r in range(ROWS + 1):
            y = BOARD_Y + r * CELL
            glColor4f(1, 1, 1, 0.06)
            glBegin(GL_LINES)
            glVertex2f(BOARD_X, y)
            glVertex2f(BOARD_X + BOARD_W, y)
            glEnd()

        # Зафиксированные блоки
        for r in range(ROWS):
            for c in range(COLS):
                color = self.grid[r][c]
                if color is not None:
                    self.draw_cell(c, r, color)

        # Тень (ghost) текущей фигуры - от логической (не визуальной) позиции,
        # чтобы она всегда точно показывала, куда упадёт фигура
        if not self.game_over:
            ghost_r = self.ghost_row()
            for (cx, cy) in self.current.cells():
                gy = ghost_r + cy
                if gy >= 0:
                    self.draw_cell(self.current.col + cx, gy, self.current.color, ghost=True)

            # Текущая фигура - рисуется по плавным (visual) координатам, а не по
            # целочисленным col/row, поэтому падение и сдвиги выглядят плавно
            for (cx, cy) in self.current.cells():
                vy = self.current.visual_row + cy
                if vy >= -1:
                    self.draw_cell(self.current.visual_col + cx, vy, self.current.color)

        for effect in self.clear_effects:
            effect.draw()

        for particle in self.particles:
            particle.draw()

    def draw_cell(self, col, row, color, ghost=False):
        # col/row могут быть float (плавная анимация), поэтому позиция в
        # пикселях просто масштабируется - без округления до целой клетки.
        x = BOARD_X + col * CELL
        y = BOARD_Y + row * CELL
        pad = 2.2
        radius = 7
        size = CELL - 2 * pad

        if ghost:
            # Тень (превью посадки фигуры) - тот же градиентный объём, но
            # полупрозрачный, чтобы явно отличаться от настоящего блока
            draw_rounded_rect(x + pad - 2, y + pad - 2, size + 4, size + 4, radius + 2, color, alpha=0.10)
            draw_rounded_rect_shaded(x + pad, y + pad, size, size, radius, color, alpha=0.38)
            return

        # Мягкая тень под блоком - усиливает ощущение объёма
        draw_rounded_rect(x + pad + 1.5, y + pad + 2.5, size, size, radius, (0, 0, 0), alpha=0.28)
        # Основное тело блока - полный вертикальный градиент (светлый верх ->
        # тёмный низ), а не маленький блик, поэтому объём хорошо виден на любом цвете
        draw_rounded_rect_shaded(x + pad, y + pad, size, size, radius, color)
        # Тонкая яркая кромка сверху-слева - имитация отражения света, добавляет "глянца"
        rim = lighten_color(color, 0.75)
        glColor4f(rim[0] / 255.0, rim[1] / 255.0, rim[2] / 255.0, 0.55)
        glBegin(GL_LINE_STRIP)
        glVertex2f(x + pad + size * 0.18, y + pad + size - size * 0.12)
        glVertex2f(x + pad + size * 0.06, y + pad + size * 0.35)
        glVertex2f(x + pad + size * 0.18, y + pad + size * 0.06)
        glVertex2f(x + pad + size * 0.65, y + pad + size * 0.06)
        glEnd()


def draw_mini_piece(kind, x, y, cell=20):
    """Рисует миниатюру фигуры (со скруглёнными блоками) для панели Next / Hold."""
    color = SHAPES[kind]['color']
    cells = SHAPES[kind]['rotations'][0]
    min_cx = min(c for c, _ in cells)
    max_cx = max(c for c, _ in cells)
    min_cy = min(r for _, r in cells)
    max_cy = max(r for _, r in cells)
    w = (max_cx - min_cx + 1) * cell
    h = (max_cy - min_cy + 1) * cell
    ox = x - w / 2
    oy = y - h / 2
    pad = 1.5
    radius = min(5, cell * 0.3)
    for (cx, cy) in cells:
        px = ox + (cx - min_cx) * cell
        py = oy + (cy - min_cy) * cell
        size = cell - 2 * pad
        draw_rounded_rect_shaded(px + pad, py + pad, size, size, radius, color)

# ============================== МЕНЮ С ВИДЕО (intro.mp4 / settings.mp4) ==============================
# Логика взята из AkanoID практически без изменений — те же видео-заставки и та же навигация,
# только пункт "Level" теперь означает стартовый уровень скорости Тетриса (1-20).

def show_menu():
    global music_playing, selected_level

    menu_items = ["Play", "Settings", "Exit"]
    settings_items = ["Start level: {} / 20".format(selected_level), "Music: On" if music_playing else "Music: Off", "Back"]
    current_menu = "main"
    selected_item = 0
    menu_fps = 30
    main_video_path = 'intro.mp4'
    settings_video_path = 'settings.mp4'

    main_cap = None
    settings_cap = None

    if os.path.exists(main_video_path):
        main_cap = cv2.VideoCapture(main_video_path)
        if not main_cap.isOpened():
            main_cap = None
            print("Не удалось открыть видеофайл intro.mp4")
    else:
        print("Видео intro.mp4 не найдено. Используется стандартный фон.")

    if os.path.exists(settings_video_path):
        settings_cap = cv2.VideoCapture(settings_video_path)
        if not settings_cap.isOpened():
            settings_cap = None
            print("Не удалось открыть видеофайл settings.mp4")
    else:
        print("Видео settings.mp4 не найдено. Будет использоваться intro.mp4 для настроек")
        if main_cap is not None:
            settings_cap = cv2.VideoCapture(main_video_path)

    if music_loaded and music_playing:
        pygame.mixer.music.play(loops=-1)

    menu_video_texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, menu_video_texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    menu_running = True
    while menu_running:
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        current_cap = main_cap if current_menu == "main" else settings_cap

        if current_cap is not None:
            ret, frame = current_cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                texture_data = frame.tobytes()
                glBindTexture(GL_TEXTURE_2D, menu_video_texture_id)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH, HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)

                glEnable(GL_TEXTURE_2D)
                glColor3f(1.0, 1.0, 1.0)
                glBegin(GL_QUADS)
                glTexCoord2f(0.0, 0.0); glVertex2f(0, 0)
                glTexCoord2f(1.0, 0.0); glVertex2f(WIDTH, 0)
                glTexCoord2f(1.0, 1.0); glVertex2f(WIDTH, HEIGHT)
                glTexCoord2f(0.0, 1.0); glVertex2f(0, HEIGHT)
                glEnd()
                glDisable(GL_TEXTURE_2D)
            else:
                current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        else:
            if current_menu == "main":
                draw_text("File intro.mp4 not found", WIDTH//2 - 150, HEIGHT//2 - 20, WHITE, 24)
            else:
                draw_text("File settings.mp4 not found", WIDTH//2 - 150, HEIGHT//2 - 20, WHITE, 24)

        if current_menu == "main":
            items = menu_items
            start_y = 350
        else:
            items = settings_items
            start_y = 300
            if selected_item == 0:
                hint_y = start_y + len(items) * 60 + 40
                hint_text = "< / > to change starting level"
                draw_text(hint_text, WIDTH//2 - 150, hint_y, CYAN, 18)

        for i, item in enumerate(items):
            y = start_y + i * 60
            color = YELLOW if i == selected_item else WHITE
            size = 32 if i == selected_item else 24
            if i == selected_item:
                pulse = np.sin(pygame.time.get_ticks() * 0.005) * 0.1 + 0.2
                glColor4f(1.0, 1.0, 0.0, pulse)
                glBegin(GL_QUADS)
                glVertex2f(WIDTH//2 - 150, y - 10)
                glVertex2f(WIDTH//2 + 150, y - 10)
                glVertex2f(WIDTH//2 + 150, y + 40)
                glVertex2f(WIDTH//2 - 150, y + 40)
                glEnd()
            draw_text(item, WIDTH//2 - len(item) * 8, y, color, size)

        hint_y = HEIGHT - 100
        draw_text("UP DOWN - navigate", WIDTH//2 - 80, hint_y, GRAY, 16)
        draw_text("ENTER - select", WIDTH//2 - 70, hint_y + 25, GRAY, 16)

        if not music_loaded:
            draw_text("Add music.mp3 to the game folder", WIDTH//2 - 160, HEIGHT - 50, YELLOW, 14)

        pygame.display.flip()
        clock.tick(menu_fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if main_cap:
                    main_cap.release()
                if settings_cap:
                    settings_cap.release()
                return "exit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_item = (selected_item - 1) % len(items)
                elif event.key == pygame.K_DOWN:
                    selected_item = (selected_item + 1) % len(items)
                elif event.key == pygame.K_LEFT:
                    if current_menu == "settings" and selected_item == 0:
                        selected_level = max(1, selected_level - 1)
                        settings_items[0] = "Start level: {} / 20".format(selected_level)
                elif event.key == pygame.K_RIGHT:
                    if current_menu == "settings" and selected_item == 0:
                        selected_level = min(20, selected_level + 1)
                        settings_items[0] = "Start level: {} / 20".format(selected_level)
                elif event.key == pygame.K_RETURN:
                    if current_menu == "main":
                        if selected_item == 0:
                            if main_cap:
                                main_cap.release()
                            if settings_cap:
                                settings_cap.release()
                            return "play"
                        elif selected_item == 1:
                            current_menu = "settings"
                            selected_item = 0
                        elif selected_item == 2:
                            if main_cap:
                                main_cap.release()
                            if settings_cap:
                                settings_cap.release()
                            return "exit"
                    else:
                        if selected_item == 1:
                            toggle_music()
                            settings_items[1] = "Music: On" if music_playing else "Music: Off"
                        elif selected_item == 2:
                            current_menu = "main"
                            selected_item = 0
                elif event.key == pygame.K_ESCAPE:
                    if current_menu == "settings":
                        current_menu = "main"
                        selected_item = 0
                    else:
                        if main_cap:
                            main_cap.release()
                        if settings_cap:
                            settings_cap.release()
                        return "exit"
                elif event.key == pygame.K_m and music_loaded:
                    toggle_music()
                    if current_menu == "settings":
                        settings_items[1] = "Music: On" if music_playing else "Music: Off"

    if main_cap:
        main_cap.release()
    if settings_cap:
        settings_cap.release()
    return "exit"


def show_exit_screen():
    """Показывает видео при выходе из игры (outro.mp4, если есть, иначе intro.mp4)."""
    global music_playing

    if music_loaded:
        pygame.mixer.music.stop()

    video_path = 'intro.mp4'
    outro_path = 'outro.mp4'

    if os.path.exists(outro_path):
        video_path = outro_path
        print("Найдено видео для выхода: outro.mp4")
    elif os.path.exists(video_path):
        print("Используется intro.mp4 для выхода")
    else:
        print("Видео для выхода не найдено")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Не удалось открыть видеофайл {video_path}")
        return

    if music_loaded and music_playing:
        exit_music_files = ['exit.mp3', 'goodbye.mp3', 'music.mp3']
        music_loaded_exit = False
        for music_file in exit_music_files:
            if os.path.exists(music_file):
                try:
                    pygame.mixer.music.load(music_file)
                    pygame.mixer.music.play(loops=-1)
                    music_loaded_exit = True
                    print(f"Загружена музыка для выхода: {music_file}")
                    break
                except Exception as e:
                    print(f"Ошибка загрузки музыки для выхода {music_file}: {e}")
        if not music_loaded_exit and music_loaded:
            pygame.mixer.music.play(loops=-1)

    start_time = time.time()
    duration = 5
    fade_start = duration - 1

    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        if elapsed >= duration:
            break

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            texture_data = frame.tobytes()
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH, HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)

            alpha = 1.0
            if elapsed > fade_start:
                alpha = 1.0 - (elapsed - fade_start)

            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glColor4f(1.0, 1.0, 1.0, alpha)
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex2f(0, 0)
            glTexCoord2f(1.0, 0.0); glVertex2f(WIDTH, 0)
            glTexCoord2f(1.0, 1.0); glVertex2f(WIDTH, HEIGHT)
            glTexCoord2f(0.0, 1.0); glVertex2f(0, HEIGHT)
            glEnd()
            glDisable(GL_TEXTURE_2D)

            glDeleteTextures([texture_id])
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        if elapsed < duration - 1:
            if int(elapsed * 2) % 2 == 0:
                draw_text("GOODBYE!", WIDTH//2 - 150, HEIGHT//2 - 50, WHITE, 36)
                draw_text("Thanks for playing Tetris!", WIDTH//2 - 150, HEIGHT//2 + 20, YELLOW, 24)

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    cap.release()
                    return

    cap.release()

# ============================== ГЛАВНЫЙ ИГРОВОЙ ЦИКЛ ==============================

def draw_side_panel(board):
    # ---- Панель HOLD (слева от поля) ----
    panel_w = 150
    hold_x = BOARD_X - panel_w - 20
    hold_y = BOARD_Y
    draw_rounded_rect(hold_x, hold_y, panel_w, 110, 8, (10, 10, 18), alpha=0.55)
    draw_text("HOLD", hold_x + panel_w//2 - 30, hold_y + 8, CYAN, 18)
    if board.hold_kind:
        alpha_color = GRAY if board.hold_used else WHITE
        draw_mini_piece(board.hold_kind, hold_x + panel_w//2, hold_y + 70, cell=18)

    # Подсказки управления под HOLD
    hint_y = hold_y + 140
    draw_rounded_rect(hold_x, hint_y, panel_w, 230, 8, (10, 10, 18), alpha=0.45)
    controls = [
        ("<- ->", "Move"),
        ("UP", "Rotate"),
        ("DOWN", "Soft drop"),
        ("SPACE", "Hard drop"),
        ("C", "Hold"),
        ("P", "Pause"),
        ("M", "Music"),
        ("ESC", "Menu"),
    ]
    for i, (key, action) in enumerate(controls):
        y = hint_y + 12 + i * 27
        draw_text(key, hold_x + 10, y, YELLOW, 13)
        draw_text(action, hold_x + 65, y, WHITE, 13)

    # ---- Панель NEXT (справа от поля) ----
    next_x = BOARD_X + BOARD_W + 20
    next_y = BOARD_Y
    draw_rounded_rect(next_x, next_y, panel_w, 260, 8, (10, 10, 18), alpha=0.55)
    draw_text("NEXT", next_x + panel_w//2 - 30, next_y + 8, CYAN, 18)
    for i, kind in enumerate(board.next_queue[:3]):
        draw_mini_piece(kind, next_x + panel_w//2, next_y + 60 + i * 65, cell=16)

    # ---- Панель статистики (под NEXT) ----
    stats_y = next_y + 280
    draw_rounded_rect(next_x, stats_y, panel_w, 190, 8, (10, 10, 18), alpha=0.55)
    draw_text("SCORE", next_x + 12, stats_y + 10, GRAY, 14)
    draw_text(f"{board.score}", next_x + 12, stats_y + 28, WHITE, 22)
    draw_text("LEVEL", next_x + 12, stats_y + 65, GRAY, 14)
    draw_text(f"{board.level}", next_x + 12, stats_y + 83, GOLD, 22)
    draw_text("LINES", next_x + 12, stats_y + 120, GRAY, 14)
    draw_text(f"{board.lines_cleared}", next_x + 12, stats_y + 138, GREEN, 22)


def show_boss_intro_removed():
    # Не используется в Тетрисе - оставлено для совместимости структуры проекта
    pass


DAS_DELAY = 10   # кадров до начала автоповтора при удержании кнопки
DAS_SPEED = 2    # кадров между повторами при удержании


def main():
    global game_background_texture, selected_level, max_level

    while True:
        menu_result = show_menu()

        if menu_result == "exit":
            show_exit_screen()
            break
        elif menu_result == "play":
            game_background_texture, _, _ = load_texture('background_game.png')

            board = TetrisBoard(start_level=selected_level)
            paused = False
            running = True

            move_left_timer = 0
            move_right_timer = 0
            down_held = False

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r and board.game_over:
                            board = TetrisBoard(start_level=selected_level)
                            paused = False
                        elif event.key == pygame.K_p and not board.game_over:
                            paused = not paused
                        elif event.key == pygame.K_m and music_loaded:
                            toggle_music()
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                        elif not board.game_over and not paused:
                            if event.key == pygame.K_LEFT:
                                board.try_move(-1, 0)
                                move_sound.play()
                                move_left_timer = 0
                            elif event.key == pygame.K_RIGHT:
                                board.try_move(1, 0)
                                move_sound.play()
                                move_right_timer = 0
                            elif event.key in (pygame.K_UP, pygame.K_x):
                                board.try_rotate(1)
                            elif event.key == pygame.K_z:
                                board.try_rotate(-1)
                            elif event.key == pygame.K_SPACE:
                                board.hard_drop()
                            elif event.key == pygame.K_c:
                                board.hold()
                            elif event.key == pygame.K_DOWN:
                                down_held = True
                    if event.type == pygame.KEYUP:
                        if event.key == pygame.K_DOWN:
                            down_held = False

                if not board.game_over and not paused:
                    keys = pygame.key.get_pressed()

                    # DAS (автоповтор движения при удержании клавиши)
                    if keys[pygame.K_LEFT]:
                        move_left_timer += 1
                        if move_left_timer > DAS_DELAY and move_left_timer % DAS_SPEED == 0:
                            board.try_move(-1, 0)
                    else:
                        move_left_timer = 0

                    if keys[pygame.K_RIGHT]:
                        move_right_timer += 1
                        if move_right_timer > DAS_DELAY and move_right_timer % DAS_SPEED == 0:
                            board.try_move(1, 0)
                    else:
                        move_right_timer = 0

                    board.soft_drop = down_held
                    board.update()

                # Отрисовка
                draw_background()

                # затемняющая подложка, чтобы поле было хорошо видно поверх фона
                draw_rect(0, 0, WIDTH, HEIGHT, (0, 0, 0), alpha=0.35)

                board.draw()
                draw_side_panel(board)

                draw_text("TETRIS", BOARD_X, BOARD_Y - 44, CYAN, 26)

                if paused:
                    draw_rounded_rect(WIDTH//2 - 160, HEIGHT//2 - 60, 320, 120, 12, (0, 0, 0), alpha=0.75)
                    draw_text("PAUSED", WIDTH//2 - 70, HEIGHT//2 - 40, YELLOW, 32)
                    draw_text("Press P to resume", WIDTH//2 - 95, HEIGHT//2 + 10, WHITE, 16)

                if board.game_over:
                    draw_rounded_rect(WIDTH//2 - 220, HEIGHT//2 - 70, 440, 140, 12, (0, 0, 0), alpha=0.8)
                    draw_text("GAME OVER", WIDTH//2 - 110, HEIGHT//2 - 50, RED, 32)
                    draw_text(f"Final score: {board.score}", WIDTH//2 - 110, HEIGHT//2 - 5, WHITE, 20)
                    draw_text("Press R to restart, ESC for menu", WIDTH//2 - 160, HEIGHT//2 + 30, GRAY, 16)

                # Статус музыки
                if music_loaded:
                    music_status = "M: MUSIC ON" if music_playing else "M: MUSIC OFF"
                    music_color = GREEN if music_playing else RED
                    draw_text(music_status, 16, HEIGHT - 30, music_color, 14)

                pygame.display.flip()
                clock.tick(FPS)

            if game_background_texture is not None:
                glDeleteTextures([game_background_texture])
                game_background_texture = None

    if music_loaded:
        pygame.mixer.music.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
