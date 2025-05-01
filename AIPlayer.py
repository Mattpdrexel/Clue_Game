from Player import Player
from Constants import SUSPECTS, WEAPONS, ROOMS, ALL_CARDS
import random

class AIPlayer(Player):
    """
    An AI player that uses deduction to make decisions.
    """
    def __init__(self, player_id, character):
        super().__init__(player_id, character)
        self.target_room = None  # The room the AI is trying to reach
        self.last_suggestion = None  # The last suggestion made by this AI
        self.last_suggestion_room = None  # The room where the last suggestion was made
        self.game_state_log = []  # Log of game states for analysis
        self.past_suggestion_rooms = set()  # Set of rooms where suggestions have been made

    def choose_move(self, valid_moves, game):
        """
        Choose a move from the list of valid moves.

        Args:
            valid_moves: List of valid moves (row, col) tuples
            game: The game instance

        Returns:
            The chosen move as a (row, col) tuple
        """
        if not valid_moves:
            return None

        if getattr(self, "must_exit_next_turn", False):
            self.must_exit_next_turn = False
            door_moves = [m for m in valid_moves
                          if game.mansion_board.get_cell_type(m[0], m[1]) and hasattr(game.mansion_board.get_cell_type(m[0], m[1]), 'room_name')]
            if door_moves:
                return random.choice(door_moves)

        if self.target_room is None:
            self.target_room = self._choose_target_room(
                game.logic_engines[self.player_id], game
            )

        entrances = game.mansion_board.room_dict[self.target_room].room_entrance_list
        goals = {(e.row, e.column) for e in entrances}

        # Greedy − pick the legal step with lowest Manhattan distance to ANY goal
        best = min(valid_moves,
                   key=lambda m: min(abs(m[0]-r)+abs(m[1]-c) for r, c in goals))
        return best

    def _choose_target_room(self, matrix, game):
        """
        Choose a target room based on deduction.

        Args:
            matrix: The deduction matrix for this player
            game: The game instance

        Returns:
            The name of the target room
        """
        if matrix and matrix.envelope_complete():
            return "Clue"
        unseen = [r for r in ROOMS if r not in self.past_suggestion_rooms]
        return random.choice(unseen) if unseen else random.choice(ROOMS)

    def choose_suggestion(self, room, game):
        """
        Choose a suggestion to make in the given room.

        Args:
            room: The name of the room
            game: The game instance

        Returns:
            A tuple of (suspect, weapon, room)
        """
        matrix = game.logic_engines[self.player_id]

        unknown_suspects = [s for s in SUSPECTS if matrix.poss[s]["ENVELOPE"]]
        unknown_weapons  = [w for w in WEAPONS  if matrix.poss[w]["ENVELOPE"]]

        suspect = random.choice(unknown_suspects) if unknown_suspects else random.choice(SUSPECTS)
        weapon  = random.choice(unknown_weapons)  if unknown_weapons  else random.choice(WEAPONS)

        self.past_suggestion_rooms.add(room)
        self.last_suggestion_room = room
        return suspect, weapon, room

    def should_make_accusation(self, game):
        """
        Decide whether to make an accusation.

        Args:
            game: The game instance

        Returns:
            True if the AI should make an accusation, False otherwise
        """
        # Get the deduction matrix for this player
        matrix = game.logic_engines[self.player_id]

        # Check if we can deduce the solution
        envelope_solution = matrix.envelope_complete()
        if envelope_solution:
            # If we know the solution, make an accusation
            return True

        # Otherwise, don't make an accusation
        return False

    def choose_accusation(self, game):
        """
        Choose an accusation to make.

        Args:
            game: The game instance

        Returns:
            A tuple of (suspect, weapon, room)
        """
        # Get the deduction matrix for this player
        matrix = game.logic_engines[self.player_id]

        # Check if we can deduce the solution
        envelope_solution = matrix.envelope_complete()
        if envelope_solution:
            # If we know the solution, make an accusation
            return envelope_solution

        # If we can't deduce the solution, we shouldn't be making an accusation
        # But if we must, make an educated guess
        possible_envelope_suspects = [s for s in SUSPECTS if matrix.poss[s]["ENVELOPE"]]
        possible_envelope_weapons = [w for w in WEAPONS if matrix.poss[w]["ENVELOPE"]]
        possible_envelope_rooms = [r for r in ROOMS if matrix.poss[r]["ENVELOPE"]]

        suspect = random.choice(possible_envelope_suspects) if possible_envelope_suspects else random.choice(SUSPECTS)
        weapon = random.choice(possible_envelope_weapons) if possible_envelope_weapons else random.choice(WEAPONS)
        room = random.choice(possible_envelope_rooms) if possible_envelope_rooms else random.choice(ROOMS)

        return suspect, weapon, room

    def log_game_state(self, game):
        """
        Log the current game state for analysis.

        Args:
            game: The game instance
        """
        # Get the deduction matrix for this player
        matrix = game.logic_engines[self.player_id]

        # Create a snapshot of the current game state
        state = {
            'turn': len(self.game_state_log) + 1,
            'player_id': self.player_id,
            'character': self.character.name,
            'position': self.character.position,
            'hand': self.hand.copy(),
            'eliminated': self.eliminated,
            'target_room': self.target_room,
            'last_suggestion': self.last_suggestion,
            'last_suggestion_room': self.last_suggestion_room,
            'deduction_matrix': {
                'suspects': {s: {h: matrix.poss[s][h] for h in matrix.holders} for s in SUSPECTS},
                'weapons': {w: {h: matrix.poss[w][h] for h in matrix.holders} for w in WEAPONS},
                'rooms': {r: {h: matrix.poss[r][h] for h in matrix.holders} for r in ROOMS}
            },
            'envelope_complete': matrix.envelope_complete()
        }

        # Add the state to the log
        self.game_state_log.append(state)
