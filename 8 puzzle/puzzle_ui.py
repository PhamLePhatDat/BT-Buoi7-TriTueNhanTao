import tkinter as tk

TILE_SIZE   = 80
GRID_PAD    = 10
TILE_RADIUS = 12

BG          = "#0f0e17"
SURFACE     = "#1a1a2e"
TILE_BG     = "#16213e"
TILE_ACTIVE = "#0f3460"
TILE_GOAL   = "#1b4332"
ACCENT      = "#e94560"
ACCENT2     = "#f5a623"
TEXT_LIGHT  = "#eaeaea"
TEXT_DIM    = "#888aaa"
BTN_START   = "#e94560"
BTN_RANDOM  = "#0f3460"
BTN_STOP    = "#555577"
ALGO_BFS    = "#0f3460"
ALGO_DFS    = "#3d0f46"
ALGO_IDS    = "#1a3d1a"
ALGO_UCS    = "#2d2a00"
ENTRY_BG    = "#16213e"
ENTRY_OK    = "#0f3460"
TOAST_ERR   = "#c0392b"
TOAST_OK    = "#1b4332"
SECTION_BG  = "#13121f"
STEP_BG     = "#12111e"
STEP_DONE   = "#0f3460"
STEP_ACTIVE = "#e94560"

NUM_MIN = 0
NUM_MAX = 8


class PuzzleUI(tk.Tk):

    def __init__(self, on_random_cb, on_start_cb, on_stop_cb,
                 on_set_initial_cb, on_set_goal_cb):
        super().__init__()
        self.title("8-Puzzle Solver")
        self.geometry("900x720")
        self.resizable(True, True)
        self.configure(bg=BG)

        self._on_random_cb      = on_random_cb
        self._on_start_cb       = on_start_cb
        self._on_stop_cb        = on_stop_cb
        self._on_set_initial_cb = on_set_initial_cb
        self._on_set_goal_cb    = on_set_goal_cb

        self._step_delay_ms  = 400
        self._algo_var       = tk.StringVar(value="BFS")
        self._toast_after    = None
        self._initial_var    = tk.StringVar()
        self._goal_var       = tk.StringVar()
        self._initial_entry  = None
        self._goal_entry     = None
        self._initial_err_lbl = None
        self._goal_err_lbl   = None
        self._last_valid_initial = ""
        self._last_valid_goal    = ""

        self._step_actions   = []   
        self._current_step   = -1

        self._build_ui()
        self.update_idletasks()
        self.minsize(700, 580)

    def _build_ui(self):
        PAD = 14

        # Title
        title_frame = tk.Frame(self, bg=BG)
        title_frame.pack(fill="x", padx=PAD, pady=(8, 2))
        tk.Label(title_frame, text="8", font=("Courier New", 16, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(title_frame, text="-PUZZLE", font=("Courier New", 14, "bold"),
                 fg=TEXT_LIGHT, bg=BG).pack(side="left", pady=(2, 0))
        tk.Label(title_frame, text="SOLVER", font=("Courier New", 8),
                 fg=TEXT_DIM, bg=BG).pack(side="right", pady=(3, 0))
        tk.Frame(self, bg=ACCENT, height=1).pack(fill="x", padx=PAD, pady=(0, 6))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=PAD, pady=(0, 8))

        body.columnconfigure(0, weight=1, uniform="half")
        body.columnconfigure(1, weight=1, uniform="half")
        body.rowconfigure(0, weight=1)

        self._build_step_panel(body)

        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        canvas_size = TILE_SIZE * 3 + GRID_PAD * 4
        self.canvas = tk.Canvas(right, width=canvas_size, height=canvas_size,
                                bg=SURFACE, highlightthickness=0)
        self.canvas.pack()

        self._toast = tk.Label(right, text="",
                               font=("Courier New", 7, "bold"),
                               fg=TEXT_LIGHT, bg=TOAST_ERR, padx=8, pady=3)

        # Stats
        stats_frame = tk.Frame(right, bg=SURFACE)
        stats_frame.pack(fill="x", pady=(5, 0))
        self._make_stat_inline(stats_frame, "BƯỚC",       "0"     ).pack(side="left", expand=True)
        tk.Frame(stats_frame, bg=BG, width=1).pack(side="left", fill="y")
        self._make_stat_inline(stats_frame, "TỔNG_BƯỚC",  "—"     ).pack(side="left", expand=True)
        tk.Frame(stats_frame, bg=BG, width=1).pack(side="left", fill="y")
        self._make_stat_inline(stats_frame, "THỜI_GIAN",  "—"     ).pack(side="left", expand=True)
        tk.Frame(stats_frame, bg=BG, width=1).pack(side="left", fill="y")
        self._make_stat_inline(stats_frame, "TRẠNG_THÁI", "Chờ...").pack(side="left", expand=True)

        # Algo
        algo_frame = tk.Frame(right, bg=SECTION_BG)
        algo_frame.pack(fill="x", pady=(8, 0))
        algo_inner = tk.Frame(algo_frame, bg=SECTION_BG)
        algo_inner.pack(fill="x", padx=8, pady=4)
        tk.Label(algo_inner, text="Thuật Toán:", font=("Courier New", 7),
                 fg=TEXT_DIM, bg=SECTION_BG).pack(side="left", padx=(0, 6))
        for algo, color in [("BFS", ALGO_BFS), ("DFS", ALGO_DFS), ("IDS", ALGO_IDS), ("UCS", ALGO_UCS)]:
            tk.Radiobutton(
                algo_inner, text=f" {algo} ",
                variable=self._algo_var, value=algo,
                font=("Courier New", 8, "bold"),
                fg=TEXT_LIGHT, bg=color,
                selectcolor=ACCENT,
                activebackground=ACCENT, activeforeground=TEXT_LIGHT,
                indicatoron=False, relief="flat",
                padx=10, pady=3, cursor="hand2"
            ).pack(side="left", padx=(0, 4))

        input_outer = tk.Frame(right, bg=BG)
        input_outer.pack(fill="x", pady=(6, 0))
        p1, self._initial_entry, self._initial_err_lbl = \
            self._make_input_panel(input_outer, "Trạng thái ban đầu", self._initial_var)
        p1.pack(fill="x", pady=(0, 3))
        p2, self._goal_entry, self._goal_err_lbl = \
            self._make_input_panel(input_outer, "Trạng thái đích", self._goal_var)
        p2.pack(fill="x")
        tk.Button(input_outer, text="Áp dụng",
                  font=("Courier New", 7, "bold"),
                  bg=ACCENT, fg=TEXT_LIGHT,
                  activebackground="#c73652", activeforeground=TEXT_LIGHT,
                  relief="flat", padx=10, pady=3, cursor="hand2",
                  command=self._on_apply_both).pack(anchor="w", pady=(4, 0))

        speed_frame = tk.Frame(right, bg=BG)
        speed_frame.pack(fill="x", pady=(7, 0))
        speed_row = tk.Frame(speed_frame, bg=BG)
        speed_row.pack(fill="x")
        tk.Label(speed_row, text="Tốc độ:", font=("Courier New", 7),
                 fg=TEXT_DIM, bg=BG).pack(side="left")
        tk.Label(speed_row, text="Chậm", font=("Courier New", 7),
                 fg=TEXT_DIM, bg=BG).pack(side="left", padx=(4, 0))
        self._speed_var = tk.IntVar(value=400)
        tk.Scale(speed_row, from_=100, to=1500, orient="horizontal",
                 variable=self._speed_var, bg=BG, fg=TEXT_LIGHT,
                 highlightthickness=0, troughcolor=TILE_BG,
                 activebackground=ACCENT, sliderrelief="flat", length=140,
                 command=self._on_speed_change, showvalue=False
                 ).pack(side="left", padx=2)
        tk.Label(speed_row, text="Nhanh", font=("Courier New", 7),
                 fg=TEXT_DIM, bg=BG).pack(side="left")
        self._speed_label = tk.Label(speed_row, text="400ms",
                                     font=("Courier New", 7, "bold"),
                                     fg=ACCENT2, bg=BG, width=5)
        self._speed_label.pack(side="left", padx=(4, 0))

        btn_frame = tk.Frame(right, bg=BG)
        btn_frame.pack(fill="x", pady=(8, 4))
        self.btn_random = self._make_button(btn_frame, "Random Puzzle", BTN_RANDOM, self._on_random_cb)
        self.btn_random.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.btn_start = self._make_button(btn_frame, "Giải", BTN_START, self._on_start_cb)
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.btn_stop = self._make_button(btn_frame, "Dừng", BTN_STOP, self._on_stop_cb)
        self.btn_stop.pack(side="left", expand=True, fill="x")
        self.btn_stop.config(state="disabled")
        self._is_paused = False

    def _build_step_panel(self, parent):
        outer = tk.Frame(parent, bg=STEP_BG)
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 0))

        hdr = tk.Frame(outer, bg=ACCENT, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="CÁC BƯỚC THỰC HIỆN",
                 font=("Courier New", 8, "bold"),
                 fg=TEXT_LIGHT, bg=ACCENT).pack(expand=True)

        scroll_frame = tk.Frame(outer, bg=STEP_BG)
        scroll_frame.pack(fill="both", expand=True, padx=6, pady=6)

        sb = tk.Scrollbar(scroll_frame, orient="vertical",
                          bg=STEP_BG, troughcolor=STEP_BG,
                          activebackground=ACCENT)
        sb.pack(side="right", fill="y")

        self._step_text = tk.Text(
            scroll_frame,
            wrap="word",              
            font=("Courier New", 11, "bold"),
            bg=STEP_BG,
            fg=TEXT_DIM,
            insertbackground=TEXT_LIGHT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            yscrollcommand=sb.set,
            state="disabled",         
            cursor="arrow",
            spacing1=2,             
            spacing3=2,
        )
        self._step_text.pack(side="left", fill="both", expand=True)
        sb.config(command=self._step_text.yview)

        self._step_text.bind("<MouseWheel>", lambda e: self._step_text.yview_scroll(
            -1 if e.delta > 0 else 1, "units"))

        self._step_text.tag_config("done",    foreground=STEP_DONE)   
        self._step_text.tag_config("active",  foreground=ACCENT,
                                   background="#2a0a10")            
        self._step_text.tag_config("pending", foreground=TEXT_DIM)  
        self._step_text.tag_config("sep",     foreground="#333355")   
    def clear_steps(self):
        self._step_actions = []
        self._current_step = -1
        self._step_text.config(state="normal")
        self._step_text.delete("1.0", "end")
        self._step_text.config(state="disabled")

    def load_steps(self, path):
        self.clear_steps()
        self._step_actions = [a for a, _ in path if a != "Start"]

        self._step_text.config(state="normal")
        for i, act in enumerate(self._step_actions):
            tag_name = f"s{i}"
            self._step_text.insert("end", act, (tag_name, "pending"))
            if i < len(self._step_actions) - 1:
                self._step_text.insert("end", " ", "sep")
        self._step_text.config(state="disabled")
        self._step_text.yview_moveto(0)

    def highlight_step(self, step_index):
        act_idx = step_index - 1   
        if act_idx < 0 or not self._step_actions:
            return

        old = self._current_step

        if 0 <= old < len(self._step_actions):
            tag_old = f"s{old}"
            self._step_text.tag_remove("active",  tag_old + ".first", tag_old + ".last")
            self._step_text.tag_remove("pending", tag_old + ".first", tag_old + ".last")
            self._step_text.tag_add("done",       tag_old + ".first", tag_old + ".last")

        self._current_step = act_idx

        if act_idx < len(self._step_actions):
            tag_cur = f"s{act_idx}"
            self._step_text.tag_remove("pending", tag_cur + ".first", tag_cur + ".last")
            self._step_text.tag_add("active",     tag_cur + ".first", tag_cur + ".last")

            self._step_text.see(tag_cur + ".first")

    def _make_stat_inline(self, parent, key, value):
        frame = tk.Frame(parent, bg=SURFACE, padx=8, pady=6)
        display = key.replace("_", " ")
        tk.Label(frame, text=display + ": ",
                 font=("Courier New", 7), fg=TEXT_DIM, bg=SURFACE).pack(side="left")
        lbl = tk.Label(frame, text=value,
                       font=("Courier New", 10, "bold"), fg=ACCENT2, bg=SURFACE)
        lbl.pack(side="left")
        setattr(self, f"_stat_{key}", lbl)
        return frame

    def _make_input_panel(self, parent, label, str_var):
        panel = tk.Frame(parent, bg=SECTION_BG)
        header = tk.Frame(panel, bg=SECTION_BG)
        header.pack(fill="x", padx=8, pady=(4, 1))
        tk.Label(header, text=label, font=("Courier New", 7, "bold"),
                 fg=TEXT_DIM, bg=SECTION_BG).pack(side="left")

        entry_row = tk.Frame(panel, bg=SECTION_BG)
        entry_row.pack(fill="x", padx=8, pady=(0, 1))
        placeholder = "Vd: 1 2 3 4 0 5 6 7 8"
        entry = tk.Entry(entry_row, textvariable=str_var,
                         font=("Courier New", 8, "bold"),
                         bg=ENTRY_BG, fg=TEXT_LIGHT,
                         insertbackground=TEXT_LIGHT,
                         relief="flat", bd=0,
                         highlightthickness=2,
                         highlightbackground="#1a1a2e",
                         highlightcolor=ACCENT)
        entry.pack(fill="x", expand=True, ipady=1)

        def _focus_in(e, sv=str_var, ph=placeholder):
            if sv.get() == ph:
                sv.set(""); entry.config(fg=TEXT_LIGHT)
        def _focus_out(e, sv=str_var, ph=placeholder):
            if sv.get().strip() == "":
                sv.set(ph); entry.config(fg=TEXT_DIM)

        if str_var.get() == "":
            str_var.set(placeholder); entry.config(fg=TEXT_DIM)

        entry.bind("<FocusIn>",  _focus_in)
        entry.bind("<FocusOut>", _focus_out)
        entry.bind("<Return>",   lambda e: self._on_apply_both())

        err_lbl = tk.Label(panel, text="", font=("Courier New", 6),
                           fg=ACCENT, bg=SECTION_BG, anchor="w")
        err_lbl.pack(fill="x", padx=8, pady=(0, 3))
        return panel, entry, err_lbl

    def _on_apply_both(self):
        state_i = self._parse_input(self._initial_var, self._initial_entry, self._initial_err_lbl)
        state_g = self._parse_input(self._goal_var,    self._goal_entry,    self._goal_err_lbl)

        if state_i is None and self._last_valid_initial:
            self._initial_var.set(self._last_valid_initial)
            self._set_entry_state(self._initial_entry, self._initial_err_lbl, "Đã khôi phục giá trị cũ", error=True)
        if state_g is None and self._last_valid_goal:
            self._goal_var.set(self._last_valid_goal)
            self._set_entry_state(self._goal_entry, self._goal_err_lbl, "Đã khôi phục giá trị cũ", error=True)
        if state_i is None or state_g is None:
            return

        self._last_valid_initial = self._initial_var.get()
        self._last_valid_goal    = self._goal_var.get()
        self._on_set_goal_cb(state_g)
        self._on_set_initial_cb(state_i)

    def _parse_input(self, str_var, entry_widget, err_lbl):
        raw = str_var.get().strip()
        if raw.startswith("Vd:") or raw == "":
            self._set_entry_state(entry_widget, err_lbl, "Vui lòng nhập 9 số", error=True)
            return None
        tokens = raw.split()
        if len(tokens) < 9:
            self._set_entry_state(entry_widget, err_lbl,
                                  f"Thiếu số - cần 9 số, hiện có {len(tokens)}", error=True)
            return None
        if len(tokens) > 9:
            self._set_entry_state(entry_widget, err_lbl,
                                  f"Quá nhiều - cần 9 số, hiện có {len(tokens)}", error=True)
            return None
        nums = []
        for idx, tok in enumerate(tokens):
            if not tok.lstrip("-").isdigit():
                self._set_entry_state(entry_widget, err_lbl,
                                      f"Vị trí {idx+1}: '{tok}' không phải số", error=True)
                return None
            n = int(tok)
            if n < NUM_MIN:
                self._set_entry_state(entry_widget, err_lbl,
                                      f"Vị trí {idx+1}: {n} < tối thiểu ({NUM_MIN})", error=True)
                return None
            if n > NUM_MAX:
                self._set_entry_state(entry_widget, err_lbl,
                                      f"Vị trí {idx+1}: {n} > tối đa ({NUM_MAX})", error=True)
                return None
            nums.append(n)
        seen = {}
        for idx, n in enumerate(nums):
            if n in seen:
                self._set_entry_state(entry_widget, err_lbl,
                                      f"Số {n} bị trùng (vị trí {seen[n]+1} và {idx+1})", error=True)
                return None
            seen[n] = idx
        if sorted(nums) != list(range(9)):
            missing = sorted(set(range(9)) - set(nums))
            self._set_entry_state(entry_widget, err_lbl, f"Thiếu các số: {missing}", error=True)
            return None
        self._set_entry_state(entry_widget, err_lbl, "", error=False)
        return [nums[i*3:(i+1)*3] for i in range(3)]

    def _set_entry_state(self, entry_widget, err_lbl, msg, error=True):
        color = ACCENT if error else ENTRY_OK
        entry_widget.config(highlightbackground=color, highlightcolor=color)
        err_lbl.config(text=msg)

    def _make_button(self, parent, text, color, cmd):
        return tk.Button(parent, text=text,
                         font=("Courier New", 8, "bold"),
                         bg=color, fg=TEXT_LIGHT,
                         activebackground=ACCENT, activeforeground=TEXT_LIGHT,
                         relief="flat", padx=6, pady=6,
                         cursor="hand2", command=cmd)

    def draw_grid(self, state, goal_state=None, highlight=None):
        self.canvas.delete("all")
        for r in range(3):
            for c in range(3):
                val = state[r][c]
                x = GRID_PAD + c * (TILE_SIZE + GRID_PAD)
                y = GRID_PAD + r * (TILE_SIZE + GRID_PAD)
                if val == 0:
                    self.canvas.create_rectangle(x, y, x+TILE_SIZE, y+TILE_SIZE,
                                                 fill=TILE_BG, outline=SURFACE, width=2)
                    continue
                if goal_state and state == goal_state:
                    color = TILE_GOAL
                elif highlight == (r, c):
                    color = ACCENT
                else:
                    color = TILE_ACTIVE
                self._rounded_rect(x, y, x+TILE_SIZE, y+TILE_SIZE, TILE_RADIUS, color)
                self.canvas.create_text(x + TILE_SIZE // 2, y + TILE_SIZE // 2,
                                        text=str(val),
                                        font=("Courier New", 24, "bold"),
                                        fill=TEXT_LIGHT)

    def _rounded_rect(self, x1, y1, x2, y2, r, color):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        self.canvas.create_polygon(pts, smooth=True, fill=color, outline="")

    def set_stat(self, key, value):
        lbl = getattr(self, f"_stat_{key}", None)
        if lbl:
            lbl.config(text=str(value))

    def set_buttons(self, running: bool):
        if running:
            self.btn_start.config(state="normal")
            self.btn_random.config(state="normal")
            self.btn_stop.config(state="normal", text="Dừng", bg=BTN_STOP)
            self._is_paused = False
        else:
            self.btn_start.config(state="normal")
            self.btn_random.config(state="normal")
            self.btn_stop.config(state="disabled", text="Dừng", bg=BTN_STOP)
            self._is_paused = False

    def get_delay_ms(self):
        return self._step_delay_ms

    def get_algorithm(self):
        return self._algo_var.get()

    def show_toast(self, msg, ok=False):
        if self._toast_after:
            self.after_cancel(self._toast_after)
        self._toast.config(text=f"  {msg}  ", bg=TOAST_OK if ok else TOAST_ERR)
        self._toast.pack(fill="x", pady=(4, 0), after=self.canvas)
        self._toast_after = self.after(3000, self._hide_toast)

    def _hide_toast(self):
        self._toast.pack_forget()
        self._toast_after = None

    def refresh_input_grids(self, initial_state, goal_state):
        flat_i = " ".join(str(x) for row in initial_state for x in row)
        flat_g = " ".join(str(x) for row in goal_state     for x in row)
        self._initial_var.set(flat_i)
        self._goal_var.set(flat_g)
        self._last_valid_initial = flat_i
        self._last_valid_goal    = flat_g
        for entry in (self._initial_entry, self._goal_entry):
            if entry:
                entry.config(fg=TEXT_LIGHT, highlightbackground=ENTRY_OK, highlightcolor=ENTRY_OK)
        for lbl in (self._initial_err_lbl, self._goal_err_lbl):
            if lbl:
                lbl.config(text="")

    def set_pause_mode(self, paused: bool):
        self._is_paused = paused
        if paused:
            self.btn_stop.config(text="Tiếp tục", bg=BTN_START)
        else:
            self.btn_stop.config(text="Dừng", bg=BTN_STOP)

    def _on_speed_change(self, _=None):
        raw = self._speed_var.get()
        self._step_delay_ms = 1600 - raw
        self._speed_label.config(text=f"{self._step_delay_ms}ms")