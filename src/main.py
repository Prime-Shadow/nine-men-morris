# src/main.py
import tkinter as tk
from gui.ui_start import StartFrame
from gui.ui_board import BoardFrame

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mill — Nine Men's Morris")
        self.geometry("520x620")
        self.resizable(False, False)
        self.current_frame = None
        self.show_start()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    def show_start(self):
        self.clear_frame()
        self.current_frame = StartFrame(self, start_callback=self.start_game)
        self.current_frame.pack(fill='both', expand=True)

    def start_game(self, mode, undo_limit, ai_level=None, max_win_moves=0):
        self.clear_frame()
        self.current_frame = BoardFrame(self, mode=mode, back_callback=self.show_start,
                                        undo_limit=undo_limit, ai_level=ai_level, max_win_moves=max_win_moves)
        self.current_frame.game_over_handled = False
        self.current_frame.pack(fill='both', expand=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()