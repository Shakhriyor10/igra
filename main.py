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
    SEGMENT_INSET_RATIO = 0.12

    BACKGROUND_COLOR = "#2e7d32"
    HEAD_COLOR = "#558b2f"
    BODY_COLORS = ("#8bc34a", "#7cb342")
    EYE_COLOR = "white"
    PUPIL_COLOR = "#1b5e20"
    FOOD_COLOR = "#d32f2f"

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Змейка")
        self.root.configure(bg=self.BACKGROUND_COLOR)

        canvas_width = self.COLUMNS * self.CELL_SIZE
        canvas_height = self.ROWS * self.CELL_SIZE

        self.score_var = tk.StringVar()
        self.score_var.set("Счёт: 0")

        self.score_label = tk.Label(
            self.root,
            textvariable=self.score_var,
            font=("Arial", 14),
            bg=self.BACKGROUND_COLOR,
            fg="white",
        )
        self.score_label.pack(pady=5)

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg=self.BACKGROUND_COLOR,
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
        self.head_feature_ids: List[int] = []

        self.segment_inset = self.CELL_SIZE * self.SEGMENT_INSET_RATIO

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
            self.canvas.create_oval(
                *self.cell_rect(x, y, inset=self.segment_inset),
                fill=self.BODY_COLORS[0],
                outline="",
            )
            for x, y in self.snake
        ]
        self.food_id = None
        if self.overlay_id is not None:
            self.canvas.delete(self.overlay_id)
            self.overlay_id = None
        for feature_id in self.head_feature_ids:
            self.canvas.delete(feature_id)
        self.head_feature_ids = []
        self.place_food()
        self.apply_segment_styles()
        self.update_head_features(force_create=True)
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
        self.update_head_features()

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
            head_coords = (
                old_coords[0]
                if old_coords
                else list(self.cell_rect(*new_head, inset=self.segment_inset))
            )
            new_head_id = self.canvas.create_oval(*head_coords, fill=self.HEAD_COLOR, outline="")
            old_segment_ids.insert(0, new_head_id)
            old_coords.insert(0, list(head_coords))

        self.segment_ids = old_segment_ids
        self.apply_segment_styles()
        new_coords = [
            self.cell_rect(x, y, inset=self.segment_inset) for x, y in self.snake
        ]
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

        x1, y1, x2, y2 = self.cell_rect(*self.food, inset=self.CELL_SIZE * 0.25)
        if self.food_id is None:
            self.food_id = self.canvas.create_oval(
                x1, y1, x2, y2, fill=self.FOOD_COLOR, outline=""
            )
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
            self.update_head_features()
            self.is_animating = False
            self.schedule_move()
            return

        progress = (step + 1) / self.ANIMATION_STEPS
        for segment_id, start, end in zip(segment_ids, start_coords, end_coords):
            interpolated = [
                start[i] + (end[i] - start[i]) * progress for i in range(4)
            ]
            self.canvas.coords(segment_id, *interpolated)
        self.update_head_features()

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

    def apply_segment_styles(self) -> None:
        if not self.segment_ids:
            return
        for index, segment_id in enumerate(self.segment_ids):
            if index == 0:
                color = self.HEAD_COLOR
            else:
                color = self.BODY_COLORS[(index - 1) % len(self.BODY_COLORS)]
            self.canvas.itemconfig(segment_id, fill=color)

    def update_head_features(self, *, force_create: bool = False) -> None:
        if not self.segment_ids:
            return

        head_coords = self.canvas.coords(self.segment_ids[0])
        if not head_coords:
            return

        eye_coords, pupil_coords = self._compute_eye_positions(head_coords)
        all_coords = eye_coords + pupil_coords

        if not self.head_feature_ids or force_create:
            for feature_id in self.head_feature_ids:
                self.canvas.delete(feature_id)
            self.head_feature_ids = []
            colors = [self.EYE_COLOR, self.EYE_COLOR, self.PUPIL_COLOR, self.PUPIL_COLOR]
            for color, coords in zip(colors, all_coords):
                feature_id = self.canvas.create_oval(*coords, fill=color, outline="")
                self.head_feature_ids.append(feature_id)
        else:
            for feature_id, coords in zip(self.head_feature_ids, all_coords):
                self.canvas.coords(feature_id, *coords)
        for feature_id in self.head_feature_ids:
            self.canvas.tag_raise(feature_id)

    def _compute_eye_positions(
        self, head_coords: List[float]
    ) -> Tuple[List[Tuple[float, float, float, float]], List[Tuple[float, float, float, float]]]:
        x1, y1, x2, y2 = head_coords
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius = (x2 - x1) / 2

        forward_offset = radius * 0.7
        side_offset = radius * 0.55
        eye_radius = radius * 0.35
        pupil_radius = eye_radius * 0.4

        dx, dy = self.direction
        if dx != 0:
            base_x = center_x + dx * forward_offset
            left_center = (base_x, center_y - side_offset)
            right_center = (base_x, center_y + side_offset)
        else:
            base_y = center_y + dy * forward_offset
            left_center = (center_x - side_offset, base_y)
            right_center = (center_x + side_offset, base_y)

        def oval_bounds(cx: float, cy: float, r: float) -> Tuple[float, float, float, float]:
            return (cx - r, cy - r, cx + r, cy + r)

        eye_bounds = [
            oval_bounds(*left_center, eye_radius),
            oval_bounds(*right_center, eye_radius),
        ]
        pupil_shift = radius * 0.3
        if dx != 0:
            pupil_left_center = (
                left_center[0] + dx * pupil_shift,
                left_center[1],
            )
            pupil_right_center = (
                right_center[0] + dx * pupil_shift,
                right_center[1],
            )
        else:
            pupil_left_center = (
                left_center[0],
                left_center[1] + dy * pupil_shift,
            )
            pupil_right_center = (
                right_center[0],
                right_center[1] + dy * pupil_shift,
            )

        pupil_bounds = [
            oval_bounds(*pupil_left_center, pupil_radius),
            oval_bounds(*pupil_right_center, pupil_radius),
        ]

        return eye_bounds, pupil_bounds


def main() -> None:
    game = SnakeGame()
    game.start()


if __name__ == "__main__":
    main()
