import random
import tkinter as tk
from typing import List, Optional, Tuple


class SnakeGame:
    """Simple Snake game using Tkinter."""

    CELL_SIZE = 20
    COLUMNS = 20
    ROWS = 20
    MOVE_DELAY = 50  # milliseconds between moves (in addition to animation)
    ANIMATION_STEPS = 5
    FRAME_DELAY = 20  # milliseconds between animation frames

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
        self.is_animating = False
        self.direction: Tuple[int, int] = (1, 0)
        self.snake: List[Tuple[int, int]] = []
        self.food: Optional[Tuple[int, int]] = None
        self.score = 0
        self.segment_ids: List[int] = []
        self.food_id: Optional[int] = None
        self.overlay_id: Optional[int] = None

        self.animation_token = 0

        self.reset()

    def reset(self) -> None:
        """Reset the game state to the initial configuration."""
        self.animation_token += 1
        self.running = True
        self.is_animating = False
        self.direction = (1, 0)
        start_x = self.COLUMNS // 2
        start_y = self.ROWS // 2
        self.snake = [(start_x - i, start_y) for i in range(3)]
        self.score = 0
        self.update_score()
        self.canvas.delete("all")
        self.segment_ids = [
            self.canvas.create_rectangle(*self.cell_rect(x, y), fill="lime", outline="")
            for x, y in self.snake
        ]
        self.food_id = None
        if self.overlay_id is not None:
            self.canvas.delete(self.overlay_id)
            self.overlay_id = None
        self.place_food()
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
        if self.running and not self.is_animating:
            self.root.after(self.MOVE_DELAY, self.move_snake)

    def move_snake(self) -> None:
        if not self.running or self.is_animating:
            return

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if self.is_collision(new_head):
            self.game_over()
            return

        old_segment_ids = list(self.segment_ids)
        old_coords = [self.canvas.coords(segment_id) for segment_id in old_segment_ids]

        self.snake.insert(0, new_head)

        ate_food = self.food is not None and new_head == self.food
        if ate_food:
            self.score += 1
            self.update_score()
            self.place_food()
        else:
            self.snake.pop()

        if ate_food:
            head_coords = old_coords[0] if old_coords else self.cell_rect(*new_head)
            new_head_id = self.canvas.create_rectangle(
                *head_coords, fill="lime", outline=""
            )
            old_segment_ids.insert(0, new_head_id)
            old_coords.insert(0, list(head_coords))

        self.segment_ids = old_segment_ids
        new_coords = [self.cell_rect(x, y) for x, y in self.snake]
        token = self.animation_token
        self.animate_segments(self.segment_ids, old_coords, new_coords, token=token)

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
        self.update_food_item()

    def update_score(self) -> None:
        self.score_var.set(f"Счёт: {self.score}")

    def update_food_item(self) -> None:
        if self.food is None:
            if self.food_id is not None:
                self.canvas.delete(self.food_id)
                self.food_id = None
            return

        x1, y1, x2, y2 = self.cell_rect(*self.food, inset=self.CELL_SIZE * 0.2)
        if self.food_id is None:
            self.food_id = self.canvas.create_oval(x1, y1, x2, y2, fill="red", outline="")
        else:
            self.canvas.coords(self.food_id, x1, y1, x2, y2)

    def cell_rect(
        self, x: int, y: int, *, inset: float = 0.0
    ) -> Tuple[float, float, float, float]:
        x1 = x * self.CELL_SIZE + inset
        y1 = y * self.CELL_SIZE + inset
        x2 = (x + 1) * self.CELL_SIZE - inset
        y2 = (y + 1) * self.CELL_SIZE - inset
        return (x1, y1, x2, y2)

    def animate_segments(
        self,
        segment_ids: List[int],
        start_coords: List[List[float]],
        end_coords: List[Tuple[float, float, float, float]],
        *,
        token: int,
        step: int = 0,
    ) -> None:
        if token != self.animation_token or not segment_ids:
            self.schedule_move()
            return

        if step == 0:
            self.is_animating = True

        if step >= self.ANIMATION_STEPS:
            for segment_id, coords in zip(segment_ids, end_coords):
                self.canvas.coords(segment_id, *coords)
            self.is_animating = False
            self.schedule_move()
            return

        progress = (step + 1) / self.ANIMATION_STEPS
        for segment_id, start, end in zip(segment_ids, start_coords, end_coords):
            interpolated = [
                start[i] + (end[i] - start[i]) * progress for i in range(4)
            ]
            self.canvas.coords(segment_id, *interpolated)

        self.root.after(
            self.FRAME_DELAY,
            lambda: self.animate_segments(
                segment_ids,
                start_coords,
                end_coords,
                token=token,
                step=step + 1,
            ),
        )

    def game_over(self, *, won: bool = False) -> None:
        self.running = False
        self.is_animating = False
        message = "Вы выиграли!" if won else "Столкновение!"
        self.score_var.set(
            f"{message} Счёт: {self.score}. Нажмите пробел для рестарта"
        )
        overlay_text = "Игра окончена. Нажмите пробел, чтобы перезапустить"
        if self.overlay_id is not None:
            self.canvas.delete(self.overlay_id)
        self.overlay_id = self.canvas.create_text(
            self.COLUMNS * self.CELL_SIZE // 2,
            self.ROWS * self.CELL_SIZE // 2,
            text=overlay_text,
            fill="white",
            font=("Arial", 14),
            width=self.COLUMNS * self.CELL_SIZE - 40,
        )

    def start(self) -> None:
        self.root.mainloop()


def main() -> None:
    game = SnakeGame()
    game.start()


if __name__ == "__main__":
    main()
