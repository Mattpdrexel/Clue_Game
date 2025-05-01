from Player     import Player
from Constants  import SUSPECTS, WEAPONS, ROOMS

# clockwise ring of rooms
RING = ["Study", "Hall", "Lounge",
        "Dining Room", "Kitchen", "Ball Room",
        "Conservatory", "Billiard Room", "Library"]

class SimpleAIPlayer(Player):
    """
    Dumb-but-sure Clue-o bot.
    • Moves through rooms in fixed ring order
    • Leaves every room on the next turn
    • Crosses off shown cards
    • Accuses when envelope forced OR only one card per category remains
      OR after B full room-cycles (fallback)
    """
    B = 4   # fallback after ≤ 36 suggestions ≈ 80 turns

    # ---------- init ----------
    def __init__(self, player_id, character):
        super().__init__(player_id, character)
        self.ring_ptr = 0
        self.unknown_suspects = set(SUSPECTS)
        self.unknown_weapons  = set(WEAPONS)
        self.unknown_rooms    = set(ROOMS)
        self.visited_rooms = set()
        self.cycle_counter  = 0
        self.must_exit_next_turn = False
        self._last_positions = []

        # Attributes expected by the game engine
        self.target_room = RING[self.ring_ptr]
        self.last_suggestion = None
        self.last_suggestion_room = None
        self.game_state_log = []

    # ---------- movement ----------
    def choose_move(self, valid_moves, game):
        if not valid_moves:
            return None

        # forced hallway exit if still inside same room
        if self.must_exit_next_turn:
            self.must_exit_next_turn = False
            doors = [m for m in valid_moves
                     if game.mansion_board.get_cell_type(*m) == "entrance"]
            if doors:
                return doors[0]

        target_room = RING[self.ring_ptr]
        entrances = game.mansion_board.room_dict[target_room].room_entrance_list
        goals = {(e.row, e.column) for e in entrances}

        # forbid immediate backtrack
        candidates = [m for m in valid_moves if m not in self._last_positions[-2:]] or valid_moves
        best = min(candidates,
                   key=lambda m: min(abs(m[0]-r)+abs(m[1]-c) for r, c in goals))

        self._last_positions.append(best)
        if len(self._last_positions) > 3:
            self._last_positions.pop(0)
        return best

    # ---------- room target update ----------
    def _advance_ring(self):
        self.ring_ptr = (self.ring_ptr + 1) % len(RING)

    # ---------- suggestion ----------
    def choose_suggestion(self, room, game):
        # record visit
        if room not in self.visited_rooms:
            self.visited_rooms.add(room)
            if len(self.visited_rooms) == 9:
                self.visited_rooms.clear()
                self.cycle_counter += 1
        self._advance_ring()

        suspect = next(iter(self.unknown_suspects))
        weapon  = next(iter(self.unknown_weapons))
        self.must_exit_next_turn = True
        return suspect, weapon, room

    # ---------- accusation logic ----------
    def should_make_accusation(self, game):
        matrix = game.logic_engines[self.player_id]
        if matrix.envelope_complete():
            return True
        if (len(self.unknown_suspects) == len(self.unknown_weapons) ==
                len(self.unknown_rooms) == 1):
            return True
        return self.cycle_counter >= self.B

    def choose_accusation(self, game):
        matrix = game.logic_engines[self.player_id]
        forced = matrix.envelope_complete()
        if forced:
            return forced
        return (next(iter(self.unknown_suspects)),
                next(iter(self.unknown_weapons)),
                next(iter(self.unknown_rooms)))

    # ---------- callback for a card you see ----------
    def observe_card(self, card):
        self.unknown_suspects.discard(card)
        self.unknown_weapons .discard(card)
        self.unknown_rooms   .discard(card)
