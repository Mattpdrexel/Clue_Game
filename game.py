import random
import pandas as pd
import os
import csv
from Board import MansionBoard, CharacterBoard
from Character import character_dict
from Weapon import Weapon
from Player import Player
from Room import Room
from Constants import *
from DeductionMatrix import PossibilityMatrix
from BonusCard import BonusCard
from SuggestionHistory import SuggestionHistory
from DeductionViewer import DeductionViewer
import visualization

class ClueGame:
    def __init__(self, num_players=3, use_ai_players=False, log_to_csv=False, enable_visualization=True, ai_class=None, num_human=None):
        # ---------- load boards ----------
        self.mansion_layout = pd.read_excel("mansion_board_layout.xlsx", header=None)
        self.mansion_board = MansionBoard(self.mansion_layout)
        self.char_board = CharacterBoard(self.mansion_board.rows, self.mansion_board.cols)
        self.turn_counter = 0
        self.max_turns = None

        # Board visualization symbols
        self.symbols = {
            'empty': '·',
            'wall': '█',
            'room': ' ',
            'entrance': '▢',
            'bonus': '?',
            'character': lambda name: name[0].upper(),
            'weapon': lambda name: name[:3].lower()
        }

        # Counter for board image sequence
        self.board_image_counter = 0

        # Visualization control flag
        self.enable_visualization = enable_visualization

        # Clear board_images directory at game start if visualization is enabled
        if self.enable_visualization:
            image_dir = "board_images"
            if os.path.exists(image_dir):
                for file in os.listdir(image_dir):
                    file_path = os.path.join(image_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                print(f"Cleared directory '{image_dir}' for board images")

        # Game options
        self.use_ai_players = use_ai_players or ai_class is not None or (num_human is not None and num_human == 0)
        self.log_to_csv = log_to_csv

        # ---------- characters & players ----------
        self.players = []

        # Handle num_human parameter (overrides num_players)
        if num_human is not None:
            num_players = num_human

        # Ensure num_players is at least 3 (minimum required for a game)
        num_players = max(3, num_players)

        if self.use_ai_players:
            # Use specified AI class if provided, otherwise use default AIPlayer
            if ai_class is not None:
                for i, name in enumerate(SUSPECTS[:num_players]):
                    self.players.append(ai_class(i, character_dict[name]))
            else:
                # Import AIPlayer here to avoid circular imports
                from AIPlayer import AIPlayer
                for i, name in enumerate(SUSPECTS[:num_players]):
                    self.players.append(AIPlayer(i, character_dict[name]))
        else:
            for i, name in enumerate(SUSPECTS[:num_players]):
                self.players.append(Player(i, character_dict[name]))

        # place *all* 6 tokens around the centre (row 10,11 picked arbitrarily)
        self.centre_row, self.centre_col = 10, 11
        # Place characters in a circle around the center
        positions = [
            (self.centre_row - 1, self.centre_col),     # North
            (self.centre_row - 1, self.centre_col + 1), # Northeast
            (self.centre_row, self.centre_col + 1),     # East
            (self.centre_row + 1, self.centre_col + 1), # Southeast
            (self.centre_row + 1, self.centre_col),     # South
            (self.centre_row + 1, self.centre_col - 1)  # Southwest
        ]
        for char, pos in zip(character_dict.values(), positions):
            char.position = pos
            self.char_board.place(char.name, pos[0], pos[1])

        # ---------- weapons ----------
        self.weapon_dict = {w: Weapon(w) for w in weapon_name_list}
        # Place all weapons in the center (Clue room) initially
        for w in self.weapon_dict.values():
            w.location = "Clue"

        # ---------- secret envelope ----------
        self.solution = {
            "suspect": random.choice(SUSPECTS),
            "weapon": random.choice(WEAPONS),
            "room": random.choice(ROOMS)
        }

        # remove those cards and deal the rest
        deck = [c for c in ALL_CARDS if c not in self.solution.values()]
        random.shuffle(deck)

        for idx, card in enumerate(deck):
            player = self.players[idx % len(self.players)]
            player.add_card(card)
            # Call observe_card if the player has this method
            if hasattr(player, 'observe_card'):
                player.observe_card(card)

        # ---------- build deduction matrices (one per player) ----------
        self.logic_engines = {
            p.player_id: PossibilityMatrix(len(self.players), p.player_id, p.hand)
            for p in self.players
        }

        # Game state
        self.current_player_idx = 0
        self.game_over = False
        self.winner = None

        # Suggestion history
        self.suggestion_history = SuggestionHistory()

        # CSV logging setup
        if log_to_csv:
            self.game_log_file = "game_log.csv"
            self.deduction_log_file = "deduction_log.csv"

            # Initialize game log file
            with open(self.game_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Turn', 'Player ID', 'Character', 'Position', 'Action', 
                    'Target Room', 'Suggestion Suspect', 'Suggestion Weapon', 
                    'Suggestion Room', 'Refuted By', 'Card Shown'
                ])

            # Initialize deduction log file
            with open(self.deduction_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                header = ['Turn', 'Player ID', 'Character']

                # Add columns for each card and holder combination
                for card in ALL_CARDS:
                    for holder in ['ENVELOPE'] + [f'P{i}' for i in range(num_players)]:
                        header.append(f'{card}_{holder}')

                writer.writerow(header)

        print("Setup complete ✅")
        print("Secret envelope (hidden to players):", self.solution)

        # Display each player's starting hand
        for player in self.players:
            print(f"\n{player.character.name}'s starting hand:")
            self.display_player_hand(player)

    def roll_dice(self):
        """Simulate rolling a six-sided die"""
        return random.randint(1, 6)

    def get_valid_moves(self, player, steps):
        """Get valid moves for a player given the number of steps"""
        valid_moves = []
        valid_moves_set = set()  # Use a set to track unique positions
        current_pos = player.character.position

        # Check if this is the first move (character is in the center)
        is_first_move = (current_pos[0] == self.centre_row or current_pos[0] == self.centre_row - 1 or 
                         current_pos[0] == self.centre_row + 1) and (
                         current_pos[1] == self.centre_col or current_pos[1] == self.centre_col - 1 or 
                         current_pos[1] == self.centre_col + 1)

        # Check if the player is in a room
        cell_type = self.mansion_board.get_cell_type(current_pos[0], current_pos[1])
        is_in_room = isinstance(cell_type, Room)
        current_room = cell_type if is_in_room else None

        # Check if the player is on a room entrance
        is_on_entrance = cell_type and hasattr(cell_type, 'room_name')
        if is_on_entrance:
            # If on a room entrance, get the room
            room_name = cell_type.room_name
            current_room = self.mansion_board.room_dict[room_name]
            is_in_room = True

        # For the first move or when exiting a room, allow starting from any entrance and then moving steps from there
        if is_first_move or is_in_room:
            if is_in_room:
                print(f"Exiting {current_room.name}: You can exit from any entrance of this room!")
                # When exiting a room, only allow starting from entrances of the current room
                rooms_to_check = [(current_room.name, current_room)]

                # If the player is in the Clue room and has enough steps, allow moving directly to adjacent rooms
                if current_room.name == "Clue" and steps >= 2:
                    # Add entrances of other rooms as valid moves only if they're actually reachable within the number of steps
                    for other_room_name, other_room in self.mansion_board.room_dict.items():
                        if other_room_name != "Clue":
                            for entrance in other_room.room_entrance_list:
                                entrance_pos = (entrance.row, entrance.column)
                                # Check if the entrance is not occupied by another character
                                if self.char_board.get_cell_content(entrance_pos[0], entrance_pos[1]) is None:
                                    # Check if this entrance is actually reachable within the number of steps
                                    # Calculate the minimum Manhattan distance from any Clue room entrance
                                    min_distance = float('inf')
                                    for clue_entrance in current_room.room_entrance_list:
                                        clue_entrance_pos = (clue_entrance.row, clue_entrance.column)
                                        distance = abs(entrance_pos[0] - clue_entrance_pos[0]) + abs(entrance_pos[1] - clue_entrance_pos[1])
                                        min_distance = min(min_distance, distance)

                                    # Only add this entrance if it's reachable within the number of steps
                                    if min_distance <= steps and entrance_pos not in valid_moves_set:
                                        valid_moves.append(entrance_pos)
                                        valid_moves_set.add(entrance_pos)
            else:
                print("First move: You can start from any entrance and move from there!")
                # For the first move, allow starting from any entrance
                rooms_to_check = self.mansion_board.room_dict.items()

            # For each entrance, calculate valid moves after exiting
            for room_name, room in rooms_to_check:
                for entrance in room.room_entrance_list:
                    entrance_pos = (entrance.row, entrance.column)
                    # Check if the entrance is not occupied by another character
                    if self.char_board.get_cell_content(entrance_pos[0], entrance_pos[1]) is None:
                        # Calculate moves from this entrance
                        # For the first move, we should only be able to move 'steps' away from the entrance
                        visited = {entrance_pos}
                        queue = [(entrance_pos, steps)]

                        # Use BFS to find all reachable cells within the given number of steps
                        # This ensures that we can only move 'steps' away from the entrance

                        while queue:
                            (row, col), remaining_steps = queue.pop(0)

                            # If we've used all steps, this is a valid destination
                            if remaining_steps == 0:
                                # Check if the destination is not occupied by another character
                                if self.char_board.get_cell_content(row, col) is None:
                                    # Ensure we're not adding diagonal moves
                                    # Calculate Manhattan distance from entrance
                                    manhattan_dist = abs(row - entrance_pos[0]) + abs(col - entrance_pos[1])
                                    # Check if the destination is not within the same room as the player's current position
                                    dest_cell_type = self.mansion_board.get_cell_type(row, col)
                                    is_dest_in_room = isinstance(dest_cell_type, Room)
                                    if manhattan_dist <= steps and not is_dest_in_room and (row, col) not in valid_moves_set:
                                        valid_moves.append((row, col))
                                        valid_moves_set.add((row, col))
                                continue

                            # Try all four directions (no diagonal movement)
                            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                new_row, new_col = row + dr, col + dc

                                # Check if the new position is valid
                                if 0 <= new_row < self.mansion_board.rows and 0 <= new_col < self.mansion_board.cols:
                                    cell_type = self.mansion_board.get_cell_type(new_row, new_col)

                                    # Can move to empty cells or room entrances, but not walls
                                    if cell_type is None or hasattr(cell_type, 'room_name'):
                                        # Check if the cell is not occupied by another character
                                        if (new_row, new_col) not in visited and (
                                            self.char_board.get_cell_content(new_row, new_col) is None or 
                                            (new_row, new_col) == entrance_pos
                                        ):
                                            visited.add((new_row, new_col))
                                            queue.append(((new_row, new_col), remaining_steps - 1))

            return valid_moves

        # Normal movement for subsequent turns
        # Simple BFS to find valid moves
        queue = [(current_pos, steps)]
        visited = {current_pos}
        room_entrances_found = []  # Track room entrances found during BFS

        while queue:
            (row, col), remaining_steps = queue.pop(0)

            # If we've used all steps, this is a valid destination
            if remaining_steps == 0:
                # Check if the destination is already occupied by another character
                if self.char_board.get_cell_content(row, col) is None or (row, col) == current_pos:
                    # Ensure we're not adding diagonal moves
                    # Calculate Manhattan distance from current position
                    manhattan_dist = abs(row - current_pos[0]) + abs(col - current_pos[1])
                    if manhattan_dist <= steps and (row, col) not in valid_moves_set:
                        valid_moves.append((row, col))
                        valid_moves_set.add((row, col))
                continue

            # Try all four directions (no diagonal movement)
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_row, new_col = row + dr, col + dc

                # Check if the new position is valid
                if 0 <= new_row < self.mansion_board.rows and 0 <= new_col < self.mansion_board.cols:
                    cell_type = self.mansion_board.get_cell_type(new_row, new_col)

                    # Check if this is a room entrance
                    is_room_entrance = cell_type and hasattr(cell_type, 'room_name')

                    # If it's a room entrance, check if it's actually reachable within the number of steps
                    if is_room_entrance and (new_row, new_col) not in room_entrances_found:
                        if self.char_board.get_cell_content(new_row, new_col) is None:
                            # Calculate Manhattan distance from current position
                            manhattan_dist = abs(new_row - current_pos[0]) + abs(new_col - current_pos[1])
                            # Only add this entrance if it's reachable within the number of steps
                            if manhattan_dist <= steps and (new_row, new_col) not in valid_moves_set:
                                valid_moves.append((new_row, new_col))
                                valid_moves_set.add((new_row, new_col))
                                room_entrances_found.append((new_row, new_col))

                    # Can move to empty cells or room entrances, but not walls
                    if cell_type is None or hasattr(cell_type, 'room_name'):
                        # Check if the cell is not occupied by another character
                        if (new_row, new_col) not in visited and (
                            self.char_board.get_cell_content(new_row, new_col) is None or 
                            (new_row, new_col) == current_pos
                        ):
                            visited.add((new_row, new_col))
                            queue.append(((new_row, new_col), remaining_steps - 1))

        return valid_moves

    def move_player(self, player, new_position):
        """Move a player to a new position"""
        # Check if the new position is a room entrance
        cell_type = self.mansion_board.get_cell_type(new_position[0], new_position[1])
        is_room_entrance = cell_type and hasattr(cell_type, 'room_name')

        if is_room_entrance:
            # If entering a room, distribute to any empty space within the room
            room_name = cell_type.room_name
            current_room = self.mansion_board.room_dict[room_name]

            # Find an available cell in the room to place the character
            found_cell = False
            for r in range(self.mansion_board.rows):
                for c in range(self.mansion_board.cols):
                    # Check if this cell is in the same room and is not occupied
                    cell_type = self.mansion_board.get_cell_type(r, c)
                    if (isinstance(cell_type, Room) and cell_type.name == current_room.name and 
                        self.char_board.get_cell_content(r, c) is None):
                        # Found an empty cell in the room
                        player.character.move_to((r, c))
                        self.char_board.move(player.character.name, r, c)
                        found_cell = True
                        break
                if found_cell:
                    break

            # If no empty cell was found, just place at the entrance
            if not found_cell:
                player.character.move_to(new_position)
                self.char_board.move(player.character.name, new_position[0], new_position[1])
        else:
            # Normal movement
            player.character.move_to(new_position)
            self.char_board.move(player.character.name, new_position[0], new_position[1])

    def make_suggestion(self, player, suspect, weapon, room):
        """Make a suggestion and get responses"""
        # Move the suggested character and weapon to the room
        suggested_char = character_dict[suspect]

        # Get the current room
        current_pos = player.character.position
        cell_type = self.mansion_board.get_cell_type(current_pos[0], current_pos[1])
        current_room = None

        if isinstance(cell_type, Room):
            current_room = cell_type

            # Additional safeguard: Prevent suggestions in the Clue room
            if current_room.name == "Clue":
                print("Error: Suggestions cannot be made in the Clue room.")
                return None, None

            # Find an available cell in the room to place the suggested character
            found_cell = False
            for r in range(self.mansion_board.rows):
                for c in range(self.mansion_board.cols):
                    # Check if this cell is in the same room and is not occupied
                    cell_type = self.mansion_board.get_cell_type(r, c)
                    if (isinstance(cell_type, Room) and cell_type.name == current_room.name and 
                        self.char_board.get_cell_content(r, c) is None):
                        # Found an empty cell in the room
                        suggested_char.move_to((r, c))
                        self.char_board.move(suggested_char.name, r, c)
                        found_cell = True
                        break
                if found_cell:
                    break

            # If no empty cell was found, just update the character's position without moving on the board
            if not found_cell:
                suggested_char.move_to(player.character.position)
                print(f"Could not move {suspect} to an empty cell in the {current_room.name}. Character position updated but not moved on board.")
        else:
            # This shouldn't happen as suggestions should only be made in rooms
            print(f"Error: Suggestion made outside a room at position {current_pos}")

        self.weapon_dict[weapon].move_to(room)

        # Add the suggestion to the history
        suggestion = self.suggestion_history.add_suggestion(player.player_id, suspect, weapon, room)

        # Check if any player can disprove the suggestion
        for i in range(len(self.players)):
            # Start with the player to the left
            idx = (self.current_player_idx + i + 1) % len(self.players)
            other_player = self.players[idx]

            if other_player.player_id != player.player_id and not other_player.eliminated:
                revealed_card = other_player.reveal_if_matches([suspect, weapon, room])
                if revealed_card:
                    # Update the player's deduction matrix
                    self.logic_engines[player.player_id].set_holder(revealed_card, f"P{other_player.player_id}")

                    # Record the refutation in the suggestion history
                    suggestion.refute(other_player.player_id, revealed_card)

                    # Call observe_card if the player has this method
                    if hasattr(player, 'observe_card'):
                        player.observe_card(revealed_card)

                    return other_player, revealed_card
                else:
                    # Record that this player couldn't refute the suggestion
                    # This is valuable information for deduction
                    cards_in_suggestion = [suspect, weapon, room]
                    for card in cards_in_suggestion:
                        self.logic_engines[player.player_id].eliminate(card, f"P{other_player.player_id}")

        # If no one could refute, this is valuable information
        # All cards in the suggestion might be in the envelope
        cards_in_suggestion = [suspect, weapon, room]
        for card in cards_in_suggestion:
            # Check if this card is already known to be with a player
            if not any(self.logic_engines[player.player_id].poss[card][f"P{p.player_id}"] 
                      for p in self.players if p.player_id != player.player_id and not p.eliminated):
                # If not, it might be in the envelope
                # We don't set it definitively because one of the cards might be in the suggester's hand
                pass

        return None, None

    def make_accusation(self, player, suspect, weapon, room):
        """Make an accusation and check if it's correct"""
        if (suspect == self.solution["suspect"] and 
            weapon == self.solution["weapon"] and 
            room == self.solution["room"]):
            self.game_over = True
            self.winner = player
            return True
        else:
            player.eliminated = True
            # Check if all players are eliminated
            if all(p.eliminated for p in self.players):
                self.game_over = True
            return False

    def display_board(self):
        """Display the current state of the board using ASCII characters"""
        if not hasattr(self, 'enable_visualization') or not self.enable_visualization:
            return  # Skip visualization if disabled

        # Create a 2D grid to represent the board
        board_display = [[' ' for _ in range(self.mansion_board.cols)] for _ in range(self.mansion_board.rows)]

        # Fill in the basic board layout
        for r in range(self.mansion_board.rows):
            for c in range(self.mansion_board.cols):
                cell_type = self.mansion_board.get_cell_type(r, c)

                if cell_type == "out_of_bounds":
                    board_display[r][c] = self.symbols['wall']
                elif isinstance(cell_type, Room):
                    # Room cells are represented by the first letter of the room name
                    board_display[r][c] = cell_type.name[0]
                elif cell_type and hasattr(cell_type, 'room_name'):
                    # Room entrance
                    board_display[r][c] = self.symbols['entrance']
                elif cell_type == "bonus_card":
                    board_display[r][c] = self.symbols['bonus']
                else:
                    # Empty corridor
                    board_display[r][c] = self.symbols['empty']

                # Check if there's a character at this position
                char_name = self.char_board.get_cell_content(r, c)
                if char_name:
                    # Only show characters that have left the center area
                    is_in_center = (r == self.centre_row or r == self.centre_row - 1 or 
                                   r == self.centre_row + 1) and (
                                   c == self.centre_col or c == self.centre_col - 1 or 
                                   c == self.centre_col + 1)
                    if not is_in_center:
                        board_display[r][c] = self.symbols['character'](char_name)

        # Add weapon locations (simplified - just show in room centers)
        for weapon_name, weapon in self.weapon_dict.items():
            # Only show weapons that have been moved to a room other than "Clue" (the center)
            if weapon.location in self.mansion_board.room_dict and weapon.location != "Clue":
                room = self.mansion_board.room_dict[weapon.location]
                if room.room_entrance_list:
                    # Place weapon symbol near room entrance
                    r, c = room.room_entrance_list[0].row, room.room_entrance_list[0].column
                    # Try to find a nearby empty room cell
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.mansion_board.rows and 
                            0 <= nc < self.mansion_board.cols and
                            isinstance(self.mansion_board.get_cell_type(nr, nc), Room)):
                            board_display[nr][nc] = self.symbols['weapon'](weapon_name)
                            break

        # Print the board
        print("\n=== MANSION BOARD ===")
        # Add column numbers at the top
        print("   " + "".join(f"{c%10}" for c in range(self.mansion_board.cols)))
        for r in range(self.mansion_board.rows):
            # Add row numbers at the left
            print(f"{r:2d} " + "".join(board_display[r]))
        print("===================")

        # Print legend
        print("\nLegend:")
        print(f"{self.symbols['wall']} = Wall, {self.symbols['empty']} = Corridor, {self.symbols['entrance']} = Room Entrance, {self.symbols['bonus']} = Bonus Card")
        print("UPPERCASE = Character, lowercase = Weapon, Letters = Rooms")

        # Print character and weapon positions
        print("\nCharacters:")
        for name, char in character_dict.items():
            if char.position:
                # Only show characters that have left the center area
                is_in_center = (char.position[0] == self.centre_row or char.position[0] == self.centre_row - 1 or 
                               char.position[0] == self.centre_row + 1) and (
                               char.position[1] == self.centre_col or char.position[1] == self.centre_col - 1 or 
                               char.position[1] == self.centre_col + 1)
                if not is_in_center:
                    print(f"{name} ({self.symbols['character'](name)}) at {char.position}")
                else:
                    print(f"{name} is waiting to start")

        print("\nWeapons:")
        for name, weapon in self.weapon_dict.items():
            # Only show weapons that have been moved to a room other than "Clue" (the center)
            if weapon.location != "Clue":
                print(f"{name} ({self.symbols['weapon'](name)}) in {weapon.location}")
            else:
                print(f"{name} is waiting to be used")

        # Also generate an image representation
        self.generate_board_image_sequence()

    def generate_board_image_sequence(self):
        """Generate a sequence of board images to show the game progression"""
        # Only generate images if visualization is enabled
        if self.enable_visualization:
            # Call the visualization module's function
            self.board_image_counter = visualization.generate_board_image_sequence(self, self.board_image_counter)

    def display_suggestion_history(self):
        """Display the history of suggestions made during the game."""
        print(self.suggestion_history)

    def display_player_hand(self, player):
        """Display the cards in a player's hand."""
        if not player.hand:
            print("No cards in hand.")
            return

        # Group cards by type
        suspects = [card for card in player.hand if card in SUSPECTS]
        weapons = [card for card in player.hand if card in WEAPONS]
        rooms = [card for card in player.hand if card in ROOMS]

        # Display cards by type
        if suspects:
            print("Suspects:", ", ".join(suspects))
        if weapons:
            print("Weapons:", ", ".join(weapons))
        if rooms:
            print("Rooms:", ", ".join(rooms))

    def display_deduction_matrix(self, player):
        """Display a player's deduction matrix."""
        matrix = self.logic_engines[player.player_id]
        DeductionViewer.display_matrix(matrix, player.player_id)

    def next_turn(self):
        """Advance to the next player's turn"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        # Skip eliminated players
        while self.players[self.current_player_idx].eliminated:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def play_turn(self, player):
        """Play a turn for a player"""
        print(f"\n{player.character.name}'s turn")

        # Display the current board state
        self.display_board()

        # Check if player is in a room at the start of their turn
        current_pos = player.character.position
        cell_type = self.mansion_board.get_cell_type(current_pos[0], current_pos[1])
        current_room = None

        if isinstance(cell_type, Room):
            current_room = cell_type
            room_name = current_room.name
            print(f"You are in the {room_name}")

            # If the room has a secret passage, offer to use it
            if current_room.secret_passage_to:
                use_passage = input(f"Use secret passage to {current_room.secret_passage_to}? (y/n): ").lower() == 'y'
                if use_passage:
                    # Move to the connected room
                    dest_room = self.mansion_board.room_dict[current_room.secret_passage_to]
                    if dest_room.room_entrance_list:
                        new_pos = (dest_room.room_entrance_list[0].row, dest_room.room_entrance_list[0].column)
                        self.move_player(player, new_pos)
                        print(f"Moved to {current_room.secret_passage_to} via secret passage")
                        current_room = dest_room
                        room_name = current_room.name
                    else:
                        print(f"Could not use secret passage (no entrances found in {current_room.secret_passage_to})")

            # Ask if the player wants to stay in the room or roll and move
            stay_in_room = input("Stay in this room? (y/n): ").lower() == 'y'
            if stay_in_room:
                # Skip the movement phase
                print(f"Staying in the {room_name}")

                # Offer to view deduction information
                view_deductions = input("View deduction information? (y/n): ").lower() == 'y'
                if view_deductions:
                    # Show options for what to view
                    print("\nDeduction Options:")
                    print("1. View suggestion history")
                    print("2. View your deduction matrix")
                    print("3. View your cards in hand")
                    print("4. Back to game")

                    choice = input("Choose an option (1-4): ")
                    if choice == "1":
                        self.display_suggestion_history()
                    elif choice == "2":
                        self.display_deduction_matrix(player)
                    elif choice == "3":
                        self.display_player_hand(player)

                # Ask if the player wants to make a suggestion
                # Only allow suggestions in main rooms, not the Clue room
                if room_name == "Clue":
                    print("You cannot make a suggestion in the Clue room.")
                    make_suggestion = False
                else:
                    make_suggestion = input("Make a suggestion? (y/n): ").lower() == 'y'
                if make_suggestion:
                    # Get the suggestion details
                    print("Suspects:", SUSPECTS)
                    suspect = input("Choose a suspect: ")
                    print("Weapons:", WEAPONS)
                    weapon = input("Choose a weapon: ")

                    # Make the suggestion
                    responder, card = self.make_suggestion(player, suspect, weapon, room_name)

                    # Update the board display after suggestion (characters and weapons moved)
                    self.display_board()

                    if responder:
                        print(f"{responder.character.name} showed you {card}")
                    else:
                        print("No one could disprove your suggestion!")

                    # Set flag to force player to exit room next turn
                    player.must_exit_next_turn = True

                # Check for bonus cards
                if player.bonus_cards:
                    use_bonus = input("Use a bonus card? (y/n): ").lower() == 'y'
                    if use_bonus:
                        print("Your bonus cards:")
                        for i, card in enumerate(player.bonus_cards):
                            print(f"{i+1}. {card}")

                        card_idx = int(input("Choose a card to use (number): ")) - 1
                        result = player.use_bonus_card(card_idx, self)
                        print(result)

                # Skip to accusation phase
                self.handle_accusation(player)

                # End the turn
                if player.extra_turn:
                    player.extra_turn = False
                    print(f"{player.character.name} gets an extra turn!")
                else:
                    self.next_turn()
                return

        # Normal turn with dice roll
        steps = self.roll_dice()
        print(f"Rolled a {steps}")

        # Get valid moves
        valid_moves = self.get_valid_moves(player, steps)

        # Ask player if they want to see the list of valid moves
        show_moves = input("Show list of valid moves? (y/n): ").lower() == 'y'
        if show_moves:
            print("Valid moves:")
            for i, move in enumerate(valid_moves):
                # Check if this move leads into a room
                cell_type = self.mansion_board.get_cell_type(move[0], move[1])
                is_room_entrance = cell_type and hasattr(cell_type, 'room_name')

                # Highlight room entrances
                if is_room_entrance:
                    room_name = cell_type.room_name
                    print(f"{i+1}. {move} [ROOM ENTRANCE: {room_name}]")
                else:
                    print(f"{i+1}. {move}")

        # Ask player if they want to enter coordinates or choose from the list
        choice_method = input("Enter coordinates directly (c) or choose from list (l)? ").lower()

        if choice_method == 'c':
            # Get coordinates from player
            while True:
                try:
                    coords_input = input("Enter coordinates as 'row,col' (e.g., '10,15'): ")
                    row, col = map(int, coords_input.split(','))

                    # Check if the coordinates are valid
                    if (row, col) in valid_moves:
                        new_position = (row, col)
                        break
                    else:
                        # Check if it's a room entrance that's reachable
                        cell_type = self.mansion_board.get_cell_type(row, col)
                        is_room_entrance = cell_type and hasattr(cell_type, 'room_name')

                        if is_room_entrance and self.char_board.get_cell_content(row, col) is None:
                            # Check if it's reachable (within steps of current position)
                            # This is a simplified check - in a real implementation, you'd need a proper pathfinding algorithm
                            manhattan_distance = abs(row - current_pos[0]) + abs(col - current_pos[1])
                            if manhattan_distance <= steps:
                                new_position = (row, col)
                                break

                        print(f"Invalid move. Coordinates ({row}, {col}) are not in the list of valid moves.")
                except ValueError:
                    print("Invalid input. Please enter coordinates as 'row,col'.")
        else:
            # Get player's choice from the list
            while True:
                try:
                    choice = int(input("Choose a move (number): ")) - 1
                    if 0 <= choice < len(valid_moves):
                        new_position = valid_moves[choice]
                        break
                    else:
                        print(f"Invalid choice. Please enter a number between 1 and {len(valid_moves)}.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

        # Move the player
        self.move_player(player, new_position)
        print(f"Moved to {new_position}")

        # Update the board display after movement
        self.display_board()

        # Check if the player landed on a bonus card space
        if self.mansion_board.is_bonus_card_space(new_position[0], new_position[1]):
            print("You landed on a bonus card space!")
            draw_card = input("Draw a bonus card? (y/n): ").lower() == 'y'
            if draw_card:
                bonus_card = BonusCard()
                print(f"You drew: {bonus_card}")

                if bonus_card.immediate:
                    # Play the card immediately
                    result = bonus_card.play(self, player)
                    print(result)

                    if bonus_card.card_type == "Extra Turn":
                        player.extra_turn = True
                else:
                    # Add to player's hand
                    player.add_bonus_card(bonus_card)

        # Check if the player is in a room or on a room entrance
        cell_type = self.mansion_board.get_cell_type(new_position[0], new_position[1])
        current_room = None

        # Check if the player is on a room entrance
        is_room_entrance = cell_type and hasattr(cell_type, 'room_name')
        if is_room_entrance:
            # If on a room entrance, get the room
            room_name = cell_type.room_name
            current_room = self.mansion_board.room_dict[room_name]
        elif isinstance(cell_type, Room):
            current_room = cell_type
            room_name = current_room.name

        # If the player is in a room or on a room entrance
        if current_room:
            print(f"You are in the {room_name}")

            # Offer to view deduction information
            view_deductions = input("View deduction information? (y/n): ").lower() == 'y'
            if view_deductions:
                # Show options for what to view
                print("\nDeduction Options:")
                print("1. View suggestion history")
                print("2. View your deduction matrix")
                print("3. View your cards in hand")
                print("4. Back to game")

                choice = input("Choose an option (1-4): ")
                if choice == "1":
                    self.display_suggestion_history()
                elif choice == "2":
                    self.display_deduction_matrix(player)
                elif choice == "3":
                    self.display_player_hand(player)

            # Ask if the player wants to make a suggestion
            make_suggestion = input("Make a suggestion? (y/n): ").lower() == 'y'
            if make_suggestion:
                # Get the suggestion details
                show_suspects = input("Show suspects list? (y/n): ").lower() == 'y'
                if show_suspects:
                    print("Suspects:", SUSPECTS)
                suspect = input("Choose a suspect: ")

                show_weapons = input("Show weapons list? (y/n): ").lower() == 'y'
                if show_weapons:
                    print("Weapons:", WEAPONS)
                weapon = input("Choose a weapon: ")

                # Make the suggestion
                responder, card = self.make_suggestion(player, suspect, weapon, room_name)

                # Update the board display after suggestion (characters and weapons moved)
                self.display_board()

                if responder:
                    print(f"{responder.character.name} showed you {card}")
                else:
                    print("No one could disprove your suggestion!")

                # Set flag to force player to exit room next turn
                player.must_exit_next_turn = True

        # Handle accusation phase
        self.handle_accusation(player)

        # End the turn
        if player.extra_turn:
            player.extra_turn = False
            print(f"{player.character.name} gets an extra turn!")
        else:
            self.next_turn()

    def handle_accusation(self, player):
        """Handle the accusation phase of a turn"""
        # Offer to view deduction information before making an accusation
        view_deductions = input("View deduction information before deciding on accusation? (y/n): ").lower() == 'y'
        if view_deductions:
            # Show options for what to view
            print("\nDeduction Options:")
            print("1. View suggestion history")
            print("2. View your deduction matrix")
            print("3. View your cards in hand")
            print("4. Back to game")

            choice = input("Choose an option (1-4): ")
            if choice == "1":
                self.display_suggestion_history()
            elif choice == "2":
                self.display_deduction_matrix(player)
            elif choice == "3":
                self.display_player_hand(player)

        # Ask if the player wants to make an accusation
        make_accusation = input("Make an accusation? (y/n): ").lower() == 'y'
        if make_accusation:
            # Check if player is in the center
            is_in_center = (player.character.position[0] == self.centre_row and 
                           player.character.position[1] == self.centre_col)

            if not is_in_center:
                # Ask if player wants to move to center
                move_to_center = input("You must be in the center to make an accusation. Move there now? (y/n): ").lower() == 'y'
                if move_to_center:
                    # Move to center
                    self.move_player(player, (self.centre_row, self.centre_col))
                    print(f"Moved to center at {self.centre_row}, {self.centre_col}")

                    # Update the board display after moving to center
                    self.display_board()
                else:
                    print("Accusation cancelled.")
                    return

            # Get the accusation details
            show_suspects = input("Show suspects list? (y/n): ").lower() == 'y'
            if show_suspects:
                print("Suspects:", SUSPECTS)
            suspect = input("Choose a suspect: ")

            show_weapons = input("Show weapons list? (y/n): ").lower() == 'y'
            if show_weapons:
                print("Weapons:", WEAPONS)
            weapon = input("Choose a weapon: ")

            show_rooms = input("Show rooms list? (y/n): ").lower() == 'y'
            if show_rooms:
                print("Rooms:", ROOMS)
            room = input("Choose a room: ")

            # Make the accusation
            correct = self.make_accusation(player, suspect, weapon, room)
            if correct:
                print("Correct! You win!")
            else:
                print("Wrong! You are eliminated from making accusations.")

    def play_ai_turn(self, player):
        """Play a turn for an AI player"""
        if self.enable_visualization:
            print(f"\n{player.character.name}'s turn (AI)")
            self.display_board()  # Only display if visualization is enabled

        # Log the game state if enabled
        if self.log_to_csv:
            self._log_game_state(player, "Start Turn")

        # Check if player is in a room at the start of their turn
        current_pos = player.character.position
        cell_type = self.mansion_board.get_cell_type(current_pos[0], current_pos[1])
        current_room = None

        if isinstance(cell_type, Room):
            current_room = cell_type
            room_name = current_room.name
            if self.enable_visualization:
                print(f"AI is in the {room_name}")

            # If the room has a secret passage, decide whether to use it
            if current_room.secret_passage_to:
                # AI logic: Use secret passage if it leads to a room we want to visit
                use_passage = current_room.secret_passage_to == player.target_room
                if use_passage:
                    # Move to the connected room
                    dest_room = self.mansion_board.room_dict[current_room.secret_passage_to]
                    if dest_room.room_entrance_list:
                        new_pos = (dest_room.room_entrance_list[0].row, dest_room.room_entrance_list[0].column)
                        self.move_player(player, new_pos)
                        if self.enable_visualization:
                            print(f"AI moved to {current_room.secret_passage_to} via secret passage")
                        current_room = dest_room
                        room_name = current_room.name
                    elif self.enable_visualization:
                        print(f"Could not use secret passage (no entrances found in {current_room.secret_passage_to})")

            # AI logic: Decide whether to stay in the room or roll and move
            # Stay if we want to make a suggestion in this room and it's not the Clue room
            stay_in_room = room_name != "Clue" and (player.target_room is None or room_name == player.target_room)
            if stay_in_room:
                # Skip the movement phase
                if self.enable_visualization:
                    print(f"AI staying in the {room_name}")

                # AI logic: Make a suggestion in this room
                # Double-check that we're not in the Clue room
                if room_name == "Clue":
                    if self.enable_visualization:
                        print("AI cannot make a suggestion in the Clue room.")
                    responder, card = None, None
                else:
                    suspect, weapon, room = player.choose_suggestion(room_name, self)
                    if self.enable_visualization:
                        print(f"AI suggests: {suspect} with {weapon} in {room_name}")

                    # Make the suggestion
                    responder, card = self.make_suggestion(player, suspect, weapon, room_name)

                    # Update the board display after suggestion (characters and weapons moved)
                    self.display_board()

                    # Log the suggestion if enabled
                    if self.log_to_csv:
                        self._log_game_state(player, "Suggestion", 
                                            suggestion_suspect=suspect, 
                                            suggestion_weapon=weapon, 
                                            suggestion_room=room_name,
                                            refuted_by=responder.player_id if responder else None,
                                            card_shown=card)

                    if self.enable_visualization:
                        if responder:
                            print(f"{responder.character.name} showed {card}")
                        else:
                            print("No one could disprove the suggestion!")

                # Set flag to force player to exit room next turn
                player.must_exit_next_turn = True

                # Skip to accusation phase
                self.handle_ai_accusation(player)

                # End the turn
                if player.extra_turn:
                    player.extra_turn = False
                    if self.enable_visualization:
                        print(f"{player.character.name} gets an extra turn!")
                else:
                    self.next_turn()
                return

        # Normal turn with dice roll
        steps = self.roll_dice()
        if self.enable_visualization:
            print(f"AI rolled a {steps}")

        # Get valid moves
        valid_moves = self.get_valid_moves(player, steps)

        # AI logic: Choose a move
        new_position = player.choose_move(valid_moves, self)
        if new_position:
            # Move the player
            self.move_player(player, new_position)
            if self.enable_visualization:
                print(f"AI moved to {new_position}")

            # Log the move if enabled
            if self.log_to_csv:
                self._log_game_state(player, "Move", target_room=player.target_room)

            # Update the board display after movement
            self.display_board()

            # Check if the player landed on a bonus card space
            if self.mansion_board.is_bonus_card_space(new_position[0], new_position[1]) and self.enable_visualization:
                print("AI landed on a bonus card space!")
                # AI logic: Always draw a bonus card
                bonus_card = BonusCard()
                if self.enable_visualization:
                    print(f"AI drew: {bonus_card}")

                if bonus_card.immediate:
                    # Play the card immediately
                    result = bonus_card.play(self, player)
                    if self.enable_visualization:
                        print(result)

                    if bonus_card.card_type == "Extra Turn":
                        player.extra_turn = True
                else:
                    # Add to player's hand
                    player.add_bonus_card(bonus_card)

            # Check if the player is in a room or on a room entrance
            cell_type = self.mansion_board.get_cell_type(new_position[0], new_position[1])
            current_room = None

            # Check if the player is on a room entrance
            is_room_entrance = cell_type and hasattr(cell_type, 'room_name')
            if is_room_entrance:
                # If on a room entrance, get the room
                room_name = cell_type.room_name
                current_room = self.mansion_board.room_dict[room_name]
            elif isinstance(cell_type, Room):
                current_room = cell_type
                room_name = current_room.name

            # If the player is in a room or on a room entrance (and it's not the Clue room)
            if current_room and room_name != "Clue":
                if self.enable_visualization:
                    print(f"AI is in the {room_name}")

                # AI logic: Make a suggestion in this room
                suspect, weapon, room = player.choose_suggestion(room_name, self)
                if self.enable_visualization:
                    print(f"AI suggests: {suspect} with {weapon} in {room_name}")

                # Make the suggestion
                responder, card = self.make_suggestion(player, suspect, weapon, room_name)

                # Update the board display after suggestion (characters and weapons moved)
                self.display_board()

                # Log the suggestion if enabled
                if self.log_to_csv:
                    self._log_game_state(player, "Suggestion", 
                                        suggestion_suspect=suspect, 
                                        suggestion_weapon=weapon, 
                                        suggestion_room=room_name,
                                        refuted_by=responder.player_id if responder else None,
                                        card_shown=card)

                if self.enable_visualization:
                    if responder:
                        print(f"{responder.character.name} showed {card}")
                    else:
                        print("No one could disprove the suggestion!")

                # Set flag to force player to exit room next turn
                player.must_exit_next_turn = True

        # Handle accusation phase
        self.handle_ai_accusation(player)

        # End the turn
        if player.extra_turn:
            player.extra_turn = False
            if self.enable_visualization:
                print(f"{player.character.name} gets an extra turn!")
        else:
            self.next_turn()

    def handle_ai_accusation(self, player):
        """Handle the accusation phase of a turn for an AI player"""
        # AI logic: Decide whether to make an accusation
        make_accusation = player.should_make_accusation(self)
        if make_accusation:
            # Check if player is in the center
            is_in_center = (player.character.position[0] == self.centre_row and 
                           player.character.position[1] == self.centre_col)

            if not is_in_center:
                # Move to center
                self.move_player(player, (self.centre_row, self.centre_col))
                if self.enable_visualization:
                    print(f"AI moved to center at {self.centre_row}, {self.centre_col}")

                # Update the board display after moving to center
                self.display_board()

            # AI logic: Choose an accusation
            suspect, weapon, room = player.choose_accusation(self)
            if self.enable_visualization:
                print(f"AI accuses: {suspect} with {weapon} in {room}")

            # Make the accusation
            correct = self.make_accusation(player, suspect, weapon, room)

            # Log the accusation if enabled
            if self.log_to_csv:
                self._log_game_state(player, "Accusation", 
                                    suggestion_suspect=suspect, 
                                    suggestion_weapon=weapon, 
                                    suggestion_room=room,
                                    refuted_by="Correct" if correct else "Incorrect")

            if self.enable_visualization:
                if correct:
                    print("Correct! AI wins!")
                else:
                    print("Wrong! AI is eliminated from making accusations.")

    def _log_game_state(self, player, action, target_room=None, suggestion_suspect=None, 
                       suggestion_weapon=None, suggestion_room=None, refuted_by=None, card_shown=None):
        """Log the current game state to CSV files"""
        if not self.log_to_csv:
            return

        # Log game action
        with open(self.game_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                len(player.game_state_log) + 1,  # Turn number
                player.player_id,
                player.character.name,
                player.character.position,
                action,
                target_room,
                suggestion_suspect,
                suggestion_weapon,
                suggestion_room,
                refuted_by,
                card_shown
            ])

        # Log deduction matrix state
        matrix = self.logic_engines[player.player_id]
        with open(self.deduction_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            row = [
                len(player.game_state_log) + 1,  # Turn number
                player.player_id,
                player.character.name
            ]

            # Add values for each card and holder combination
            for card in ALL_CARDS:
                for holder in ['ENVELOPE'] + [f'P{i}' for i in range(len(self.players))]:
                    row.append(1 if matrix.poss[card][holder] else 0)

            writer.writerow(row)

        # Also log to the player's internal state log
        if hasattr(player, 'log_game_state'):
            player.log_game_state(self)

    def run(self, max_turns=None):
        """Play the game until it's over or max_turns is reached"""
        if self.enable_visualization:
            print("\nStarting the game!")
            # Display the initial board state
            self.display_board()

        self.turn_counter = 0
        while not self.game_over:
            if max_turns is not None and self.turn_counter >= max_turns:
                print(f"\nReached maximum turns ({max_turns}). Ending game.")
                break

            current_player = self.players[self.current_player_idx]

            # Track player positions if track_positions attribute exists
            if hasattr(self, 'track_positions'):
                # Get current room name or None
                current_pos = current_player.character.position
                cell_type = self.mansion_board.get_cell_type(current_pos[0], current_pos[1])
                current_room = None

                if isinstance(cell_type, Room):
                    current_room = cell_type.name
                elif cell_type and hasattr(cell_type, 'room_name'):
                    current_room = cell_type.room_name

                self.track_positions.append((current_player.player_id, current_room))

            if self.use_ai_players:
                self.play_ai_turn(current_player)
            else:
                self.play_turn(current_player)

            self.turn_counter += 1

        if self.winner:
            print(f"\nGame over! {self.winner.character.name} wins!")
        else:
            print("\nGame over! All players eliminated. The solution was:")
            print(f"Suspect: {self.solution['suspect']}")
            print(f"Weapon: {self.solution['weapon']}")
            print(f"Room: {self.solution['room']}")

    def play_game(self):
        """Play the game until it's over (wrapper for run method)"""
        self.run()

    def play(self):
        """Play the game until it's over (wrapper for run method)"""
        self.run(self.max_turns)

    def replace_all_players(self, player_class):
        """Replace all players with instances of the given player class"""
        new_players = []
        for i, player in enumerate(self.players):
            new_player = player_class(i, player.character)
            # Copy the hand from the old player to the new player
            for card in player.hand:
                new_player.add_card(card)
                # Call observe_card if the player has this method
                if hasattr(new_player, 'observe_card'):
                    new_player.observe_card(card)
            new_players.append(new_player)

        self.players = new_players

        # Rebuild the logic engines for the new players
        self.logic_engines = {
            p.player_id: PossibilityMatrix(len(self.players), p.player_id, p.hand)
            for p in self.players
        }

        # Update use_ai_players flag based on the player class
        from AIPlayer import AIPlayer
        self.use_ai_players = issubclass(player_class, AIPlayer) or player_class.__name__ == "SimpleAIPlayer"

if __name__ == "__main__":
    game = ClueGame()
    game.play_game()
