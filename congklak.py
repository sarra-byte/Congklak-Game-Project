"""
Congklak Game with Minimax + Alpha-Beta Pruning AI
Based on: "Implementation of Minimax with Alpha-Beta Pruning as Computer Player in Congklak"
by Brian Sumali, Ivan Michael Siregar, Rosalina - President University (2016)
Published in: Jurnal Teknik Informatika dan Sistem Informasi, Vol.2 No.2, Agustus 2016

Rules:
- 2 rows of 7 holes + 2 "home" holes = 16 total
- Each hole starts with 7 seeds
- Players distribute seeds counter-clockwise
- Skip opponent's home, not own home
- Rule 4: Last seed in own home        -> extra turn
- Rule 5: Last seed in own EMPTY hole  -> capture opposite hole -> end turn
- Rule 6: Last seed in own OCCUPIED hole -> relay sowing
- Game ends when all holes on both sides are empty
"""

import tkinter as tk
from tkinter import font as tkfont, messagebox
import random
import time
import copy
import math


# ─────────────────────────────────────────────
#  GAME LOGIC
# ─────────────────────────────────────────────

class CongklakState:
    """
    Board layout (indices):
    
    Player 2 holes (top, right to left): indices 1-7
    Player 2 Home: index 0
    Player 1 holes (bottom, left to right): indices 8-14
    Player 1 Home: index 15

    Visual layout:
    [home2] [7][6][5][4][3][2][1]
            [8][9][10][11][12][13][14] [home1]
    """
    PLAYER1 = 1
    PLAYER2 = 2

    P1_HOLES = list(range(8, 15))   # indices 8-14
    P2_HOLES = list(range(1, 8))    # indices 1-7
    P1_HOME = 15
    P2_HOME = 0
    TOTAL = 16

    def __init__(self):
        self.board = [0] * 16
        # Fill each hole with 7 seeds
        for i in self.P1_HOLES:
            self.board[i] = 7
        for i in self.P2_HOLES:
            self.board[i] = 7
        self.current_player = self.PLAYER1

    def clone(self):
        s = CongklakState.__new__(CongklakState)
        s.board = self.board[:]
        s.current_player = self.current_player
        return s

    def get_holes(self, player):
        return self.P1_HOLES if player == self.PLAYER1 else self.P2_HOLES

    def get_home(self, player):
        return self.P1_HOME if player == self.PLAYER1 else self.P2_HOME

    def get_opponent(self, player):
        return self.PLAYER2 if player == self.PLAYER1 else self.PLAYER1

    def get_opposite(self, hole):
        """
        Get the opposite hole (same column, other row).

        Board columns (left to right):
          col 1: P2 hole 1  <->  P1 hole 8
          col 2: P2 hole 2  <->  P1 hole 9
          ...
          col 7: P2 hole 7  <->  P1 hole 14

        Formula:
          P1 hole h (8-14) -> opposite = h - 7   (8->1, 9->2, ..., 14->7)
          P2 hole h (1-7)  -> opposite = h + 7   (1->8, 2->9, ...,  7->14)
        """
        if hole in self.P1_HOLES:
            return hole - 7   # 8->1, 9->2, 10->3, 11->4, 12->5, 13->6, 14->7
        elif hole in self.P2_HOLES:
            return hole + 7   # 1->8, 2->9, 3->10, 4->11, 5->12, 6->13,  7->14
        return -1

    def legal_moves(self, player):
        return [h for h in self.get_holes(player) if self.board[h] > 0]

    def is_terminal(self):
        return (all(self.board[h] == 0 for h in self.P1_HOLES) and
                all(self.board[h] == 0 for h in self.P2_HOLES))

    def do_move(self, hole):
        """
        Execute a move from the given hole.
        Returns the next player to move.
        Counter-clockwise sowing:
          P1 moves: 8->9->10->...->14->15(home)->7->6->5->...->1->0(skip)->8->...
          P2 moves: 7->6->5->...->1->0(home)->8->9->...->14->15(skip)->7->...
        """
        seeds = self.board[hole]
        self.board[hole] = 0
        pos = hole
        opponent_home = self.get_home(self.get_opponent(self.current_player))

        while seeds > 0:
            pos = self._next(pos, self.current_player)
            if pos == opponent_home:
                continue  # skip opponent's home (already advanced)
            # Actually we need to skip, so let's redo:
            # The _next already handles skip in logic below
            self.board[pos] += 1
            seeds -= 1

        # Evaluate last seed landing
        if pos == self.get_home(self.current_player):
            # Extra turn for current player
            return self.current_player

        player_holes = self.get_holes(self.current_player)
        if pos in player_holes and self.board[pos] == 1:
            # Landed in own empty hole -> capture
            opposite = self.get_opposite(pos)
            captured = self.board[opposite]
            self.board[opposite] = 0
            self.board[pos] = 0
            self.board[self.get_home(self.current_player)] += captured + 1
            return self.get_opponent(self.current_player)

        if pos not in (self.P1_HOME, self.P2_HOME) and self.board[pos] > 1:
            # Landed in occupied hole -> continue sowing (already handled above)
            # This is handled by the while loop above — when seeds > 0 we keep going
            # Actually the rule says: if last piece in occupied hole, pick up all and sow again
            # We need to re-implement with relay sowing
            pass

        return self.get_opponent(self.current_player)

    def _next(self, pos, player):
        """Get next position in counter-clockwise order, skipping opponent's home."""
        opponent_home = self.get_home(self.get_opponent(player))
        # Counter-clockwise order: 8,9,10,11,12,13,14,15,7,6,5,4,3,2,1,0 then back
        order = self.P1_HOLES + [self.P1_HOME] + list(reversed(self.P2_HOLES)) + [self.P2_HOME]
        # This is circular for P1. For P2, same circular but different orientation.
        # Actually, both players use the SAME circular path (counter-clockwise).
        idx = order.index(pos)
        while True:
            idx = (idx + 1) % len(order)
            nxt = order[idx]
            if nxt != opponent_home:
                return nxt


def do_move_full(state, hole):
    """
    Full relay-sowing move. Returns (new_state, next_player).

    Sowing order (counter-clockwise, same for both players):
      [8..14] -> [15=P1_HOME] -> [7..1] -> [0=P2_HOME] -> repeat

    Rules:
      Rule 4: last in own home          -> extra turn
      Rule 5: last in own EMPTY hole    -> capture opposite -> end turn
      Rule 6: last in own OCCUPIED hole -> relay (pick up and sow again)
      Otherwise (opponent hole)         -> end turn immediately
    """
    s = state.clone()
    current = s.current_player
    own_home = s.get_home(current)
    own_holes = s.get_holes(current)
    opponent_home = s.get_home(s.get_opponent(current))
    order = s.P1_HOLES + [s.P1_HOME] + list(reversed(s.P2_HOLES)) + [s.P2_HOME]

    pos = hole
    for _ in range(500):
        seeds = s.board[pos]
        s.board[pos] = 0

        i = order.index(pos)
        distributed = 0
        last = pos

        # Sow seeds one by one; remember state of each hole BEFORE placing
        last_hole_before = 0  # tracks content of destination hole BEFORE last seed
        while distributed < seeds:
            i = (i + 1) % len(order)
            nxt = order[i]
            if nxt == opponent_home:
                continue
            if distributed == seeds - 1:
                # This is the last seed — record hole state BEFORE placing
                last_hole_before = s.board[nxt]
            s.board[nxt] += 1
            distributed += 1
            last = nxt

        # Rule 4: extra turn — last seed in own home
        if last == own_home:
            s.current_player = current
            return s, current

        # Rule 5: capture — last seed in own hole that was EMPTY before
        # (last_hole_before == 0 means the hole was empty when the seed arrived)
        if last in own_holes and last_hole_before == 0:
            opp = s.get_opposite(last)
            captured = s.board[opp]
            s.board[opp] = 0
            s.board[last] = 0
            s.board[own_home] += captured + 1
            s.current_player = s.get_opponent(current)
            return s, s.get_opponent(current)

        # Rule 6: relay — last seed in own hole that was OCCUPIED before
        # (last_hole_before > 0 means the hole already had seeds)
        if last in own_holes and last_hole_before > 0:
            pos = last
            continue

        # Default: landed on opponent hole (any state) -> end turn
        s.current_player = s.get_opponent(current)
        return s, s.get_opponent(current)

    s.current_player = s.get_opponent(current)
    return s, s.get_opponent(current)


# ─────────────────────────────────────────────
#  MINIMAX WITH ALPHA-BETA PRUNING
# ─────────────────────────────────────────────

class MinimaxAI:
    def __init__(self, depth=3):
        self.depth = depth
        self.nodes_explored = 0

    def evaluate(self, state):
        """Heuristic: difference in home seeds (AI = Player 2 = MAX)."""
        return state.board[state.P2_HOME] - state.board[state.P1_HOME]

    # ── Article Figure 3.7 / 5.5 : GetMove(State S) : Move ───────────────
    def GetMove(self, S):
        """
        Returns the best Move for the current state S.
        Corresponds to GetMove(State S) : Move in the article.
        """
        self.nodes_explored = 0
        Best_Move = None
        Alpha = -math.inf
        Beta  =  math.inf
        Best_Move_Value = -math.inf

        moves = S.legal_moves(S.current_player)
        if not moves:
            return None

        for Mi in moves:
            NS, NP = do_move_full(S, Mi)
            self.nodes_explored += 1

            if NS.is_terminal():
                Current_Move_Value = self.evaluate(NS)
            elif NP == S.current_player:
                # NP is current player (extra turn) → still MAX
                Current_Move_Value = self.GetMax(NS, Alpha, Beta, 1)
            else:
                # NP is opponent → MIN
                Current_Move_Value = self.GetMin(NS, Alpha, Beta, 1)

            if Current_Move_Value > Best_Move_Value:
                Alpha            = Current_Move_Value
                Best_Move_Value  = Current_Move_Value
                Best_Move        = Mi

            # Alpha cut-off at root
            if Alpha >= Beta:
                break

        # If no best move found (all losses), pick random
        if Best_Move is None:
            Best_Move = random.choice(moves)

        return Best_Move

    # ── Article Figure 3.8 / 5.6 : GetMax(State S, Alpha, Beta, Depth D) ─
    def GetMax(self, S, Alpha, Beta, D):
        """
        Returns the best (maximum) move value for state S at depth D.
        Corresponds to GetMax(State S, MinimumBound Alpha, MaximumBound Beta, Depth D) : Value
        """
        # Base case: terminal state OR depth limit reached
        if S.is_terminal() or D >= self.depth:
            return self.evaluate(S)

        moves = S.legal_moves(S.current_player)
        if not moves:
            return self.evaluate(S)

        Best_Move_Value = -math.inf

        for Mi in moves:
            NS, NP = do_move_full(S, Mi)
            self.nodes_explored += 1

            if NS.is_terminal():
                Current_Move_Value = self.evaluate(NS)
            elif NP == S.current_player:
                # Extra turn → still MAX
                Current_Move_Value = self.GetMax(NS, Alpha, Beta, D + 1)
            else:
                Current_Move_Value = self.GetMin(NS, Alpha, Beta, D + 1)

            if Current_Move_Value > Best_Move_Value:
                Best_Move_Value = Current_Move_Value
                Alpha = max(Alpha, Best_Move_Value)

            # Alpha-Beta pruning condition (article: "If Alpha >= Beta: break")
            if Alpha >= Beta:
                break  # Prune remaining branches

        return Best_Move_Value

    # ── Article Figure 3.9 / 5.7 : GetMin(State S, Alpha, Beta, Depth D) ─
    def GetMin(self, S, Alpha, Beta, D):
        """
        Returns the worst (minimum) move value for state S at depth D.
        Corresponds to GetMin(State S, MinimumBound Alpha, MaximumBound Beta, Depth D) : Value
        """
        # Base case: terminal state OR depth limit reached
        if S.is_terminal() or D >= self.depth:
            return self.evaluate(S)

        moves = S.legal_moves(S.current_player)
        if not moves:
            return self.evaluate(S)

        Worst_Move_Value = math.inf

        for Mi in moves:
            NS, NP = do_move_full(S, Mi)
            self.nodes_explored += 1

            if NS.is_terminal():
                Current_Move_Value = self.evaluate(NS)
            elif NP == S.current_player:
                # Extra turn → still MIN
                Current_Move_Value = self.GetMin(NS, Alpha, Beta, D + 1)
            else:
                Current_Move_Value = self.GetMax(NS, Alpha, Beta, D + 1)

            if Current_Move_Value < Worst_Move_Value:
                Worst_Move_Value = Current_Move_Value
                Beta = min(Beta, Worst_Move_Value)

            # Alpha-Beta pruning condition (article: "If Alpha >= Beta: break")
            if Alpha >= Beta:
                break  # Prune remaining branches

        return Worst_Move_Value

    # ── Keep snake_case aliases so the GUI code still works ───────────────
    def get_move(self, state): return self.GetMove(state)
    def get_max(self, s, a, b, d): return self.GetMax(s, a, b, d)
    def get_min(self, s, a, b, d): return self.GetMin(s, a, b, d)


# ─────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────

class CongklakGUI:
    # Colors
    BG         = "#1a0a00"
    BOARD_BG   = "#5c2d0a"
    HOLE_EMPTY = "#3d1f07"
    HOLE_P1    = "#e8a020"
    HOLE_P2    = "#20a8e8"
    HOME_P1    = "#c87000"
    HOME_P2    = "#0070c8"
    SEED_COLOR = "#f5d060"
    TEXT_LIGHT = "#f5e6c8"
    TEXT_DARK  = "#1a0a00"
    HIGHLIGHT  = "#ffe066"
    DISABLED   = "#5c3a1a"
    GREEN_MSG  = "#50e878"
    RED_MSG    = "#e85050"

    def __init__(self, root):
        self.root = root
        self.root.title("Congklak — Minimax AI")
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)

        self.ai_level = tk.StringVar(value="Normal")
        self.first_player = tk.StringVar(value="Human")
        self.state = None
        self.ai = None
        self.human_player = CongklakState.PLAYER1
        self.game_active = False
        self.hole_buttons = {}

        self._build_fonts()
        self._build_main_menu()

    def _build_fonts(self):
        self.font_title  = tkfont.Font(family="Georgia", size=26, weight="bold")
        self.font_sub    = tkfont.Font(family="Georgia", size=13, slant="italic")
        self.font_btn    = tkfont.Font(family="Courier", size=12, weight="bold")
        self.font_hole   = tkfont.Font(family="Courier", size=11, weight="bold")
        self.font_home   = tkfont.Font(family="Courier", size=14, weight="bold")
        self.font_label  = tkfont.Font(family="Courier", size=10)
        self.font_status = tkfont.Font(family="Courier", size=11, weight="bold")
        self.font_info   = tkfont.Font(family="Courier", size=9)

    # ── MAIN MENU ──────────────────────────────────────────────────────────

    def _build_main_menu(self):
        self._clear()
        f = tk.Frame(self.root, bg=self.BG, padx=60, pady=40)
        f.pack()

        tk.Label(f, text="⚬  CONGKLAK  ⚬", font=self.font_title,
                 bg=self.BG, fg=self.HIGHLIGHT).pack(pady=(0, 4))
        tk.Label(f, text="Jeu traditionnel indonésien avec IA Minimax",
                 font=self.font_sub, bg=self.BG, fg="#b89060").pack(pady=(0, 30))

        for txt, cmd in [
            ("▶  Jouer contre l'IA",    self._open_settings),
            ("ℹ  Règles du jeu",        self._show_rules),
            ("✕  Quitter",              self.root.quit),
        ]:
            tk.Button(f, text=txt, font=self.font_btn, bg=self.BOARD_BG,
                      fg=self.TEXT_LIGHT, activebackground=self.HIGHLIGHT,
                      activeforeground=self.TEXT_DARK, relief="flat",
                      width=32, pady=10, cursor="hand2",
                      command=cmd).pack(pady=6)

    # ── SETTINGS ───────────────────────────────────────────────────────────

    def _open_settings(self):
        self._clear()
        f = tk.Frame(self.root, bg=self.BG, padx=60, pady=40)
        f.pack()

        tk.Label(f, text="Paramètres", font=self.font_title,
                 bg=self.BG, fg=self.HIGHLIGHT).pack(pady=(0, 24))

        # AI Level
        tk.Label(f, text="Niveau de l'IA :", font=self.font_btn,
                 bg=self.BG, fg=self.TEXT_LIGHT).pack(anchor="w")
        lvl_f = tk.Frame(f, bg=self.BG)
        lvl_f.pack(anchor="w", pady=(4, 16))
        for lvl in ["Facile", "Normal", "Expert", "Impossible"]:
            tk.Radiobutton(lvl_f, text=lvl, variable=self.ai_level, value=lvl,
                           font=self.font_label, bg=self.BG, fg=self.TEXT_LIGHT,
                           selectcolor=self.BOARD_BG,
                           activebackground=self.BG).pack(side="left", padx=8)

        # First player
        tk.Label(f, text="Premier joueur :", font=self.font_btn,
                 bg=self.BG, fg=self.TEXT_LIGHT).pack(anchor="w")
        fp_f = tk.Frame(f, bg=self.BG)
        fp_f.pack(anchor="w", pady=(4, 24))
        for fp in ["Human", "Computer"]:
            tk.Radiobutton(fp_f, text=fp, variable=self.first_player, value=fp,
                           font=self.font_label, bg=self.BG, fg=self.TEXT_LIGHT,
                           selectcolor=self.BOARD_BG,
                           activebackground=self.BG).pack(side="left", padx=8)

        btn_f = tk.Frame(f, bg=self.BG)
        btn_f.pack()
        tk.Button(btn_f, text="✓  Démarrer", font=self.font_btn, bg=self.HOLE_P1,
                  fg=self.TEXT_DARK, relief="flat", width=16, pady=8,
                  cursor="hand2", command=self._start_game).pack(side="left", padx=8)
        tk.Button(btn_f, text="←  Retour", font=self.font_btn, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", width=16, pady=8,
                  cursor="hand2", command=self._build_main_menu).pack(side="left", padx=8)

    # ── RULES ──────────────────────────────────────────────────────────────

    def _show_rules(self):
        win = tk.Toplevel(self.root)
        win.title("Règles du Congklak")
        win.configure(bg=self.BG)
        win.resizable(False, False)
        rules = (
            "RÈGLES DU CONGKLAK\n"
            "══════════════════════════════════════\n\n"
            "Plateau : 2 rangées de 7 trous + 2 maisons (16 trous).\n"
            "Départ  : 7 graines dans chaque trou (maisons vides).\n\n"
            "Tour de jeu :\n"
            "  1. Choisissez un trou de votre côté.\n"
            "  2. Distribuez les graines sens anti-horaire (une par trou).\n"
            "  3. On saute la maison adverse, pas la sienne.\n\n"
            "Règles spéciales :\n"
            "  • Dernière graine dans votre maison → rejouer.\n"
            "  • Dernière graine dans trou vide (votre côté) → capture\n"
            "    des graines du trou opposé → dans votre maison.\n"
            "  • Dernière graine dans trou occupé → ramasser et continuer.\n\n"
            "Fin de partie :\n"
            "  • Quand tous les trous des deux côtés sont vides.\n"
            "  • Le joueur avec le plus de graines dans sa maison gagne.\n\n"
            "IA : Minimax avec Alpha-Beta Pruning\n"
            "  Facile    : Aléatoire\n"
            "  Normal    : Profondeur 2\n"
            "  Expert    : Profondeur 4\n"
            "  Impossible: Profondeur 6\n"
        )
        tk.Label(win, text=rules, font=tkfont.Font(family="Courier", size=10),
                 bg=self.BG, fg=self.TEXT_LIGHT, justify="left",
                 padx=30, pady=20).pack()
        tk.Button(win, text="Fermer", font=self.font_btn, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", pady=6,
                  command=win.destroy).pack(pady=(0, 20))

    # ── GAME START ─────────────────────────────────────────────────────────

    def _start_game(self):
        lvl = self.ai_level.get()
        depth_map = {"Facile": 0, "Normal": 2, "Expert": 4, "Impossible": 6}
        depth = depth_map[lvl]

        self.state = CongklakState()
        self.ai = MinimaxAI(depth=depth)
        self.game_active = True

        if self.first_player.get() == "Human":
            self.human_player = CongklakState.PLAYER1
            self.state.current_player = CongklakState.PLAYER1
        else:
            self.human_player = CongklakState.PLAYER1
            self.state.current_player = CongklakState.PLAYER2

        self._build_game_screen()

        if self.state.current_player != self.human_player:
            self.root.after(800, self._ai_move)

    # ── GAME SCREEN ────────────────────────────────────────────────────────

    def _build_game_screen(self):
        self._clear()
        root = self.root

        # Top bar
        top = tk.Frame(root, bg=self.BG, pady=8)
        top.pack(fill="x", padx=20)

        tk.Button(top, text="← Menu", font=self.font_label, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._confirm_quit).pack(side="left")

        self.lbl_level = tk.Label(top,
            text=f"Niveau: {self.ai_level.get()}",
            font=self.font_label, bg=self.BG, fg="#b89060")
        self.lbl_level.pack(side="right")

        # Status
        self.lbl_status = tk.Label(root, text="", font=self.font_status,
                                   bg=self.BG, fg=self.GREEN_MSG, pady=6)
        self.lbl_status.pack()

        # Board frame
        board_frame = tk.Frame(root, bg=self.BOARD_BG, bd=0,
                               padx=18, pady=18, relief="flat")
        board_frame.pack(padx=24, pady=4)

        self.hole_buttons = {}
        self._draw_board(board_frame)

        # Score bar
        self.lbl_score = tk.Label(root, text="", font=self.font_status,
                                  bg=self.BG, fg=self.TEXT_LIGHT, pady=6)
        self.lbl_score.pack()

        # Info
        self.lbl_info = tk.Label(root, text="", font=self.font_info,
                                 bg=self.BG, fg="#888060", pady=2)
        self.lbl_info.pack()

        self._refresh_board()
        self._update_status()

    def _draw_board(self, frame):
        """
        Anti-clockwise sowing visualised correctly:

          [HOME2=left] [P2: 1  2  3  4  5  6  7] [      ]
          [           ] [P1: 8  9 10 11 12 13 14] [HOME1=right]

        P1 sows left→right (8→9→…→14→HOME1→ top-right→left)   anti-clockwise ✓
        P2 sows right→left (7→6→…→1→HOME2→ bottom-left→right)  anti-clockwise ✓

        Both rows share the same left-to-right column alignment:
          col 1=holes(1,8), col2=(2,9), …, col7=(7,14)
        so grains visually wrap around the oval in one direction.
        """
        # Home P2 (LEFT)
        home2_frame = tk.Frame(frame, bg=self.BOARD_BG)
        home2_frame.grid(row=0, column=0, rowspan=4, padx=(0, 12), pady=4)
        self._make_home_widget(home2_frame, CongklakState.PLAYER2)

        # P2 holes (row 1): LEFT→RIGHT order [1,2,3,4,5,6,7]
        # Anti-clockwise for P2 = sow from right to left (7→6→5→4→3→2→1→HOME2) ✓
        p2_display_order = CongklakState.P2_HOLES  # [1,2,3,4,5,6,7]

        # Hole number labels for P2 (row 0, above buttons)
        for col_idx, hole in enumerate(p2_display_order):
            tk.Label(frame, text=str(hole), font=self.font_info,
                     bg=self.BOARD_BG, fg="#80c8e8").grid(
                         row=0, column=col_idx + 1, pady=(4, 0))

        for col_idx, hole in enumerate(p2_display_order):
            btn = tk.Button(frame, text="7", font=self.font_hole,
                            width=4, height=2,
                            bg=self.HOLE_P2, fg=self.TEXT_DARK,
                            relief="flat", cursor="arrow",
                            state="disabled")
            btn.grid(row=1, column=col_idx + 1, padx=3, pady=2)
            self.hole_buttons[hole] = btn

        # P1 holes (row 2): LEFT→RIGHT order [8,9,10,11,12,13,14]
        # Anti-clockwise for P1 = sow from left to right (8→9→…→14→HOME1) ✓
        for col_idx, hole in enumerate(CongklakState.P1_HOLES):
            btn = tk.Button(frame, text="7", font=self.font_hole,
                            width=4, height=2,
                            bg=self.HOLE_P1, fg=self.TEXT_DARK,
                            relief="flat", cursor="hand2",
                            command=lambda h=hole: self._human_move(h))
            btn.grid(row=2, column=col_idx + 1, padx=3, pady=2)
            self.hole_buttons[hole] = btn

        # Hole number labels for P1 (row 3, below buttons)
        for col_idx, hole in enumerate(CongklakState.P1_HOLES):
            tk.Label(frame, text=str(hole), font=self.font_info,
                     bg=self.BOARD_BG, fg="#e8c060").grid(
                         row=3, column=col_idx + 1, pady=(0, 4))

        # Home P1 (RIGHT)
        home1_frame = tk.Frame(frame, bg=self.BOARD_BG)
        home1_frame.grid(row=0, column=8, rowspan=4, padx=(12, 0), pady=4)
        self._make_home_widget(home1_frame, CongklakState.PLAYER1)

        # Direction labels
        tk.Label(frame, text="IA → sens de semis →", font=self.font_info,
                 bg=self.BOARD_BG, fg=self.HOLE_P2).grid(
                     row=4, column=1, columnspan=7, sticky="w", pady=(4, 0))
        tk.Label(frame, text="← sens de semis ← Vous", font=self.font_info,
                 bg=self.BOARD_BG, fg=self.HOLE_P1).grid(
                     row=5, column=1, columnspan=7, sticky="e")

    def _make_home_widget(self, frame, player):
        color = self.HOME_P1 if player == CongklakState.PLAYER1 else self.HOME_P2
        lbl_name = "Maison\nVous" if player == CongklakState.PLAYER1 else "Maison\nIA"
        tk.Label(frame, text=lbl_name, font=self.font_info,
                 bg=self.BOARD_BG, fg=color).pack()
        lbl = tk.Label(frame, text="0", font=self.font_home,
                       bg=color, fg=self.TEXT_DARK,
                       width=5, height=4, relief="flat")
        lbl.pack(pady=4)
        attr = "lbl_home1" if player == CongklakState.PLAYER1 else "lbl_home2"
        setattr(self, attr, lbl)

    # ── REFRESH ────────────────────────────────────────────────────────────

    def _refresh_board(self):
        b = self.state.board
        for hole, btn in self.hole_buttons.items():
            val = b[hole]
            btn.config(text=str(val))
            if hole in CongklakState.P1_HOLES:
                base = self.HOLE_P1 if val > 0 else self.HOLE_EMPTY
                btn.config(bg=base)
            else:
                base = self.HOLE_P2 if val > 0 else self.HOLE_EMPTY
                btn.config(bg=base)

        self.lbl_home1.config(text=str(b[CongklakState.P1_HOME]))
        self.lbl_home2.config(text=str(b[CongklakState.P2_HOME]))

        total = sum(b)
        self.lbl_score.config(
            text=f"Vous: {b[CongklakState.P1_HOME]}  •  "
                 f"IA: {b[CongklakState.P2_HOME]}  •  "
                 f"En jeu: {total - b[CongklakState.P1_HOME] - b[CongklakState.P2_HOME]}")

    def _update_status(self):
        if not self.game_active:
            return
        if self.state.current_player == self.human_player:
            self.lbl_status.config(text="Votre tour — Choisissez un trou",
                                   fg=self.GREEN_MSG)
            self._set_p1_buttons(True)
        else:
            self.lbl_status.config(text="L'IA réfléchit…", fg="#e8c060")
            self._set_p1_buttons(False)

    def _set_p1_buttons(self, enabled):
        legal = self.state.legal_moves(self.human_player)
        for hole in CongklakState.P1_HOLES:
            btn = self.hole_buttons[hole]
            if enabled and hole in legal:
                btn.config(state="normal", cursor="hand2",
                           relief="flat")
            else:
                btn.config(state="disabled", cursor="arrow")

    def _highlight_hole(self, hole, on):
        if hole not in self.hole_buttons:
            return
        if on:
            self.hole_buttons[hole].config(bg=self.HIGHLIGHT, fg=self.TEXT_DARK)
        else:
            self._refresh_board()

    # ── HUMAN MOVE ─────────────────────────────────────────────────────────

    def _human_move(self, hole):
        if not self.game_active:
            return
        if self.state.current_player != self.human_player:
            return
        if hole not in self.state.legal_moves(self.human_player):
            return

        self._set_p1_buttons(False)
        self._highlight_hole(hole, True)
        self.root.after(300, lambda: self._apply_move(hole))

    def _apply_move(self, hole):
        new_state, next_player = do_move_full(self.state, hole)
        self.state = new_state
        self._refresh_board()

        if self.state.is_terminal():
            self._end_game()
            return

        self._check_soft_endgame()
        if not self.game_active:
            return

        self.state.current_player = next_player
        self._update_status()

        if next_player != self.human_player:
            self.root.after(700, self._ai_move)

    # ── AI MOVE ────────────────────────────────────────────────────────────

    def _ai_move(self):
        if not self.game_active:
            return

        lvl = self.ai_level.get()
        t0 = time.time()

        if lvl == "Facile":
            moves = self.state.legal_moves(self.state.current_player)
            move = random.choice(moves) if moves else None
        else:
            move = self.ai.get_move(self.state)

        elapsed = time.time() - t0

        if move is None:
            self.state.current_player = self.human_player
            self._update_status()
            return

        self.lbl_info.config(
            text=f"IA: trou {move}  |  temps: {elapsed:.2f}s  |  "
                 f"noeuds explorés: {self.ai.nodes_explored if lvl != 'Facile' else 'N/A'}")

        self._highlight_hole(move, True)
        self.root.after(500, lambda: self._apply_ai_move(move))

    def _apply_ai_move(self, move):
        new_state, next_player = do_move_full(self.state, move)
        self.state = new_state
        self._refresh_board()

        if self.state.is_terminal():
            self._end_game()
            return

        self._check_soft_endgame()
        if not self.game_active:
            return

        self.state.current_player = next_player
        self._update_status()

        if next_player != self.human_player:
            self.root.after(800, self._ai_move)

    # ── SOFT END-GAME DETECTION ────────────────────────────────────────────

    def _check_soft_endgame(self):
        total_seeds = 98  # 7 holes * 7 seeds * 2 players
        half = total_seeds // 2 + 1
        b = self.state.board
        if b[CongklakState.P1_HOME] >= half:
            if messagebox.askyesno("Victoire évidente",
                                   f"Vous avez {b[CongklakState.P1_HOME]} graines !\n"
                                   "La victoire est évidente. Terminer la partie ?"):
                self._end_game(forced=True)
        elif b[CongklakState.P2_HOME] >= half:
            if messagebox.askyesno("Défaite évidente",
                                   f"L'IA a {b[CongklakState.P2_HOME]} graines !\n"
                                   "La défaite est évidente. Terminer la partie ?"):
                self._end_game(forced=True)

    # ── END GAME ───────────────────────────────────────────────────────────

    def _end_game(self, forced=False):
        self.game_active = False
        self._set_p1_buttons(False)
        b = self.state.board
        p1 = b[CongklakState.P1_HOME]
        p2 = b[CongklakState.P2_HOME]

        if p1 > p2:
            msg = f"🎉 Vous gagnez !\nVous: {p1}  •  IA: {p2}"
            color = self.GREEN_MSG
        elif p2 > p1:
            msg = f"💻 L'IA gagne !\nVous: {p1}  •  IA: {p2}"
            color = self.RED_MSG
        else:
            msg = f"🤝 Égalité !\nVous: {p1}  •  IA: {p2}"
            color = self.HIGHLIGHT

        self.lbl_status.config(text=msg, fg=color)

        # Show dialog
        result_win = tk.Toplevel(self.root)
        result_win.title("Résultat")
        result_win.configure(bg=self.BG)
        result_win.resizable(False, False)
        tk.Label(result_win, text=msg, font=self.font_title,
                 bg=self.BG, fg=color, padx=40, pady=30).pack()
        btn_f = tk.Frame(result_win, bg=self.BG)
        btn_f.pack(pady=(0, 20))
        tk.Button(btn_f, text="Rejouer", font=self.font_btn, bg=self.HOLE_P1,
                  fg=self.TEXT_DARK, relief="flat", width=14, pady=8,
                  cursor="hand2",
                  command=lambda: [result_win.destroy(), self._start_game()]
                  ).pack(side="left", padx=8)
        tk.Button(btn_f, text="Menu", font=self.font_btn, bg=self.BOARD_BG,
                  fg=self.TEXT_LIGHT, relief="flat", width=14, pady=8,
                  cursor="hand2",
                  command=lambda: [result_win.destroy(), self._build_main_menu()]
                  ).pack(side="left", padx=8)

    def _confirm_quit(self):
        if self.game_active:
            if messagebox.askyesno("Quitter", "Abandonner la partie en cours ?"):
                self.game_active = False
                self._build_main_menu()
        else:
            self._build_main_menu()

    # ── UTILITY ────────────────────────────────────────────────────────────

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("720x520")
    app = CongklakGUI(root)
    root.mainloop()
