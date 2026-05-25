from builtins import len
import time
import threading

from puzzle_logic import (
    bfs, dfs, ids, ucs, get_path,
    random_state, is_solvable,
    goal, DFS_MAX_DEPTH
)
from puzzle_ui import PuzzleUI


class PuzzleApp:

    def __init__(self):
        self.goal_state    = [row[:] for row in goal]
        self.current_state = random_state(self.goal_state)
        self.path          = []
        self.step_index    = 0
        self.running       = False
        self._after_id     = None
        self._solve_id     = 0

        self.ui = PuzzleUI(
            on_random_cb      = self.on_random,
            on_start_cb       = self.on_start,
            on_stop_cb        = self.on_stop,
            on_set_initial_cb = self.on_set_initial,
            on_set_goal_cb    = self.on_set_goal,
        )

        self.ui.refresh_input_grids(self.current_state, self.goal_state)
        self.ui.draw_grid(self.current_state, self.goal_state)

    def run(self):
        self.ui.mainloop()

    def on_random(self):
        self.running = False
        self._cancel_animation()
        self._solve_id += 1
        self.current_state = random_state(self.goal_state)
        self.path          = []
        self.step_index    = 0
        self._reset_stats()
        self.ui.clear_steps()
        self.ui.refresh_input_grids(self.current_state, self.goal_state)
        self.ui.draw_grid(self.current_state, self.goal_state)

    def on_set_initial(self, state):
        if self.running:
            return
        if not is_solvable(state, self.goal_state):
            self.ui.show_toast("Puzzle này KHÔNG giải được với trạng thái đích hiện tại!")
            return
        self._cancel_animation()
        self.current_state = state
        self.path          = []
        self.step_index    = 0
        self._reset_stats()
        self.ui.clear_steps()
        self.ui.draw_grid(self.current_state, self.goal_state)

    def on_set_goal(self, state):
        if self.running:
            return
        if not is_solvable(self.current_state, state):
            self.ui.show_toast("Trạng thái đích này khiến puzzle KHÔNG giải được!")
            return
        self._cancel_animation()
        self.goal_state = state
        self.path       = []
        self.step_index = 0
        self._reset_stats()
        self.ui.clear_steps()
        self.ui.draw_grid(self.current_state, self.goal_state)

    def on_start(self):
        if not is_solvable(self.current_state, self.goal_state):
            self.ui.show_toast("Puzzle này không giải được!")
            return

        self.running = False
        self._cancel_animation()
        self.path       = []
        self.step_index = 0
        self._solve_id += 1
        self.running    = True

        algo = self.ui.get_algorithm()
        self.ui.set_stat("BƯỚC",        0)
        self.ui.set_stat("TỔNG_BƯỚC",  "...")
        self.ui.set_stat("THỜI_GIAN",  "...")
        self.ui.set_stat("TRẠNG_THÁI", f"Đang giải ({algo})...")
        self.ui.set_buttons(running=True)
        self.ui.clear_steps()

        threading.Thread(target=self._solve_worker, daemon=True).start()

    def on_stop(self):
        if not self.path or self.step_index >= len(self.path):
            return
        if self.running:
            self.running = False
            self._cancel_animation()
            self.ui.set_stat("TRẠNG_THÁI", "Đã tạm dừng")
            self.ui.set_pause_mode(paused=True)
        else:
            self.running = True
            self.ui.set_stat("TRẠNG_THÁI", "Đang chạy...")
            self.ui.set_pause_mode(paused=False)
            self._animate_next()

    def _solve_worker(self):
        my_id = self._solve_id
        algo  = self.ui.get_algorithm()
        t0    = time.time()

        def stop_flag():
            return self._solve_id != my_id

        if algo == "BFS":
            result = bfs(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "DFS":
            result = dfs(self.current_state, self.goal_state, stop_flag=stop_flag)
        elif algo == "UCS":
            result = ucs(self.current_state, self.goal_state, stop_flag=stop_flag)
        else:
            result = ids(self.current_state, self.goal_state, stop_flag=stop_flag)

        elapsed = time.time() - t0

        if my_id != self._solve_id:
            return

        if result is None:
            self.ui.after(0, lambda: self.ui.show_toast(
                f"{algo} không tìm được lời giải"))
            self.ui.after(0, lambda: self.ui.set_stat("TRẠNG_THÁI", "Không tìm được"))
            self.ui.after(0, lambda: self.ui.set_buttons(running=False))
            self.running = False
            return

        self.path = get_path(result)
        total     = len(self.path) - 1

        elapsed_str = f"{elapsed*1000:.0f}ms" if elapsed < 1 else f"{elapsed:.2f}s"
        self.ui.after(0, lambda: self.ui.set_stat("TỔNG_BƯỚC",  total))
        self.ui.after(0, lambda: self.ui.set_stat("THỜI_GIAN",  elapsed_str))
        self.ui.after(0, lambda: self.ui.set_stat("TRẠNG_THÁI", "Chờ..."))

        self.ui.after(0, lambda: self.ui.load_steps(self.path))
        self.ui.after(50, self._animate_next)

    def _animate_next(self):
        if not self.running:
            return
        if self.step_index >= len(self.path):
            self.running = False
            self.ui.set_stat("TRẠNG_THÁI", "Hoàn thành")
            self.ui.set_buttons(running=False)
            return

        if self.step_index == 1:
            self.ui.set_stat("TRẠNG_THÁI", "Đang chạy...")

        _, state = self.path[self.step_index]
        if self.step_index >= 1:
            self.ui.set_stat("BƯỚC", self.step_index)

        self.ui.draw_grid(state, self.goal_state)

        # Highlight bước tương ứng trong bảng bên trái
        self.ui.highlight_step(self.step_index)

        self.step_index += 1
        self._after_id = self.ui.after(self.ui.get_delay_ms(), self._animate_next)

    def _cancel_animation(self):
        if self._after_id is not None:
            self.ui.after_cancel(self._after_id)
            self._after_id = None

    def _reset_stats(self):
        self.ui.set_stat("BƯỚC",        0)
        self.ui.set_stat("TỔNG_BƯỚC",  "—")
        self.ui.set_stat("THỜI_GIAN",  "—")
        self.ui.set_stat("TRẠNG_THÁI", "Chờ...")


if __name__ == "__main__":
    app = PuzzleApp()
    app.run()