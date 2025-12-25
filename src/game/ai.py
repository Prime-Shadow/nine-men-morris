# src/game/ai.py
import math
import random
import time
from game.game import GameState
from utils.utils import WHITE, BLACK, EMPTY, MILLS


class AIPlayer:
    """
    Iterative deepening minimax with alpha-beta and mate-shortening preference.
    """

    def __init__(self, color=BLACK, max_time=1.8, max_win_moves=0):
        self.color = color
        self.max_time = float(max_time)
        self.max_win_moves = int(max_win_moves)
        self.start_time = 0
        self.transposition = {}

    # ======================================================================
    # PUBLIC: choose_move
    # ======================================================================
    def choose_move(self, state):
        """
        Returns (move, capture_pos)
        move is either:
            ('place', pos)
            ('move', frm, to)
        """

        # ---------------------------------------------------------
        # 1. NORMAL AI SEARCH (iterative deepening)
        # ---------------------------------------------------------
        result = self._search(state) if self.max_time > 0 else None

        if result is None:
            # fallback: random legal move for current player (AI turn)
            legal = state.legal_moves()
            if not legal:
                return None
            move = random.choice(legal)
            cap = None
        else:
            move, cap = result

        # ---------------------------------------------------------
        # 2. ENDGAME MAX-MOVES-TO-WIN RULE
        # ---------------------------------------------------------
        ai_pieces = state.pieces_count(self.color)
        opp_pieces = state.pieces_count(-self.color)

        if ai_pieces == 3 and opp_pieces in (3, 4) and self.max_win_moves > 0:
            # count only AI moves in this specific endgame pattern
            state.ai_endgame_moves += 1

            if state.ai_endgame_moves >= self.max_win_moves:
                # next move is random (but only if there are legal moves)
                legal = state.legal_moves()
                if legal:
                    move = random.choice(legal)
                    cap = None
                # reset counter after random move
                state.ai_endgame_moves = 0

        return move, cap

    # ======================================================================
    # PRIVATE: iterative deepening search
    # ======================================================================
    def _search(self, state):
        """
        Iterative deepening over _search_root until time runs out.
        Returns (move, cap) or None.
        """
        self.start_time = time.time()
        self.transposition.clear()

        best_choice = None
        best_mate = None
        depth = 1

        try:
            while True:
                score, choice, mate_dist = self._search_root(state, depth)
                if choice is not None:
                    best_choice = choice
                    best_mate = mate_dist
                depth += 1
        except TimeoutError:
            pass

        return best_choice

    # ======================================================================
    # ROOT SEARCH
    # ======================================================================
    def _search_root(self, state, depth):
        """
        Search from root for the current player (state.current).
        IMPORTANT: here we assume state.current == self.color.
        """
        moves = state.legal_moves()
        random.shuffle(moves)

        best_score = -math.inf
        best_choice = None
        best_mate = None
        alpha = -math.inf
        beta = math.inf

        for move in moves:
            if time.time() - self.start_time > self.max_time:
                raise TimeoutError()

            # apply the move (this also flips turn inside GameState)
            if state.last_move_forms_mill(move):
                # must consider all captures
                captures = state.can_capture_positions()
                for cap in captures:
                    new_state = state.apply_move(move, remove_pos=cap)
                    val, mate_dist = self._minimax_with_mate(new_state, depth - 1, alpha, beta, maximizing=False)
                    if val > best_score:
                        best_score = val
                        best_choice = (move, cap)
                        best_mate = mate_dist
                    alpha = max(alpha, val)
            else:
                new_state = state.apply_move(move, remove_pos=None)
                val, mate_dist = self._minimax_with_mate(new_state, depth - 1, alpha, beta, maximizing=False)
                if val > best_score:
                    best_score = val
                    best_choice = (move, None)
                    best_mate = mate_dist
                alpha = max(alpha, val)

        return best_score, best_choice, best_mate

    # ======================================================================
    # MINIMAX WITH MATE DISTANCE
    # ======================================================================
    def _minimax_with_mate(self, state, depth, alpha, beta, maximizing):
        """
        Returns tuple (score, mate_distance)
        - score: numeric evaluation
        - mate_distance: None if no forced mate found in this subtree,
                         otherwise number of plies until mate.
        """
        if time.time() - self.start_time > self.max_time:
            raise TimeoutError()

        over, winner = state.is_game_over()
        if over:
            if winner == self.color:
                # immediate win: mate in 0 plies
                return 1000000 + depth, 0
            else:
                return -1000000 - depth, None

        if depth == 0:
            return self.evaluate(state), None

        key = (tuple(state.board), state.current, state.phase, depth, maximizing)
        if key in self.transposition:
            return self.transposition[key]

        moves = state.legal_moves()
        if not moves:
            return (-1000000 if maximizing else 1000000), None

        if maximizing:
            value = -math.inf
            best_mate = None

            for move in moves:
                if time.time() - self.start_time > self.max_time:
                    raise TimeoutError()

                if state.last_move_forms_mill(move):
                    captures = state.can_capture_positions()
                    for cap in captures:
                        new_state = state.apply_move(move, remove_pos=cap)
                        val, mate_dist = self._minimax_with_mate(new_state, depth - 1, alpha, beta, False)
                        if val > value:
                            value = val
                            best_mate = mate_dist
                        alpha = max(alpha, value)
                        if alpha >= beta:
                            break
                else:
                    new_state = state.apply_move(move, remove_pos=None)
                    val, mate_dist = self._minimax_with_mate(new_state, depth - 1, alpha, beta, False)
                    if val > value:
                        value = val
                        best_mate = mate_dist
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        break

            mate_result = best_mate + 1 if best_mate is not None else None
            self.transposition[key] = (value, mate_result)
            return value, mate_result

        else:
            value = math.inf
            best_mate = None

            for move in moves:
                if time.time() - self.start_time > self.max_time:
                    raise TimeoutError()

                if state.last_move_forms_mill(move):
                    captures = state.can_capture_positions()
                    for cap in captures:
                        new_state = state.apply_move(move, remove_pos=cap)
                        val, mate_dist = self._minimax_with_mate(new_state, depth - 1, alpha, beta, True)
                        if val < value:
                            value = val
                            best_mate = mate_dist
                        beta = min(beta, value)
                        if alpha >= beta:
                            break
                else:
                    new_state = state.apply_move(move, remove_pos=None)
                    val, mate_dist = self._minimax_with_mate(new_state, depth - 1, alpha, beta, True)
                    if val < value:
                        value = val
                        best_mate = mate_dist
                    beta = min(beta, value)
                    if alpha >= beta:
                        break

            mate_result = best_mate + 1 if best_mate is not None else None
            self.transposition[key] = (value, mate_result)
            return value, mate_result

    # ======================================================================
    # EVALUATION
    # ======================================================================
    def evaluate(self, state: GameState):
        """
        Heuristic: piece difference, mobility, potential mills.
        """
        my = state.pieces_count(self.color)
        opp = state.pieces_count(-self.color)
        piece_diff = 100 * (my - opp)

        # mobility (using color-agnostic legal_moves_for)
        my_moves = len(state.legal_moves_for(self.color))
        opp_moves = len(state.legal_moves_for(-self.color))
        mobility = 5 * (my_moves - opp_moves)

        # potential mills
        potential = 0
        for a, b, c in MILLS:
            line = [state.board[a], state.board[b], state.board[c]]
            if line.count(self.color) == 2 and line.count(EMPTY) == 1:
                potential += 1
            if line.count(-self.color) == 2 and line.count(EMPTY) == 1:
                potential -= 1

        return piece_diff + mobility + 30 * potential