#!/usr/bin/env python3
"""
Terminal Aquarium — press Q to quit, F to add a fish, B for a burst of bubbles
"""

import curses
import random
import time
import math
import sys

# ── Sprites ─────────────────────────────────────────────────────────────────
FISH_SPRITES = [
    ('><>',        '<><'),
    ('><(·>',      '<·)><'),
    ('><((º>',     '<º))><'),
    ('><(((º>',    '<º)))><'),
]
FISH_SPEEDS = [0.06, 0.05, 0.035, 0.025]  # seconds per column

SEAWEED_TOPS = ['&', '%', '@', '*', '+']

BUBBLE_CHARS = ['o', 'O', '°', '.', '·']

CORAL_SPRITES = [
    [' /\\ ', '/  \\', '|  |'],
    ['\\  /', ' \\/ ', '  | '],
    [' ** ', '*  *', ' ** '],
]

TREASURE_SPRITE = [
    '╔══╗',
    '║()║',
    '╚══╝',
]

TITLE = '~  T E R M I N A L   A Q U A R I U M  ~'

# ── Color pair IDs ───────────────────────────────────────────────────────────
C_WATER_DEEP   = 1
C_WATER_MID    = 2
C_WATER_LIGHT  = 3
C_WATER_SURF   = 4
C_SAND         = 5
C_WEED_DARK    = 6
C_WEED_LIGHT   = 7
C_BUBBLE       = 8
C_TITLE        = 16
C_CORAL        = 17
C_TREASURE     = 18
C_STATUS       = 19

FISH_PAIR_START = 9   # pairs 9-15 are fish colors

# ── Entity classes ───────────────────────────────────────────────────────────
class Fish:
    def __init__(self, size, x, y, going_right, color_pair, w, h):
        self.size = size
        self.x = float(x)
        self.y = float(y)
        self.going_right = going_right
        self.color_pair = color_pair
        self.speed = FISH_SPEEDS[size] * random.uniform(0.75, 1.3)
        self.bob_phase = random.uniform(0, math.tau)
        self.bob_amp = random.uniform(0.3, 0.8)
        self.bob_speed = random.uniform(0.6, 1.4)
        self.bubble_timer = random.uniform(2, 7)
        self.w = w
        self.h = h

    @property
    def sprite(self):
        return FISH_SPRITES[self.size][0 if self.going_right else 1]

    @property
    def length(self):
        return len(FISH_SPRITES[self.size][0])

    def update(self, dt, bubbles, t):
        dx = (1 if self.going_right else -1) * dt / self.speed
        self.x += dx

        margin = self.length
        if self.going_right and self.x + margin >= self.w:
            self.x = float(self.w - margin - 1)
            self.going_right = False
        elif not self.going_right and self.x < 0:
            self.x = 0.0
            self.going_right = True

        self.bubble_timer -= dt
        if self.bubble_timer <= 0:
            bx = int(self.x) + (self.length - 1 if not self.going_right else 0)
            by = int(self.y) - 1
            if by > 1:
                bubbles.append(Bubble(bx, by))
            self.bubble_timer = random.uniform(3, 9)

    def draw_row(self, t):
        bob = self.bob_amp * math.sin(t * self.bob_speed + self.bob_phase)
        return int(self.x), int(self.y + bob)


class Bubble:
    def __init__(self, x, y):
        self.x = x
        self.y = float(y)
        self.rise = random.uniform(0.8, 2.5)
        self.drift = random.uniform(-0.3, 0.3)
        self.char = random.choice(BUBBLE_CHARS)
        self.age = 0.0

    def update(self, dt):
        self.y -= dt * self.rise
        self.x += dt * self.drift
        self.age += dt


class Seaweed:
    def __init__(self, x, height):
        self.x = x
        self.height = height
        self.phase = random.uniform(0, math.tau)
        self.speed = random.uniform(0.4, 0.9)
        self.top = random.choice(SEAWEED_TOPS)

    def sway_offset(self, row_from_bottom, t):
        depth_factor = (self.height - row_from_bottom) / self.height
        return int(round(depth_factor * math.sin(t * self.speed + self.phase)))


# ── Color setup ──────────────────────────────────────────────────────────────
def init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
    except Exception:
        pass

    rich = curses.can_change_color() and curses.COLORS >= 256

    if rich:
        curses.init_color(50, 0,   80,  350)   # deep water
        curses.init_color(51, 0,  120,  470)   # mid water
        curses.init_color(52, 0,  180,  600)   # light water
        curses.init_color(53, 0,  260,  720)   # surface
        curses.init_color(54, 820, 710, 420)   # sand
        curses.init_color(55, 80,  540, 180)   # seaweed dark
        curses.init_color(56, 160, 750, 280)   # seaweed light
        curses.init_color(57, 750, 850, 950)   # bubble / white
        curses.init_color(58, 1000, 420,  20)  # fish orange
        curses.init_color(59, 1000, 820,  0)   # fish yellow
        curses.init_color(60, 1000, 200, 200)  # fish red
        curses.init_color(61, 200,  900, 200)  # fish green
        curses.init_color(62, 200,  600,1000)  # fish blue
        curses.init_color(63, 1000, 400, 750)  # fish pink
        curses.init_color(64, 720,  300,1000)  # fish purple
        curses.init_color(65, 100,  950, 720)  # fish teal
        curses.init_color(66, 1000, 860, 0)    # gold (treasure)
        curses.init_color(67, 1000, 300, 100)  # coral

        curses.init_pair(C_WATER_DEEP,  57, 50)
        curses.init_pair(C_WATER_MID,   57, 51)
        curses.init_pair(C_WATER_LIGHT, 57, 52)
        curses.init_pair(C_WATER_SURF,  57, 53)
        curses.init_pair(C_SAND,        54, 54)
        curses.init_pair(C_WEED_DARK,   55, 51)
        curses.init_pair(C_WEED_LIGHT,  56, 51)
        curses.init_pair(C_BUBBLE,      57, 51)
        curses.init_pair(C_TITLE,       66, 53)
        curses.init_pair(C_CORAL,       67, 50)
        curses.init_pair(C_TREASURE,    66, 50)
        curses.init_pair(C_STATUS,      57, 50)

        fish_fgs = [58, 59, 60, 61, 62, 63, 64, 65]
        for i, fg in enumerate(fish_fgs):
            curses.init_pair(FISH_PAIR_START + i, fg, 51)
    else:
        # Basic 8-color fallback
        bgs = [curses.COLOR_BLUE] * 4 + [curses.COLOR_YELLOW, curses.COLOR_BLUE,
               curses.COLOR_BLUE, curses.COLOR_WHITE]
        fgs = [curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_WHITE,
               curses.COLOR_WHITE, curses.COLOR_YELLOW, curses.COLOR_GREEN,
               curses.COLOR_GREEN, curses.COLOR_WHITE]
        for i in range(1, 9):
            curses.init_pair(i, fgs[i-1], bgs[i-1])
        curses.init_pair(C_TITLE,    curses.COLOR_YELLOW, curses.COLOR_CYAN)
        curses.init_pair(C_CORAL,    curses.COLOR_RED,    curses.COLOR_BLUE)
        curses.init_pair(C_TREASURE, curses.COLOR_YELLOW, curses.COLOR_BLUE)
        curses.init_pair(C_STATUS,   curses.COLOR_WHITE,  curses.COLOR_BLUE)

        basic_fish = [(curses.COLOR_YELLOW, curses.COLOR_BLUE),
                      (curses.COLOR_YELLOW, curses.COLOR_BLUE),
                      (curses.COLOR_RED,    curses.COLOR_BLUE),
                      (curses.COLOR_GREEN,  curses.COLOR_BLUE),
                      (curses.COLOR_CYAN,   curses.COLOR_BLUE),
                      (curses.COLOR_MAGENTA,curses.COLOR_BLUE),
                      (curses.COLOR_MAGENTA,curses.COLOR_BLUE),
                      (curses.COLOR_CYAN,   curses.COLOR_BLUE)]
        for i, (fg, bg) in enumerate(basic_fish):
            curses.init_pair(FISH_PAIR_START + i, fg, bg)


# ── Background ───────────────────────────────────────────────────────────────
def water_pair(row, h):
    floor_rows = 3
    water_h = h - floor_rows - 1
    if water_h <= 0:
        return C_WATER_MID
    frac = row / max(water_h, 1)
    if frac < 0.2:
        return C_WATER_SURF
    elif frac < 0.5:
        return C_WATER_LIGHT
    elif frac < 0.75:
        return C_WATER_MID
    return C_WATER_DEEP


def draw_background(win, h, w):
    floor_rows = 3
    for r in range(h - floor_rows):
        pair = water_pair(r, h)
        try:
            win.addstr(r, 0, ' ' * w, curses.color_pair(pair))
        except curses.error:
            pass
    # Sand floor
    for r in range(h - floor_rows, h - 1):
        try:
            win.addstr(r, 0, '~' * w, curses.color_pair(C_SAND) | curses.A_DIM)
        except curses.error:
            pass


def draw_title(win, w, t):
    title = TITLE
    blink = int(t * 2) % 3 != 0
    x = max(0, (w - len(title)) // 2)
    attr = curses.color_pair(C_TITLE) | curses.A_BOLD
    if blink:
        attr |= curses.A_BOLD
    try:
        win.addstr(0, x, title[:w - x], attr)
    except curses.error:
        pass


def draw_status(win, h, w, fish_count):
    msg = f'  Q:quit  F:+fish  B:bubbles  🐠×{fish_count}  '
    try:
        win.addstr(h - 1, 0, msg[:w], curses.color_pair(C_STATUS))
    except curses.error:
        pass


def draw_seaweed(win, h, w, seaweeds, t):
    floor_y = h - 4
    for sw in seaweeds:
        if sw.x >= w:
            continue
        for k in range(sw.height):
            row = floor_y - k
            if row < 1 or row >= h - 1:
                continue
            offset = sw.sway_offset(k, t)
            col = sw.x + offset
            if col < 0 or col >= w:
                continue
            ch = sw.top if k == sw.height - 1 else ('(' if k % 2 == 0 else ')')
            pair = C_WEED_LIGHT if k % 2 == 0 else C_WEED_DARK
            try:
                win.addstr(row, col, ch, curses.color_pair(pair) | curses.A_BOLD)
            except curses.error:
                pass


def draw_coral(win, h, w, coral_positions):
    floor_y = h - 4
    for cx, sprite_idx in coral_positions:
        sprite = CORAL_SPRITES[sprite_idx % len(CORAL_SPRITES)]
        for i, line in enumerate(reversed(sprite)):
            row = floor_y - i
            if row < 1 or row >= h - 1:
                continue
            col = cx
            if col + len(line) > w:
                continue
            try:
                win.addstr(row, col, line, curses.color_pair(C_CORAL) | curses.A_BOLD)
            except curses.error:
                pass


def draw_treasure(win, h, w, tx):
    floor_y = h - 4
    for i, line in enumerate(reversed(TREASURE_SPRITE)):
        row = floor_y - i
        if row < 1 or row >= h - 1:
            continue
        if tx + len(line) > w:
            continue
        try:
            win.addstr(row, tx, line, curses.color_pair(C_TREASURE) | curses.A_BOLD)
        except curses.error:
            pass


def draw_fish(win, h, w, fish_list, t):
    for fish in fish_list:
        col, row = fish.draw_row(t)
        if row < 1 or row >= h - 4:
            continue
        sprite = fish.sprite
        if col < 0:
            sprite = sprite[-col:]
            col = 0
        if col + len(sprite) > w:
            sprite = sprite[:w - col]
        if not sprite:
            continue
        try:
            win.addstr(row, col, sprite,
                       curses.color_pair(fish.color_pair) | curses.A_BOLD)
        except curses.error:
            pass


def draw_bubbles(win, h, w, bubbles):
    for b in bubbles:
        row = int(b.y)
        col = int(b.x)
        if row < 1 or row >= h - 4 or col < 0 or col >= w:
            continue
        pair = C_BUBBLE if row > h // 2 else C_WATER_LIGHT
        try:
            win.addstr(row, col, b.char, curses.color_pair(pair))
        except curses.error:
            pass


# ── Population helpers ───────────────────────────────────────────────────────
def make_fish(w, h, size=None, color_pair=None):
    if size is None:
        weights = [3, 3, 2, 1]
        size = random.choices(range(4), weights=weights)[0]
    if color_pair is None:
        color_pair = random.randint(FISH_PAIR_START, FISH_PAIR_START + 7)
    going_right = random.choice([True, False])
    floor_y = h - 4
    x = random.randint(0, max(1, w - len(FISH_SPRITES[size][0]) - 1))
    y = random.randint(2, floor_y - 2)
    return Fish(size, x, y, going_right, color_pair, w, h)


def populate(w, h):
    fish_list = []
    counts = [3, 3, 2, 1]
    used_pairs = []
    for size, count in enumerate(counts):
        for _ in range(count):
            available = [p for p in range(FISH_PAIR_START, FISH_PAIR_START + 8)
                         if p not in used_pairs] or list(range(FISH_PAIR_START, FISH_PAIR_START + 8))
            cp = random.choice(available)
            used_pairs.append(cp)
            fish_list.append(make_fish(w, h, size, cp))

    floor_y = h - 4
    seaweeds = []
    positions = sorted(random.sample(range(3, w - 3), min(12, w - 6)))
    for x in positions:
        seaweeds.append(Seaweed(x, random.randint(2, min(6, floor_y - 2))))

    coral_positions = []
    coral_xs = random.sample(range(2, w - 6), min(5, w // 12))
    for cx in coral_xs:
        coral_positions.append((cx, random.randint(0, len(CORAL_SPRITES) - 1)))

    treasure_x = random.randint(4, w - 8)

    return fish_list, seaweeds, coral_positions, treasure_x


# ── Main loop ────────────────────────────────────────────────────────────────
def aquarium(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    init_colors()

    h, w = stdscr.getmaxyx()
    fish_list, seaweeds, coral_positions, treasure_x = populate(w, h)
    bubbles = []

    start = time.time()
    last_frame = start
    frame_dt = 1 / 20  # target 20 FPS

    while True:
        now = time.time()
        dt = now - last_frame
        if dt < frame_dt:
            curses.napms(int((frame_dt - dt) * 1000))
            continue
        last_frame = now
        t = now - start

        # Handle resize
        new_h, new_w = stdscr.getmaxyx()
        if new_h != h or new_w != w:
            h, w = new_h, new_w
            fish_list, seaweeds, coral_positions, treasure_x = populate(w, h)
            bubbles.clear()

        # Input
        try:
            key = stdscr.getch()
        except Exception:
            key = -1

        if key in (ord('q'), ord('Q')):
            break
        elif key in (ord('f'), ord('F')):
            if len(fish_list) < 20:
                fish_list.append(make_fish(w, h))
        elif key in (ord('b'), ord('B')):
            for _ in range(15):
                bx = random.randint(1, w - 2)
                by = random.randint(h // 2, h - 5)
                bubbles.append(Bubble(bx, by))

        # Update
        for fish in fish_list:
            fish.update(dt, bubbles, t)

        for b in bubbles:
            b.update(dt)

        bubbles = [b for b in bubbles if b.y > 1 and b.age < 30]
        if len(bubbles) > 60:
            bubbles = bubbles[-60:]

        # Draw
        stdscr.erase()
        draw_background(stdscr, h, w)
        draw_seaweed(stdscr, h, w, seaweeds, t)
        draw_coral(stdscr, h, w, coral_positions)
        draw_treasure(stdscr, h, w, treasure_x)
        draw_bubbles(stdscr, h, w, bubbles)
        draw_fish(stdscr, h, w, fish_list, t)
        draw_title(stdscr, w, t)
        draw_status(stdscr, h, w, len(fish_list))

        try:
            stdscr.refresh()
        except curses.error:
            pass


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    try:
        curses.wrapper(aquarium)
    except KeyboardInterrupt:
        pass
    print("\nThanks for visiting the aquarium! 🐠\n")


if __name__ == '__main__':
    main()
