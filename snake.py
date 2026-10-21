# -*- coding: utf-8 -*-
"""Bài 4 — Rắn săn mồi (pygame)

Cách chơi:
  - Mũi tên / WASD: di chuyển theo lưới (mỗi bước đúng 1 ô)
  - P: tạm dừng        R: chơi lại        Esc: thoát
Quy tắc:
  - Mồi đỏ  : +1 điểm, rắn dài thêm 1 đốt
  - Mồi vàng: chỉ tồn tại 5 giây rồi biến mất, ăn được +5 điểm
  - Cứ ăn đủ 5 mồi, rắn nhanh hơn (tốc độ tăng, có trần tối đa)
  - Đâm vào tường hoặc thân mình: thua

Chạy tự kiểm tra logic (không cần cửa sổ):  python snake.py --selftest
"""

import os
import random
import sys
from collections import deque

import pygame

# ---------- Hằng số ----------
CELL = 20                 # kích thước 1 ô lưới (px)
COLS, ROWS = 30, 24       # bàn cờ 30 x 24 ô
HUD_HEIGHT = 40           # thanh trạng thái phía trên
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + HUD_HEIGHT

START_SPEED = 6.0         # bước / giây
SPEED_UP = 1.5            # tăng thêm sau mỗi 5 mồi
MAX_SPEED = 16.0
FOODS_PER_BOOST = 5       # cứ 5 mồi thì nhanh hơn

SPECIAL_LIFETIME_MS = 5000  # mồi vàng sống 5 giây
SPECIAL_SCORE = 5           # ăn mồi vàng +5 điểm
SPECIAL_SPAWN_CHANCE = 0.015  # xác suất mồi vàng xuất hiện mỗi bước rắn

DIRS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}

# Màu
BG = (18, 20, 28)
GRID = (28, 32, 46)
BORDER = (70, 76, 100)
HUD_BG = (10, 12, 18)
HUD_TEXT = (235, 235, 240)
BODY = (70, 200, 110)
HEAD = (130, 245, 160)
FOOD_COLOR = (235, 80, 80)
SPECIAL_COLOR = (250, 200, 60)
OVERLAY = (8, 10, 16)


def random_free_cell(dodge):
    """Chọn ngẫu nhiên 1 ô lưới không trùng ô nào trong `dodge`."""
    while True:
        cell = (random.randrange(COLS), random.randrange(ROWS))
        if cell not in dodge:
            return cell


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rắn săn mồi — Bài 4")
        self.font = pygame.font.SysFont("segoeui,arial", 18)
        self.font_big = pygame.font.SysFont("segoeui,arial", 34, bold=True)
        self.clock = pygame.time.Clock()
        self.reset()

    # ---------- Khởi tạo / chơi lại ----------
    def reset(self):
        cx, cy = COLS // 4, ROWS // 2
        self.snake = deque([(cx, cy), (cx - 1, cy), (cx - 2, cy)])  # đầu ở index 0
        self.dir = (1, 0)                 # hướng hiện tại
        self.pending = deque(maxlen=2)    # hướng người chơi vừa bấm (xử lý 1 hướng / tick)
        self.score = 0
        self.eaten = 0                    # số mồi đã ăn, để đếm 5 mồi / lần tăng tốc
        self.speed = START_SPEED
        self.best = 0
        self.game_over = False
        self.paused = False
        self.acc = 0                      # bộ tích luỹ thời gian cho chu kỳ bước rắn
        self.special = None               # toạ độ mồi vàng
        self.special_deadline = 0         # thời điểm (ms) mồi vàng biến mất
        self.food = self.spawn_food()     # spawn mồi, tránh thân rắn

    def spawn_food(self):
        dodge = set(self.snake)
        if self.special:
            dodge.add(self.special)
        return random_free_cell(dodge)

    # ---------- Vòng chính ----------
    def run(self):
        while True:
            dt = self.clock.tick(60)          # ms của khung hình này
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in (pygame.K_ESCAPE,):
                pygame.quit()
                sys.exit()
            if self.game_over:
                if event.key in (pygame.K_r, pygame.K_RETURN):
                    self.reset()
                elif event.key == pygame.K_p:
                    pass
                continue
            if event.key == pygame.K_p:
                self.paused = not self.paused
            if event.key in DIRS and not self.paused:
                self.pending.append(DIRS[event.key])

    # ---------- Cập nhật ----------
    def update(self, dt):
        """dt: ms trôi qua. Gọi step() theo đúng chu kỳ của tốc độ hiện tại."""
        if self.game_over or self.paused:
            return
        self.acc += dt
        interval = 1000.0 / self.speed
        while self.acc >= interval and not self.game_over:
            self.acc -= interval
            self.step()

    def step(self):
        # Hết giờ mồi vàng -> biến mất
        now = pygame.time.get_ticks()
        if self.special and now >= self.special_deadline:
            self.special = None

        # Angular: nhận tối đa 1 hướng mới / tick, cấm quay đầu 180 độ
        if self.pending:
            d = self.pending.popleft()
            if d != self.dir and (d[0] + self.dir[0], d[1] + self.dir[1]) != (0, 0):
                self.dir = d

        hx, hy = self.snake[0]
        new_head = (hx + self.dir[0], hy + self.dir[1])

        # Đâm tường
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            self.game_over = True
            return

        ate_food = new_head == self.food
        ate_special = self.special is not None and new_head == self.special
        grow = ate_food  # mồi vàng chỉ +điểm, không dài ra

        # Đâm thân mình (ô đuôi sẽ rời đi trong bước này nếu không dài ra
        # => phép nhảy vào ô đang bị đuôi bỏ là hợp lệ)
        body = list(self.snake) if grow else list(self.snake)[:-1]
        if new_head in body:
            self.game_over = True
            return

        # Mồi vàng hết hạn ngay tại thời điểm ăn cũng vẫn tính
        self.snake.appendleft(new_head)
        if not grow:
            self.snake.pop()

        if ate_food:
            self.score += 1
            self.eaten += 1
            if self.eaten % FOODS_PER_BOOST == 0:
                self.speed = min(self.speed + SPEED_UP, MAX_SPEED)
            self.food = self.spawn_food()
        elif ate_special:
            self.score += SPECIAL_SCORE
            self.special = None

        # Mồi vàng xuất hiện ngẫu nhiên, tối đa 1 mồi / 1 thời điểm
        if not self.special and random.random() < SPECIAL_SPAWN_CHANCE:
            self.special = random_free_cell(set(self.snake) | {self.food})
            self.special_deadline = pygame.time.get_ticks() + SPECIAL_LIFETIME_MS

    # ---------- Vẽ ----------
    def draw(self):
        self.screen.fill(HUD_BG)
        board_y = HUD_HEIGHT
        board = pygame.Rect(0, board_y, WIDTH, HEIGHT - board_y)

        # Bàn cờ: nền + lưới
        pygame.draw.rect(self.screen, BG, board)
        for x in range(0, COLS + 1):
            pygame.draw.line(self.screen, GRID, (x * CELL, board_y),
                             (x * CELL, HEIGHT))
        for y in range(0, ROWS + 1):
            pygame.draw.line(self.screen, GRID, (0, board_y + y * CELL),
                             (WIDTH, board_y + y * CELL))
        pygame.draw.rect(self.screen, BORDER, board, 2)

        # Mồi thường (đỏ) — hình tròn
        if self.food:
            fx, fy = self.food
            pygame.draw.circle(self.screen, FOOD_COLOR,
                               (fx * CELL + CELL // 2, board_y + fy * CELL + CELL // 2),
                               CELL // 2 - 3)

        # Mồi vàng — kim cương nhấp nháy
        if self.special:
            sx, sy = self.special
            cx_, cy_ = sx * CELL + CELL // 2, board_y + sy * CELL + CELL // 2
            now = pygame.time.get_ticks()
            pulse = 4 + int(2 * (now % 400) / 400)
            r = min(CELL, CELL // 2 - 2 + pulse)
            points = [(cx_, cy_ - r), (cx_ + r, cy_), (cx_, cy_ + r), (cx_ - r, cy_)]
            pygame.draw.polygon(self.screen, SPECIAL_COLOR, points)

        # Rắn
        for i, (sx, sy) in enumerate(self.snake):
            rect = pygame.Rect(sx * CELL + 1, board_y + sy * CELL + 1,
                               CELL - 2, CELL - 2)
            pygame.draw.rect(self.screen, HEAD if i == 0 else BODY, rect,
                             border_radius=4)
        # Mắt rắn
        hx, hy = self.snake[0]
        ecx, ecy = hx * CELL + CELL // 2, board_y + hy * CELL + CELL // 2
        dx, dy = self.dir
        ex1, ey1 = ecx + dx * 4 - dy * 4, ecy + dy * 4 - dx * 4
        ex2, ey2 = ecx + dx * 4 + dy * 4, ecy + dy * 4 + dx * 4
        pygame.draw.circle(self.screen, (255, 255, 255), (ex1, ey1), 2)
        pygame.draw.circle(self.screen, (255, 255, 255), (ex2, ey2), 2)

        self.draw_hud()
        if self.game_over:
            self.draw_center_overlay("THUA RỒI!", "Điểm: %d   —   R: chơi lại   Esc: thoát" % self.score)
        elif self.paused:
            self.draw_center_overlay("TẠM DỪNG", "P: chơi tiếp")

    def draw_hud(self):
        self.best = max(self.best, self.score)
        to_boost = FOODS_PER_BOOST - self.eaten % FOODS_PER_BOOST
        hud = "Điểm: %d    Mồi tiếp theo tăng tốc: %d/%d    Tốc độ: %.1f    Kỷ lục: %d" % (
            self.score, to_boost, FOODS_PER_BOOST, self.speed, self.best)
        self.screen.blit(self.font.render(hud, True, HUD_TEXT), (8, 10))

        if self.special:
            remain = max(0, self.special_deadline - pygame.time.get_ticks())
            bar = pygame.Rect(WIDTH - 160, 12, 150, 12)
            pygame.draw.rect(self.screen, HUD_TEXT, bar, 1)
            fill_w = int(bar.w * remain / SPECIAL_LIFETIME_MS)
            pygame.draw.rect(self.screen, SPECIAL_COLOR,
                             (bar.x + 1, bar.y + 1, fill_w, bar.h - 2))
            label = self.font.render("Mồi vàng: %s" % ("%.1fs" % (remain / 1000)),
                                     True, SPECIAL_COLOR)
            self.screen.blit(label, (WIDTH - 160, 28 - label.get_height()))

    def draw_center_overlay(self, title, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT - HUD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*OVERLAY, 190))
        self.screen.blit(overlay, (0, HUD_HEIGHT))
        t = self.font_big.render(title, True, HUD_TEXT)
        s = self.font.render(subtitle, True, HUD_TEXT)
        self.screen.blit(t, t.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        self.screen.blit(s, s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))


def main():
    Game().run()


# ---------- Tự kiểm tra logic (không cần cửa sổ) ----------
def _selftest():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    """python snake.py --selftest  ->  chạy assert toàn bộ luồng logic."""
    global SPECIAL_SPAWN_CHANCE
    SPECIAL_SPAWN_CHANCE = 0   # tắt spawn ngẫu nhiên để test deterministic
    random.seed(7)
    g = Game()

    # 1) Rắn di chuyển theo lưới
    head0 = g.snake[0]
    for _ in range(15):
        g.update(50)
    assert g.snake[0] != head0, "Rắn phải di chuyển"

    # 2) Ăn mồi thường: +1 điểm, +1 đốt
    hx, hy = g.snake[0]
    g.food = (hx + g.dir[0], hy + g.dir[1])          # đặt mồi ngay phía trước
    score0, length0 = g.score, len(g.snake)
    g.acc = 0
    g.update(1000 / g.speed + 1)
    assert g.score == score0 + 1, "Mồi thường phải +1 điểm"
    assert len(g.snake) == length0 + 1, "Ăn mồi phải dài thêm 1 đốt"
    assert g.food and g.food != g.snake[0], "Mồi mới phải respawn"

    # 3) Mồi vàng: +5 điểm rồi biến mất sau 5 giây
    hx, hy = g.snake[0]
    g.special = (hx + g.dir[0], hy + g.dir[1])
    g.special_deadline = pygame.time.get_ticks() + SPECIAL_LIFETIME_MS
    score0, length0 = g.score, len(g.snake)
    g.acc = 0
    g.update(1000 / g.speed + 1)
    assert g.score == score0 + SPECIAL_SCORE, "Mồi vàng phải +5 điểm"
    assert len(g.snake) == length0, "Mồi vàng không làm dài thêm"
    assert g.special is None, "Mồi vàng phải biến mất sau khi ăn"

    # 3b) Mồi vàng tự biến mất ngay khi quá hạn (kể cả không ăn)
    g.special = (0, 0)
    g.special_deadline = pygame.time.get_ticks() - 1  # đã quá hạn
    g.update(200)
    assert g.special is None, "Mồi vàng phải tự biến mất sau 5 giây"

    # 4) Cứ 5 mồi thì nhanh hơn
    g.speed = START_SPEED
    g.eaten = FOODS_PER_BOOST - 1
    hx, hy = g.snake[0]
    g.food = (hx + g.dir[0], hy + g.dir[1])
    g.acc = 0
    g.update(1000 / g.speed + 1)
    assert g.speed > START_SPEED, "Ăn đủ 5 mồi phải tăng tốc"
    assert g.speed <= MAX_SPEED, "Không được vượt trần tốc độ"

    # 5) Đâm tường -> thua
    g.game_over = False
    g.snake = deque([(COLS - 1, 2), (COLS - 2, 2), (COLS - 3, 2)])
    g.dir = (1, 0)
    g.pending.clear()
    g.update(1000)
    assert g.game_over, "Đâm tường phải thua"

    # 6) Đâm vào thân -> thua (đầu (4,4) đi trái, ngay trước là (3,4) thuộc thân,
    #    không phải ô đuôi)
    g.game_over = False
    g.snake = deque([(4, 4), (3, 4), (3, 5), (4, 5)])
    g.dir = (-1, 0)
    g.pending.clear()
    g.update(1000)
    assert g.game_over, "Đâm vào thân mình phải thua"

    # 7) Đâm vào ô đuôi vừa rời đi thì KHÔNG chết (nếu không đồng thời dài ra)
    g.game_over = False
    g.score, g.eaten, g.speed = 0, 0, START_SPEED
    g.food = (0, 0)
    g.snake = deque([(4, 4), (3, 4), (2, 4)])
    g.dir = (1, 0)            # đi phải, phía phải là (5,4) trống: sống
    g.acc = 0
    g.update(1000 / g.speed + 1)
    assert not g.game_over, "Không được chết oan khi ô đi qua trống"

    # 7b) bước vào ô đuôi vừa rời đi -> sống (không ăn mồi nên đuôi rơi ra trước)
    g.game_over = False
    g.snake = deque([(4, 4), (5, 4), (5, 5), (4, 5)])  # thân vòng quanh
    g.dir = (0, -1)             # trước là (4,3) trống -> sống
    g.acc = 0
    g.update(1000 / g.speed + 1)
    assert not g.game_over, "Trường hợp hợp lệ phải sống"

    # 8) Cấm quay đầu 180 độ
    g.game_over = False
    g.snake = deque([(5, 5), (4, 5), (3, 5)])
    g.dir = (1, 0)
    g.pending.append((-1, 0))   # bấm quay đầu 180°
    g.acc = 0
    g.update(1000 / g.speed + 1)
    assert g.dir == (1, 0), "Không được cho phép quay đầu 180 độ"
    assert not g.game_over

    # 9) Vẽ 1 khung không lỗi
    g.draw()
    print("Selftest OK")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
