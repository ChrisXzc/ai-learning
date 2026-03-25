import random
import tkinter as tk


CELL_SIZE = 90
ROWS = 5
COLS = 9
BOARD_LEFT = 80
BOARD_TOP = 60
BOARD_WIDTH = CELL_SIZE * COLS
BOARD_HEIGHT = CELL_SIZE * ROWS
WINDOW_WIDTH = BOARD_LEFT + BOARD_WIDTH + 60
WINDOW_HEIGHT = BOARD_TOP + BOARD_HEIGHT + 120

SUNFLOWER_COST = 50
PEASHOOTER_COST = 100
INITIAL_SUN = 150
ZOMBIE_HP = 6
PEA_DAMAGE = 1
SPAWN_MIN_MS = 1700
SPAWN_MAX_MS = 2800


class Plant:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.hp = 6

    @property
    def x(self) -> int:
        return BOARD_LEFT + self.col * CELL_SIZE + CELL_SIZE // 2

    @property
    def y(self) -> int:
        return BOARD_TOP + self.row * CELL_SIZE + CELL_SIZE // 2


class Sunflower(Plant):
    kind = "sunflower"

    def __init__(self, row: int, col: int):
        super().__init__(row, col)
        self.generate_cd = random.randint(3500, 5500)
        self.elapsed = 0


class Peashooter(Plant):
    kind = "peashooter"

    def __init__(self, row: int, col: int):
        super().__init__(row, col)
        self.shoot_cd = 1100
        self.elapsed = 0


class Zombie:
    def __init__(self, row: int):
        self.row = row
        self.hp = ZOMBIE_HP
        self.speed = random.uniform(0.18, 0.32)
        self.x = BOARD_LEFT + BOARD_WIDTH + 30
        self.y = BOARD_TOP + row * CELL_SIZE + CELL_SIZE // 2
        self.attack_cd = 850
        self.elapsed = 0


class Pea:
    def __init__(self, row: int, x: float):
        self.row = row
        self.x = x
        self.y = BOARD_TOP + row * CELL_SIZE + CELL_SIZE // 2
        self.speed = 8


class PvZMini:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("植物大战僵尸 - 迷你版")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg="#86d57c", highlightthickness=0)
        self.canvas.pack()

        self.selected = "peashooter"
        self.sun = INITIAL_SUN
        self.score = 0
        self.game_over = False

        self.grid: list[list[Plant | None]] = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.zombies: list[Zombie] = []
        self.peas: list[Pea] = []
        self.floating_texts: list[tuple[float, float, int, int]] = []

        self.spawn_timer = random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("1", lambda _e: self.set_selected("sunflower"))
        self.root.bind("2", lambda _e: self.set_selected("peashooter"))
        self.root.bind("<space>", lambda _e: self.restart())

        self.loop()

    def restart(self):
        self.sun = INITIAL_SUN
        self.score = 0
        self.game_over = False
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.zombies.clear()
        self.peas.clear()
        self.floating_texts.clear()
        self.spawn_timer = random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

    def set_selected(self, plant_kind: str):
        self.selected = plant_kind

    def on_click(self, event: tk.Event):
        if self.game_over:
            return

        row = (event.y - BOARD_TOP) // CELL_SIZE
        col = (event.x - BOARD_LEFT) // CELL_SIZE
        if not (0 <= row < ROWS and 0 <= col < COLS):
            return

        if self.grid[row][col] is not None:
            return

        if self.selected == "sunflower":
            if self.sun < SUNFLOWER_COST:
                return
            self.sun -= SUNFLOWER_COST
            self.grid[row][col] = Sunflower(row, col)
        elif self.selected == "peashooter":
            if self.sun < PEASHOOTER_COST:
                return
            self.sun -= PEASHOOTER_COST
            self.grid[row][col] = Peashooter(row, col)

    def update(self, dt_ms: int):
        if self.game_over:
            return

        self.spawn_timer -= dt_ms
        if self.spawn_timer <= 0:
            self.zombies.append(Zombie(random.randint(0, ROWS - 1)))
            self.spawn_timer = random.randint(SPAWN_MIN_MS, SPAWN_MAX_MS)

        for r in range(ROWS):
            for c in range(COLS):
                plant = self.grid[r][c]
                if plant is None:
                    continue

                if isinstance(plant, Sunflower):
                    plant.elapsed += dt_ms
                    if plant.elapsed >= plant.generate_cd:
                        self.sun += 25
                        self.floating_texts.append((plant.x, plant.y - 20, 25, 40))
                        plant.elapsed = 0
                        plant.generate_cd = random.randint(3500, 5500)

                if isinstance(plant, Peashooter):
                    has_target = any(z.row == r and z.x > plant.x - 10 for z in self.zombies)
                    if has_target:
                        plant.elapsed += dt_ms
                        if plant.elapsed >= plant.shoot_cd:
                            self.peas.append(Pea(r, plant.x + 10))
                            plant.elapsed = 0
                    else:
                        plant.elapsed = 0

        for pea in list(self.peas):
            pea.x += pea.speed
            hit = None
            for zombie in self.zombies:
                if zombie.row == pea.row and abs(zombie.x - pea.x) < 22:
                    hit = zombie
                    break
            if hit:
                hit.hp -= PEA_DAMAGE
                if pea in self.peas:
                    self.peas.remove(pea)
            elif pea.x > BOARD_LEFT + BOARD_WIDTH + 20:
                self.peas.remove(pea)

        for zombie in list(self.zombies):
            col = int((zombie.x - BOARD_LEFT) // CELL_SIZE)
            plant = self.grid[zombie.row][col] if 0 <= col < COLS else None

            if plant and abs(zombie.x - plant.x) < 30:
                zombie.elapsed += dt_ms
                if zombie.elapsed >= zombie.attack_cd:
                    plant.hp -= 1
                    zombie.elapsed = 0
                    if plant.hp <= 0:
                        self.grid[zombie.row][col] = None
            else:
                zombie.x -= zombie.speed * dt_ms

            if zombie.hp <= 0:
                self.score += 1
                self.zombies.remove(zombie)

            if zombie.x <= BOARD_LEFT - 15:
                self.game_over = True

        for i in range(len(self.floating_texts) - 1, -1, -1):
            x, y, val, life = self.floating_texts[i]
            life -= 1
            if life <= 0:
                self.floating_texts.pop(i)
            else:
                self.floating_texts[i] = (x, y - 0.4, val, life)

    def draw(self):
        self.canvas.delete("all")

        self.canvas.create_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, fill="#9cdf86", outline="")
        self.canvas.create_rectangle(BOARD_LEFT, BOARD_TOP, BOARD_LEFT + BOARD_WIDTH, BOARD_TOP + BOARD_HEIGHT, fill="#66bb55", outline="#2e6f2c", width=3)

        for r in range(ROWS):
            for c in range(COLS):
                x1 = BOARD_LEFT + c * CELL_SIZE
                y1 = BOARD_TOP + r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                shade = "#6dc55b" if (r + c) % 2 == 0 else "#62b854"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=shade, outline="#4d8f3f")

        for r in range(ROWS):
            for c in range(COLS):
                plant = self.grid[r][c]
                if plant is None:
                    continue
                if isinstance(plant, Sunflower):
                    self.draw_sunflower(plant)
                elif isinstance(plant, Peashooter):
                    self.draw_peashooter(plant)

        for pea in self.peas:
            self.canvas.create_oval(pea.x - 6, pea.y - 6, pea.x + 6, pea.y + 6, fill="#9efc6f", outline="#3c8b27", width=2)

        for zombie in self.zombies:
            self.draw_zombie(zombie)

        for x, y, val, _life in self.floating_texts:
            self.canvas.create_text(x, y, text=f"+{val}", fill="#ffe46f", font=("Arial", 12, "bold"))

        self.draw_ui()

    def draw_ui(self):
        self.canvas.create_text(18, 28, anchor="w", text=f"阳光: {self.sun}", font=("Arial", 17, "bold"), fill="#2d2d2d")
        self.canvas.create_text(210, 28, anchor="w", text=f"击败僵尸: {self.score}", font=("Arial", 15), fill="#2d2d2d")

        def card(x: int, label: str, cost: int, kind: str):
            chosen = self.selected == kind
            color = "#ffe08a" if chosen else "#f2f2f2"
            border = "#e2a43d" if chosen else "#666666"
            self.canvas.create_rectangle(x, WINDOW_HEIGHT - 52, x + 128, WINDOW_HEIGHT - 12, fill=color, outline=border, width=3 if chosen else 2)
            self.canvas.create_text(x + 10, WINDOW_HEIGHT - 32, anchor="w", text=label, font=("Arial", 12, "bold"), fill="#222")
            self.canvas.create_text(x + 120, WINDOW_HEIGHT - 32, anchor="e", text=str(cost), font=("Arial", 12), fill="#555")

        card(20, "1 向日葵", SUNFLOWER_COST, "sunflower")
        card(165, "2 豌豆射手", PEASHOOTER_COST, "peashooter")

        if self.game_over:
            self.canvas.create_rectangle(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, fill="#000", stipple="gray50", outline="")
            self.canvas.create_text(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20, text="游戏结束", fill="white", font=("Arial", 34, "bold"))
            self.canvas.create_text(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20, text="按空格键重新开始", fill="white", font=("Arial", 16))

    def draw_sunflower(self, plant: Sunflower):
        x, y = plant.x, plant.y
        for angle in range(0, 360, 45):
            dx = 16 * (1 if angle in (0, 45, 315) else -1 if angle in (135, 180, 225) else 0)
            dy = 16 * (1 if angle in (225, 270, 315) else -1 if angle in (45, 90, 135) else 0)
            self.canvas.create_oval(x - 9 + dx, y - 9 + dy, x + 9 + dx, y + 9 + dy, fill="#ffd24c", outline="#d9902f")
        self.canvas.create_oval(x - 13, y - 13, x + 13, y + 13, fill="#a05a2c", outline="#6d371a", width=2)
        self.canvas.create_line(x, y + 10, x, y + 30, fill="#2f8b3a", width=4)

    def draw_peashooter(self, plant: Peashooter):
        x, y = plant.x, plant.y
        self.canvas.create_oval(x - 15, y - 16, x + 16, y + 16, fill="#69ce5e", outline="#2b7b2a", width=2)
        self.canvas.create_oval(x + 10, y - 9, x + 34, y + 9, fill="#69ce5e", outline="#2b7b2a", width=2)
        self.canvas.create_oval(x + 28, y - 5, x + 38, y + 5, fill="#4caa42", outline="#2b7b2a")
        self.canvas.create_line(x - 3, y + 12, x - 3, y + 30, fill="#2f8b3a", width=4)

    def draw_zombie(self, zombie: Zombie):
        x, y = zombie.x, zombie.y
        self.canvas.create_rectangle(x - 12, y - 24, x + 12, y + 17, fill="#8a99a5", outline="#5f6b74", width=2)
        self.canvas.create_oval(x - 11, y - 36, x + 11, y - 14, fill="#b0d7a3", outline="#668b62", width=2)
        self.canvas.create_oval(x - 6, y - 29, x - 1, y - 24, fill="#222", outline="")
        self.canvas.create_oval(x + 2, y - 29, x + 7, y - 24, fill="#222", outline="")
        hp_text = f"{max(zombie.hp, 0)}"
        self.canvas.create_text(x, y - 45, text=hp_text, fill="#fff", font=("Arial", 10, "bold"))

    def loop(self):
        self.update(50)
        self.draw()
        self.root.after(50, self.loop)


def main():
    root = tk.Tk()
    PvZMini(root)
    root.mainloop()


if __name__ == "__main__":
    main()
