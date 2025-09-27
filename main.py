import random
import tkinter as tk
from typing import List, Optional, Tuple


class SnakeGame:
    """Simple Snake game using Tkinter."""

    CELL_SIZE = 20
    COLUMNS = 20
    ROWS = 20
    MOVE_DELAY = 150  # milliseconds

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Змейка")

        canvas_width = self.COLUMNS * self.CELL_SIZE
        canvas_height = self.ROWS * self.CELL_SIZE

        self.score_var = tk.StringVar()
        self.score_var.set("Счёт: 0")

        self.score_label = tk.Label(self.root, textvariable=self.score_var, font=("Arial", 14))
        self.score_label.pack(pady=5)

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.root.bind("<Up>", lambda _: self.change_direction((0, -1)))
        self.root.bind("<Down>", lambda _: self.change_direction((0, 1)))
        self.root.bind("<Left>", lambda _: self.change_direction((-1, 0)))
        self.root.bind("<Right>", lambda _: self.change_direction((1, 0)))
        self.root.bind("<space>", lambda _: self.reset())

        self.running = False
        self.direction: Tuple[int, int] = (1, 0)
        self.snake: List[Tuple[int, int]] = []
        self.food: Optional[Tuple[int, int]] = None
        self.score = 0

        self.reset()

    def reset(self) -> None:
        """Reset the game state to the initial configuration."""
        self.running = True
        self.direction = (1, 0)
        start_x = self.COLUMNS // 2
        start_y = self.ROWS // 2
        self.snake = [(start_x - i, start_y) for i in range(3)]
        self.score = 0
        self.update_score()
        self.place_food()
        self.draw()
        self.schedule_move()

    def change_direction(self, new_direction: Tuple[int, int]) -> None:
        """Update the snake direction while preventing 180° turns."""
        if not self.running:
            return

        if not self.snake:
            return

        current_dx, current_dy = self.direction
        new_dx, new_dy = new_direction
        if (current_dx + new_dx, current_dy + new_dy) == (0, 0):
            return
        self.direction = new_direction

    def schedule_move(self) -> None:
        if self.running:
            self.root.after(self.MOVE_DELAY, self.move_snake)

    def move_snake(self) -> None:
        if not self.running:
            return

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if self.is_collision(new_head):
            self.game_over()
            return

        self.snake.insert(0, new_head)

        if self.food and new_head == self.food:
            self.score += 1
            self.update_score()
            self.place_food()
        else:
            self.snake.pop()

        self.draw()
        self.schedule_move()

    def is_collision(self, position: Tuple[int, int]) -> bool:
        x, y = position
        if x < 0 or y < 0 or x >= self.COLUMNS or y >= self.ROWS:
            return True
        return position in self.snake

    def place_food(self) -> None:
        available_cells = [
            (x, y)
            for x in range(self.COLUMNS)
            for y in range(self.ROWS)
            if (x, y) not in self.snake
        ]
        if not available_cells:
            self.food = None
            self.game_over(won=True)
            return
        self.food = random.choice(available_cells)

    def update_score(self) -> None:
        self.score_var.set(f"Счёт: {self.score}")

    def draw(self) -> None:
        self.canvas.delete("all")

        for x, y in self.snake:
            self.draw_cell(x, y, fill="lime")

        if self.food:
            self.draw_cell(*self.food, fill="red")

        if not self.running:
            self.canvas.create_text(
                self.COLUMNS * self.CELL_SIZE // 2,
                self.ROWS * self.CELL_SIZE // 2,
                text="Игра окончена. Нажмите пробел, чтобы перезапустить",
                fill="white",
                font=("Arial", 14),
                width=self.COLUMNS * self.CELL_SIZE - 40,
            )

    def draw_cell(self, x: int, y: int, fill: str) -> None:
        x1 = x * self.CELL_SIZE
        y1 = y * self.CELL_SIZE
        x2 = x1 + self.CELL_SIZE
        y2 = y1 + self.CELL_SIZE
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")

    def game_over(self, *, won: bool = False) -> None:
        self.running = False
        message = "Вы выиграли!" if won else "Столкновение!"
        self.score_var.set(f"{message} Счёт: {self.score}. Нажмите пробел для рестарта")
        self.draw()

    def start(self) -> None:
        self.root.mainloop()


def main() -> None:
    game = SnakeGame()
    game.start()


if __name__ == "__main__":
    main()
