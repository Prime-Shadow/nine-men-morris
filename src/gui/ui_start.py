# src/gui/ui_start.py
import os
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk, ImageEnhance

# Paths relative to project root (you run from project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "resources", "imgs")

WOOD_TEXTURE = os.path.join(IMG_DIR, "premium_deep_mahogany.jpg")

BG = "#24130F"       # main dark background
PANEL_BG = "#3A1F0F" # panel background
GOLD = "#FFD65C"
IVORY = "#F7E7D0"


class StartFrame(tk.Frame):
    def __init__(self, master, start_callback):
        super().__init__(master, bg=BG)
        self.start_callback = start_callback

        self.bg_img = None
        self.load_background()
        self.build_ui()

    # ---------------------------------------------------------
    # Load mahogany background texture
    # ---------------------------------------------------------
    def load_background(self):
        try:
            img = Image.open(WOOD_TEXTURE).convert("RGB")
            # size doesn't have to be exact; it will be stretched
            img = img.resize((900, 700), Image.LANCZOS)
            img = ImageEnhance.Brightness(img).enhance(0.92)
            self.bg_img = ImageTk.PhotoImage(img)
        except Exception:
            self.bg_img = None

    # ---------------------------------------------------------
    # Build UI
    # ---------------------------------------------------------
    def build_ui(self):
        # Background image
        if self.bg_img:
            bg_label = tk.Label(self, image=self.bg_img, bd=0)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Main container (use same BG as frame)
        container = tk.Frame(self, bg=BG)
        container.pack(expand=True)

        # Title
        title = tk.Label(
            container,
            text="Nine Men's Morris",
            font=("Segoe UI", 32, "bold"),
            fg=GOLD,
            bg=BG
        )
        title.pack(pady=(40, 10))

        subtitle = tk.Label(
            container,
            text="Premium Carved Edition",
            font=("Segoe UI", 16, "italic"),
            fg=IVORY,
            bg=BG
        )
        subtitle.pack(pady=(0, 40))

        # Settings panel
        panel = tk.Frame(container, bg=PANEL_BG, bd=3, relief="ridge")
        panel.pack(pady=20)

        # Undo limit
        lbl_undo = tk.Label(
            panel, text="Max undos:",
            bg=PANEL_BG, fg=IVORY,
            font=("Segoe UI", 11)
        )
        lbl_undo.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.undo_spin = tk.Spinbox(
            panel, from_=0, to=100, width=6,
            font=("Segoe UI", 11),
            bg="#FDF5E6",
            fg="#24130F",
            insertbackground="#24130F"
        )
        self.undo_spin.delete(0, "end")
        self.undo_spin.insert(0, "5")
        self.undo_spin.grid(row=0, column=1, padx=10, pady=10)

        # AI level
        lbl_ai = tk.Label(
            panel, text="AI level:",
            bg=PANEL_BG, fg=IVORY,
            font=("Segoe UI", 11)
        )
        lbl_ai.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.ai_level_var = tk.StringVar(value="Medium")
        self.ai_level_combo = ttk.Combobox(
            panel, textvariable=self.ai_level_var,
            state="readonly",
            values=["Easy", "Medium", "Hard"],
            width=10,
            font=("Segoe UI", 11)
        )
        self.ai_level_combo.grid(row=1, column=1, padx=10, pady=10)

        # Max moves to win
        lbl_maxwin = tk.Label(
            panel, text="Max moves to win:",
            bg=PANEL_BG, fg=IVORY,
            font=("Segoe UI", 11)
        )
        lbl_maxwin.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.maxwin_spin = tk.Spinbox(
            panel, from_=0, to=200, width=6,
            font=("Segoe UI", 11),
            bg="#FDF5E6",
            fg="#24130F",
            insertbackground="#24130F"
        )
        self.maxwin_spin.delete(0, "end")
        self.maxwin_spin.insert(0, "20")
        self.maxwin_spin.grid(row=2, column=1, padx=10, pady=10)

        # Buttons
        btn_frame = tk.Frame(container, bg=BG)
        btn_frame.pack(pady=40)

        def make_button(text, color, command):
            return tk.Button(
                btn_frame,
                text=text,
                command=command,
                font=("Segoe UI", 14, "bold"),
                fg="#24130F",
                bg=color,
                activebackground=GOLD,
                activeforeground="#24130F",
                bd=0,
                width=18,
                height=1
            )

        btn_ai = make_button("Play vs AI", GOLD, lambda: self.start_with_settings("ai"))
        btn_pvp = make_button("Play vs Player", IVORY, lambda: self.start_with_settings("pvp"))
        btn_exit = make_button("Exit", "#E07A5F", self.master.quit)

        btn_ai.pack(pady=8)
        btn_pvp.pack(pady=8)
        btn_exit.pack(pady=8)

        # Footer
        footer = tk.Label(
            container,
            text=(
                "Make mills to capture opponent pieces.\n"
                "Win by reducing them to 2 pieces or blocking all moves."
            ),
            justify="center",
            bg=BG,
            fg=IVORY,
            font=("Segoe UI", 10)
        )
        footer.pack(pady=(20, 10))

    # ---------------------------------------------------------
    # Start game with selected settings
    # ---------------------------------------------------------
    def start_with_settings(self, mode):
        try:
            undo_limit = int(self.undo_spin.get())
        except Exception:
            undo_limit = 5

        ai_level = self.ai_level_var.get() if mode == "ai" else None

        try:
            max_win_moves = int(self.maxwin_spin.get())
        except Exception:
            max_win_moves = 20

        self.start_callback(mode, undo_limit, ai_level, max_win_moves)