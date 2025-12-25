# src/game/game.py
from copy import deepcopy
from utils.utils import ADJACENT, MILLS, WHITE, BLACK, EMPTY
import json

class GameState:
    def __init__(self):
        self.board = [EMPTY] * 24

        # placing phase counters
        self.placed_white = 0
        self.placed_black = 0
        self.white_unplaced = 9
        self.black_unplaced = 9

        # captures
        self.captured_white = 0
        self.captured_black = 0

        # turn + phase
        self.current = WHITE
        self.phase = 'placing'
        self.total_per_side = 9

        # AI endgame counter
        self.ai_endgame_moves = 0

    def clone(self):
        return deepcopy(self)

    def pieces_count(self, color):
        return sum(1 for p in self.board if p == color)

    def other(self, color):
        return -color

    def in_mill(self, pos, board=None):
        if board is None:
            board = self.board
        color = board[pos]
        if color == EMPTY:
            return False
        for a, b, c in MILLS:
            if pos in (a, b, c) and board[a] == board[b] == board[c] == color:
                return True
        return False

    def mills_formed_by_move(self, pos, color, board=None):
        if board is None:
            board = self.board
        formed = []
        for a, b, c in MILLS:
            if pos in (a, b, c) and board[a] == board[b] == board[c] == color:
                formed.append((a, b, c))
        return formed

    # ---------------------------------------------------------
    # NORMAL legal moves (for the CURRENT player)
    # ---------------------------------------------------------
    def legal_moves(self):
        return self.legal_moves_for(self.current)

    # ---------------------------------------------------------
    # LEGAL MOVES FOR ANY COLOR (used by AI)
    # ---------------------------------------------------------
    def legal_moves_for(self, color):
        moves = []

        # placing phase
        if self.phase == 'placing':
            for i in range(24):
                if self.board[i] == EMPTY:
                    moves.append(('place', i))
            return moves

        # moving phase
        my_positions = [i for i, p in enumerate(self.board) if p == color]

        # flying
        if self.pieces_count(color) == 3:
            for frm in my_positions:
                for to in range(24):
                    if self.board[to] == EMPTY:
                        moves.append(('move', frm, to))
            return moves

        # normal move
        for frm in my_positions:
            for to in ADJACENT[frm]:
                if self.board[to] == EMPTY:
                    moves.append(('move', frm, to))

        return moves

    # ---------------------------------------------------------
    # APPLY MOVE
    # ---------------------------------------------------------
    def apply_move(self, move, remove_pos=None):
        s = self.clone()

        if move[0] == 'place':
            pos = move[1]
            s.board[pos] = s.current

            if s.current == WHITE:
                s.placed_white += 1
                s.white_unplaced -= 1
            else:
                s.placed_black += 1
                s.black_unplaced -= 1

            if s.placed_white + s.placed_black >= 18:
                s.phase = 'moving'

        elif move[0] == 'move':
            frm, to = move[1], move[2]
            s.board[frm] = EMPTY
            s.board[to] = s.current

        # capture
        if remove_pos is not None:
            if s.board[remove_pos] == -s.current:
                s.board[remove_pos] = EMPTY
                if s.current == WHITE:
                    s.captured_black += 1
                else:
                    s.captured_white += 1

        # switch turn
        s.current = -s.current

        # ensure phase transition
        if s.phase == 'placing' and s.placed_white + s.placed_black >= 18:
            s.phase = 'moving'

        return s

    def can_capture_positions(self):
        opp = -self.current
        positions = [i for i, p in enumerate(self.board) if p == opp and not self.in_mill(i)]
        if positions:
            return positions
        return [i for i, p in enumerate(self.board) if p == opp]

    def is_game_over(self):
        # During placing phase, nobody can lose by piece count
        if self.phase == 'placing':
            return False, None

        # After placing phase, piece count matters
        for color in (WHITE, BLACK):
            if self.pieces_count(color) < 3:
                return True, -color

        # In moving phase, check if current player is blocked
        if self.phase == 'moving':
            if not self.legal_moves():
                return True, -self.current

        return False, None

    def last_move_forms_mill(self, move):
        temp = self.clone()
        if move[0] == 'place':
            pos = move[1]
            temp.board[pos] = temp.current
            return bool(temp.mills_formed_by_move(pos, temp.current, temp.board))
        elif move[0] == 'move':
            frm, to = move[1], move[2]
            temp.board[frm] = EMPTY
            temp.board[to] = temp.current
            return bool(temp.mills_formed_by_move(to, temp.current, temp.board))
        return False

    # ---------------------------------------------------------
    # SAVE / LOAD
    # ---------------------------------------------------------
    def to_json(self):
        data = {
            "board": self.board,
            "current": self.current,
            "phase": self.phase,
            "white_unplaced": self.white_unplaced,
            "black_unplaced": self.black_unplaced,
            "placed_white": self.placed_white,
            "placed_black": self.placed_black,
            "captured_white": self.captured_white,
            "captured_black": self.captured_black,
            "total_per_side": self.total_per_side,
            "ai_endgame_moves": self.ai_endgame_moves
        }
        return json.dumps(data)

    @staticmethod
    def from_json(text):
        data = json.loads(text)
        s = GameState()

        s.board = data.get("board", [EMPTY] * 24)
        s.current = data.get("current", WHITE)
        s.phase = data.get("phase", "placing")

        s.white_unplaced = data.get("white_unplaced", 9)
        s.black_unplaced = data.get("black_unplaced", 9)

        s.placed_white = data.get("placed_white", 0)
        s.placed_black = data.get("placed_black", 0)

        s.captured_white = data.get("captured_white", 0)
        s.captured_black = data.get("captured_black", 0)

        s.total_per_side = data.get("total_per_side", 9)

        s.ai_endgame_moves = data.get("ai_endgame_moves", 0)

        return s