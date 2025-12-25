# src/gui/ui_board.py
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageFilter

from utils.utils import COORDS, WHITE, BLACK, EMPTY, ADJACENT
from game.game import GameState
from game.ai import AIPlayer

RADIUS = 14  # logical radius for pieces

# background around the board
BG = "#24130F"
POINT_BG = "#F3E3C7"
HIGHLIGHT = "#FFD65C"    # golden highlight / glow

# paths relative to project root (you run from project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "resources", "imgs")

WOOD_TEXTURE = os.path.join(IMG_DIR, "premium_deep_mahogany.jpg")
GOLD_TEXTURE = os.path.join(IMG_DIR, "gold-piece-texture.jpg")
EBONY_TEXTURE = os.path.join(IMG_DIR, "ebony-glossy-texture.jpg")


class BoardFrame(tk.Frame):
    def __init__(
        self,
        master,
        mode='pvp',
        back_callback=None,
        undo_limit=5,
        ai_level=None,
        max_win_moves=0
    ):
        super().__init__(master, bg=BG)
        self.mode = mode
        self.back_callback = back_callback
        self.state = GameState()

        # settings
        self.ai_level = ai_level or "N/A"
        self.max_win_moves = int(max_win_moves or 0)
        self.undo_limit = max(0, int(undo_limit))

        # AI instance
        self.ai = None
        if mode == 'ai':
            level = (ai_level or "Medium").lower()
            if level == 'easy':
                max_time = 0.6
            elif level == 'hard':
                max_time = 4.0
            else:
                max_time = 1.8
            self.ai = AIPlayer(color=BLACK, max_time=max_time, max_win_moves=self.max_win_moves)

        # interaction state
        self.selected = None
        self.pending_capture = False
        self.last_move = None
        self.undo_stack = []
        self.ai_thread = None
        self.ai_running = False
        self.win_label = None
        self.game_over_handled = False

        # textures
        self.board_bg_img = None
        self.board_bg_id = None
        self.gold_piece_img = None
        self.ebony_piece_img = None

        # animation / hover state
        self.animating = False
        self.hover_pos = None
        self.hover_glow_items = []
        self.glow_items = []

        self.build_ui()
        self.load_textures()
        self.draw_board()
        self.update_status()
        

    # ---------- UI build ----------
    def build_ui(self):
        # ---------------------------------------------------------
        # CARVED WOODEN HEADER BAR
        # ---------------------------------------------------------
        # header = tk.Frame(self, bg=BG)
        # header.pack(side='top', fill='x')

        # # carved wood texture strip
        # try:
        #     header_img_raw = Image.open(WOOD_TEXTURE).convert("RGB")
        #     header_img_raw = header_img_raw.resize((5000, 40), Image.LANCZOS)
        #     header_img_raw = ImageEnhance.Brightness(header_img_raw).enhance(0.85)
        #     self.header_img = ImageTk.PhotoImage(header_img_raw)
        #     tk.Label(header, image=self.header_img, bd=0).pack(fill='x')
        # except Exception:
        #     tk.Label(header, bg="#5A2E1E", height=2).pack(fill='x')

        # TOP BAR (1st rows now)
        top = tk.Frame(self, bg=BG)
        top.pack(side='top', fill='x', pady=(4, 0))
        # ---------------- Row 1: Icon Buttons ----------------
        row1 = tk.Frame(top, bg=BG, height=40)
        row1.pack(fill='x', pady=(6, 0))
        row1.pack_propagate(False)

        # load icons
        def load_icon(name):
            path = os.path.join(IMG_DIR, name)
            img = Image.open(path).convert("RGBA")
            img = img.resize((18, 18), Image.LANCZOS)
            return ImageTk.PhotoImage(img)

        self.icon_undo = load_icon("undo.png")
        self.icon_save = load_icon("save.png")
        self.icon_load = load_icon("load.png")
        self.icon_back = load_icon("back.png")

        # hover effect
        def add_hover(btn, base_color, hover_color):
            def on_enter(_):
                btn.config(bg=hover_color)
            def on_leave(_):
                btn.config(bg=base_color)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        def make_icon_button(parent, text, icon, color, hover, cmd):
            btn = tk.Button(
                parent,
                text="  " + text,
                image=icon,
                compound="left",
                command=cmd,
                bg=color,
                fg="#24130F",
                activebackground=hover,
                activeforeground="#24130F",
                bd=0,
                font=("Segoe UI", 9, "bold"),
                width=90,
                height=28,
                anchor="w",
                padx=6
            )
            add_hover(btn, color, hover)
            return btn

        btn_back = make_icon_button(
        row1, "Back", self.icon_back,
        "#E8EAF6", "#F2F4FF",
        self.on_back
        )
        btn_back.pack(side='left', padx=6, pady=4)

        btn_save = make_icon_button(
            row1, "Save", self.icon_save,
            "#D1E8E2", "#E1F2F0",
            self.on_save
        )
        btn_save.pack(side='left', padx=6, pady=4)

        btn_load = make_icon_button(
            row1, "Load", self.icon_load,
            "#F0C2C2", "#F7D4D4",
            self.on_load
        )
        btn_load.pack(side='left', padx=6, pady=4)

        self.undo_btn = make_icon_button(
            row1, "Undo", self.icon_undo,
            "#F6D6AD", "#FFE2B8",
            self.on_undo
        )
        self.undo_btn.pack(side='left', padx=6, pady=4)

        # ---------------- Gold Separator ----------------
        tk.Frame(top, bg="#FFD65C", height=2).pack(fill='x', pady=(2, 2))

        # ---------------- Row 2: AI info + Undo counter ----------------
        row2 = tk.Frame(top, bg=BG, height=26)
        row2.pack(fill='x')
        row2.pack_propagate(False)
        self.ai_level_label = tk.Label(
            row2,
            text=f"AI: {self.ai_level} | Max win: {self.max_win_moves or '∞'}",
            bg=BG, fg="#F7E7D0", font=("Segoe UI", 10)
        )
        self.ai_level_label.pack(side='left', padx=12)

        self.undo_label = tk.Label(
            row2, text=f"Undos left: {self.undo_limit}",
            bg=BG, fg="#F7E7D0", font=("Segoe UI", 10)
        )
        self.undo_label.pack(side='right', padx=12)

        # ---------------- Gold Separator ----------------
        tk.Frame(top, bg="#FFD65C", height=2).pack(fill='x', pady=(2, 2))

        # ---------------- Row 3: Status text ----------------
        row3 = tk.Frame(top, bg=BG, height=28)
        row3.pack(fill='x')
        row3.pack_propagate(False)

        self.status_label = tk.Label(
            row3, text="", font=("Segoe UI", 11),
            bg=BG, fg="#F7E7D0"
        )
        self.status_label.pack(side='left', padx=12)

        # ---------------------------------------------------------
        # CANVAS AREA (board)
        # ---------------------------------------------------------
        canvas_frame = tk.Frame(self, bg=BG)
        canvas_frame.pack(pady=10)

        self.canvas = tk.Canvas(
            canvas_frame, width=420, height=460,
            bg=BG, bd=0, highlightthickness=0
        )
        self.canvas.pack(padx=12, pady=6)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Leave>", self.on_mouse_leave)

        # ---------------------------------------------------------
        # BOTTOM BAR (AI thinking indicator)
        # ---------------------------------------------------------
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(side='bottom', fill='x', pady=(6, 12))

        self.ai_label = tk.Label(
            bottom, text="", bg=BG, fg="#F7E7D0",
            font=("Segoe UI", 10, "italic")
        )
        self.ai_label.pack(side='left', padx=12)

        self.progress = ttk.Progressbar(bottom, mode='indeterminate', length=180)
        self.progress.pack(side='right', padx=12)
        self.progress.pack_forget()

    # ---------- Texture loading ----------
    def load_textures(self):
        try:
            # ---- helper: circular crop + gloss + shadow (subtle) ----
            def make_premium_piece(img_path, size):
                img = Image.open(img_path).convert("RGBA")
                img = img.resize((size, size), Image.LANCZOS)

                # circular mask
                mask = Image.new("L", (size, size), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, size, size), fill=255)
                img.putalpha(mask)

                # subtle gloss: light gradient at top-left
                gloss = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                gdraw = ImageDraw.Draw(gloss)
                # soft arc / ellipse
                gdraw.ellipse(
                    (size * 0.1, size * 0.05, size * 0.9, size * 0.7),
                    fill=(255, 255, 255, 40)
                )
                img = Image.alpha_composite(img, gloss)

                # drop shadow: small offset, soft
                shadow_size = size + 6
                shadow = Image.new("RGBA", (shadow_size, shadow_size), (0, 0, 0, 0))
                sdraw = ImageDraw.Draw(shadow)
                sx = 3
                sy = 3
                sdraw.ellipse(
                    (sx, sy, sx + size, sy + size),
                    fill=(0, 0, 0, 70)
                )
                shadow = shadow.filter(ImageFilter.GaussianBlur(2))

                # composite shadow + piece centered
                combined = Image.new("RGBA", (shadow_size, shadow_size), (0, 0, 0, 0))
                combined.alpha_composite(shadow, (0, 0))
                combined.alpha_composite(img, (3, 3))

                return combined

            # --- load board texture ---
            board_img = Image.open(WOOD_TEXTURE).convert("RGB")
            board_img = board_img.resize((420, 460), Image.LANCZOS)
            # subtle darkening for mood
            board_img = ImageEnhance.Brightness(board_img).enhance(0.95)
            self.board_bg_img = ImageTk.PhotoImage(board_img)

            # piece size (texture)
            piece_tex_size = RADIUS * 2 + 10

            # --- gold piece ---
            gold_img = make_premium_piece(GOLD_TEXTURE, piece_tex_size)
            self.gold_piece_img = ImageTk.PhotoImage(gold_img)

            # --- ebony piece ---
            ebony_img = make_premium_piece(EBONY_TEXTURE, piece_tex_size)
            self.ebony_piece_img = ImageTk.PhotoImage(ebony_img)

        except Exception as e:
            messagebox.showerror("Texture Error", f"Error loading textures: {e}")
            self.board_bg_img = None
            self.gold_piece_img = None
            self.ebony_piece_img = None

    # ---------- Undo / Save / Load ----------
    def push_undo(self):
        self.undo_stack.append(self.state.to_json())
        if len(self.undo_stack) > 200:
            self.undo_stack.pop(0)
        if self.undo_limit > 0:
            while len(self.undo_stack) > self.undo_limit:
                self.undo_stack.pop(0)
        self.update_undo_label()

    def on_undo(self):
        if not self.undo_stack:
            messagebox.showinfo("Undo", "No undos available")
            return
        last_json = self.undo_stack.pop()
        try:
            self.state = GameState.from_json(last_json)
            self.selected = None
            self.pending_capture = False
            self.last_move = None
            self.draw_board()
            self.update_status()
            self.update_undo_label()
        except Exception as e:
            messagebox.showerror("Undo Error", str(e))

    def update_undo_label(self):
        if self.undo_limit == 0:
            text = "Undos left: ∞"
        else:
            used = len(self.undo_stack)
            left = max(0, self.undo_limit - used)
            text = f"Undos left: {left}"
        self.undo_label.config(text=text)

    def on_save(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not path:
            return
        try:
            with open(path, 'w') as f:
                f.write(self.state.to_json())
            messagebox.showinfo("Save", "Game saved")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def on_load(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if not path:
            return
        try:
            with open(path, 'r') as f:
                text = f.read()
            loaded = GameState.from_json(text)
            self.push_undo()
            self.state = loaded
            self.selected = None
            self.pending_capture = False
            self.last_move = None
            self.draw_board()
            self.update_status()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def on_back(self):
        if self.back_callback:
            if self.ai_running:
                messagebox.showinfo("Please wait", "AI is thinking. Please wait a moment.")
                return
            self.back_callback()

    # ---------- Drawing ----------
    def draw_board(self):
        c = self.canvas
        c.delete('all')
        self.hover_glow_items.clear()
        self.glow_items.clear()

        # board background
        if self.board_bg_img is not None:
            self.board_bg_id = c.create_image(0, 0, anchor='nw', image=self.board_bg_img)
        else:
            c.create_rectangle(0, 0, 420, 460, fill="#5A2E1E", outline="#2C150E")

        # carved frame
        c.create_rectangle(8, 8, 412, 452, outline="#2D1208", width=6)
        c.create_rectangle(14, 14, 406, 446, outline="#C98F5D", width=2)

        # connections
        drawn = set()
        line_color = "#3A1F0F"
        inner_highlight = "#D9A96C"
        line_width = 5

        for frm, neighbors in ADJACENT.items():
            x1, y1 = COORDS[frm]
            for to in neighbors:
                pair = tuple(sorted((frm, to)))
                if pair in drawn:
                    continue
                drawn.add(pair)
                x2, y2 = COORDS[to]
                c.create_line(x1, y1, x2, y2, fill=line_color, width=line_width, capstyle='round')
                c.create_line(
                    x1 + 1, y1 + 1, x2 + 1, y2 + 1,
                    fill=inner_highlight, width=2, capstyle='round'
                )

        # inlaid points
        for idx, (x, y) in COORDS.items():
            c.create_oval(
                x - 18, y - 18, x + 18, y + 18,
                fill=POINT_BG, outline="#8C5A37", width=2
            )

        # pieces
        for idx, (x, y) in COORDS.items():
            self.draw_point(idx, x, y)

        # re-apply hover glow if any
        if self.hover_pos is not None:
            self.start_hover_glow(self.hover_pos)

    def draw_point(self, idx, x, y):
        c = self.canvas
        state = self.state.board[idx]
        piece_size = RADIUS * 2 + 10

        if state == WHITE:
            if self.gold_piece_img is not None:
                c.create_image(x, y, image=self.gold_piece_img, tags=f'pt{idx}')
            else:
                c.create_oval(
                    x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS,
                    fill="#FDF5E6", outline="#C9B58B", width=2, tags=f'pt{idx}'
                )
        elif state == BLACK:
            if self.ebony_piece_img is not None:
                c.create_image(x, y, image=self.ebony_piece_img, tags=f'pt{idx}')
            else:
                c.create_oval(
                    x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS,
                    fill="#1A0F0A", outline="#3D2A20", width=2, tags=f'pt{idx}'
                )

        # pressed-in effect when selected
        if self.selected == idx:
            c.create_oval(
                x - RADIUS - 4, y - RADIUS - 4,
                x + RADIUS + 4, y + RADIUS + 4,
                outline=HIGHLIGHT, width=3
            )

    # ---------- Hover handling ----------
    def on_mouse_move(self, event):
        # find nearest point in range and animate hover glow
        closest = None
        best_dist2 = (RADIUS + 14) ** 2
        for idx, (x, y) in COORDS.items():
            dx = event.x - x
            dy = event.y - y
            d2 = dx * dx + dy * dy
            if d2 <= best_dist2:
                best_dist2 = d2
                closest = idx

        if closest != self.hover_pos:
            self.hover_pos = closest
            self.clear_hover_glow()
            if closest is not None:
                self.start_hover_glow(closest)

    def on_mouse_leave(self, _event):
        self.hover_pos = None
        self.clear_hover_glow()

    def clear_hover_glow(self):
        for it in self.hover_glow_items:
            self.canvas.delete(it)
        self.hover_glow_items.clear()

    def start_hover_glow(self, idx):
        if idx is None:
            return
        c = self.canvas
        self.clear_hover_glow()
        x, y = COORDS[idx]
        steps = 12

        def frame(i):
            if self.hover_pos != idx:
                self.clear_hover_glow()
                return
            if i > steps:
                self.clear_hover_glow()
                self.after(40, lambda: frame(1))  # loop
                return
            self.clear_hover_glow()
            t = i / steps
            r = int(RADIUS + 6 + 6 * t)
            alpha = int(40 + 60 * (1 - t))
            color = f"#{255:02x}{214:02x}{92:02x}"
            # Tkinter doesn't support alpha; we simulate by width + color intensity
            it = c.create_oval(
                x - r, y - r, x + r, y + r,
                outline=color, width=2
            )
            self.hover_glow_items.append(it)
            self.after(40, lambda: frame(i + 1))

        frame(1)

    # ---------- Input handling ----------
    def on_click(self, event):
        if self.ai_running or self.animating:
            return
        clicked = None
        for idx, (x, y) in COORDS.items():
            dx = event.x - x
            dy = event.y - y
            if dx * dx + dy * dy <= (RADIUS + 8) ** 2:
                clicked = idx
                break
        if clicked is None:
            return

        if self.pending_capture:
            if self.state.board[clicked] == -self.state.current:
                capturable = self.state.can_capture_positions()
                if clicked in capturable:
                    self.push_undo()
                    self.animate_capture(clicked)
                    self.state = self.state.apply_move(self.last_move, remove_pos=clicked)
                    self.pending_capture = False
                    self.selected = None
                    self.draw_board()
                    self.update_status()
                    self.after_ai_if_needed()
                return
            return

        if self.state.phase == 'placing':
            if self.state.board[clicked] == EMPTY:
                move = ('place', clicked)
                forms_mill = self.state.last_move_forms_mill(move)
                if forms_mill:
                    self.push_undo()
                    self.last_move = move
                    self.pending_capture = True
                    self.state.board[clicked] = self.state.current
                    self.draw_board()
                    self.update_status(capturing=True)
                    self.animate_glow([clicked])
                else:
                    self.push_undo()
                    self.state = self.state.apply_move(move, remove_pos=None)
                    self.draw_board()
                    self.update_status()
                    self.animate_glow([clicked])
                    self.after_ai_if_needed()
            return

        if self.state.phase == 'moving':
            if self.selected is None:
                if self.state.board[clicked] == self.state.current:
                    self.selected = clicked
                    self.draw_board()
                    return
            else:
                if self.state.board[clicked] == EMPTY:
                    move = ('move', self.selected, clicked)
                    if self.is_legal_move(move):
                        forms_mill = self.state.last_move_forms_mill(move)
                        frm = self.selected
                        to = clicked
                        if forms_mill:
                            self.push_undo()
                            self.last_move = move
                            self.animate_move(frm, to, self.state.current)
                            self.state.board[frm] = EMPTY
                            self.state.board[to] = self.state.current
                            self.pending_capture = True
                            self.selected = None
                            self.draw_board()
                            self.update_status(capturing=True)
                            self.animate_glow([to])
                        else:
                            self.push_undo()
                            self.animate_move(frm, to, self.state.current)
                            self.state = self.state.apply_move(move, remove_pos=None)
                            self.selected = None
                            self.draw_board()
                            self.update_status()
                            self.animate_glow([to])
                            self.after_ai_if_needed()
                    else:
                        self.selected = None
                        self.draw_board()
                else:
                    if self.state.board[clicked] == self.state.current:
                        self.selected = clicked
                        self.draw_board()

    def is_legal_move(self, move):
        if move[0] != 'move':
            return False
        frm, to = move[1], move[2]
        if self.state.board[frm] != self.state.current:
            return False
        if self.state.board[to] != EMPTY:
            return False
        if self.state.pieces_count(self.state.current) == 3:
            return True
        return to in ADJACENT[frm]

    # ---------- Status and AI ----------
    def update_status(self, capturing=False):
        over, winner = self.state.is_game_over()

        if over and not self.game_over_handled:
            self.game_over_handled = True

            winner_text = "White" if winner == WHITE else "Black"
            fancy = f"🎉 {winner_text} Wins the Match! 🎉"

            # Show animated message in the center
            self.show_win_animation(fancy)

            # Stop AI indicator
            self.ai_label.config(text="")
            try:
                self.progress.stop()
            except Exception:
                pass
            self.progress.pack_forget()

            # Return to start screen after 5 seconds
            self.after(5000, self.back_callback)
            return

        # Normal status update
        if capturing:
            self.status_label.config(
                text=f"{'White' if self.state.current == WHITE else 'Black'} formed a mill. Select opponent piece to capture."
            )
            return

        text = (
            f"Turn: {'White' if self.state.current == WHITE else 'Black'}"
            f" | Phase: {self.state.phase}"
            f" | White: {self.state.pieces_count(WHITE)}"
            f" Black: {self.state.pieces_count(BLACK)}"
        )
        self.status_label.config(text=text)
        self.update_undo_label()

    def after_ai_if_needed(self):
        if self.mode == 'ai' and self.state.current == self.ai.color:
            self.update_status()
            self.push_undo()
            self.start_ai_thread()

    def start_ai_thread(self):
        if self.ai_running:
            return
        self.ai_running = True
        self.progress.pack(side='right', padx=12)
        self.progress.start(10)
        self.ai_label.config(text=f"AI ({self.ai_level}) is thinking...")
        self.ai_thread = threading.Thread(target=self.run_ai_thread, daemon=True)
        self.ai_thread.start()

    def run_ai_thread(self):
        try:
            choice = self.ai.choose_move(self.state)
            self.after(10, lambda: self.finish_ai_move(choice))
        except Exception:
            self.after(10, lambda: self.finish_ai_move(None))

    def finish_ai_move(self, choice):
        try:
            self.progress.stop()
        except Exception:
            pass
        self.progress.pack_forget()
        self.ai_label.config(text="")
        self.ai_running = False
        if choice is None:
            self.update_status()
            return
        move, cap = choice
        if move[0] == 'move':
            frm, to = move[1], move[2]
            self.animate_move(frm, to, self.ai.color)
        self.state = self.state.apply_move(move, remove_pos=cap)
        self.draw_board()
        if move[0] == 'move':
            self.animate_glow([move[2]])
        if cap is not None:
            self.animate_capture(cap)
        self.update_status()

    # ---------- Animations ----------
    def animate_move(self, frm, to, color):
        if frm == to or self.animating:
            return
        self.animating = True
        c = self.canvas
        x1, y1 = COORDS[frm]
        x2, y2 = COORDS[to]

        if color == WHITE and self.gold_piece_img is not None:
            img = self.gold_piece_img
            item = c.create_image(x1, y1, image=img)
        elif color == BLACK and self.ebony_piece_img is not None:
            img = self.ebony_piece_img
            item = c.create_image(x1, y1, image=img)
        else:
            fill = "#FDF5E6" if color == WHITE else "#1A0F0A"
            outline = "#C9B58B" if color == WHITE else "#3D2A20"
            item = c.create_oval(
                x1 - RADIUS, y1 - RADIUS, x1 + RADIUS, y1 + RADIUS,
                fill=fill, outline=outline, width=2
            )

        steps = 10
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps

        def step(i):
            if i > steps:
                c.delete(item)
                self.animating = False
                return
            c.move(item, dx, dy)
            self.after(20, lambda: step(i + 1))

        step(1)

    def animate_capture(self, pos):
        c = self.canvas
        x, y = COORDS[pos]
        r = RADIUS + 6
        steps = 6

        def step(i):
            if i > steps:
                return
            alpha = 1.0 - i / steps
            width = 2 + (steps - i)
            color = "#FFB3B3"
            c.create_oval(
                x - r, y - r, x + r, y + r,
                outline=color, width=width
            )
            self.after(40, lambda: step(i + 1))

        step(1)

    def animate_glow(self, positions):
        c = self.canvas
        for it in self.glow_items:
            c.delete(it)
        self.glow_items.clear()
        steps = 8

        def frame(i):
            if i > steps:
                for it in self.glow_items:
                    c.delete(it)
                self.glow_items.clear()
                return
            for pos in positions:
                x, y = COORDS[pos]
                factor = 1.0 + 0.4 * (i / steps)
                r = int(RADIUS * factor) + 4
                col = HIGHLIGHT
                it = c.create_oval(
                    x - r, y - r, x + r, y + r,
                    outline=col, width=2
                )
                self.glow_items.append(it)
            self.after(60, lambda: frame(i + 1))

        frame(1)
    
    def show_win_animation(self, text):
        # Create label if not created
        if self.win_label is None:
            self.win_label = tk.Label(
                self,
                text=text,
                font=("Segoe UI", 26, "bold"),
                fg="#FFD65C",
                bg=BG
            )
            # Center it
            self.win_label.place(relx=0.5, rely=0.5, anchor="center")

        # Animation: fade-in effect by gradually increasing color intensity
        steps = 20
        def animate(i):
            if i > steps:
                return
            # fade from dark gold to bright gold
            ratio = i / steps
            r = int(255 * ratio)
            g = int(214 * ratio)
            b = int(92 * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.win_label.config(fg=color)
            self.after(40, lambda: animate(i + 1))

        animate(0)