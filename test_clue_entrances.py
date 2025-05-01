from game import ClueGame
from Room import Room

# Create a game instance with visualization disabled for testing
game = ClueGame(enable_visualization=False)

# Get the Clue room
clue_room = game.mansion_board.room_dict["Clue"]

# Print the entrances of the Clue room
print("Clue room entrances:")
for entrance in clue_room.room_entrance_list:
    print(f"({entrance.row}, {entrance.column})")

# Print the valid moves when exiting the Clue room with 1 step
player = game.players[0]
steps = 1

# Find a cell in the Clue room
clue_cell = None
for r in range(game.mansion_board.rows):
    for c in range(game.mansion_board.cols):
        cell_type = game.mansion_board.get_cell_type(r, c)
        if isinstance(cell_type, Room) and cell_type.name == "Clue":
            clue_cell = (r, c)
            break
    if clue_cell:
        break

print(f"Clue cell: {clue_cell}")

# Move player to the Clue room
player.character.move_to(clue_cell)
game.char_board.move(player.character.name, clue_cell[0], clue_cell[1])

# Get valid moves
valid_moves = game.get_valid_moves(player, steps)

print(f"Valid moves when exiting the Clue room with {steps} step:")
for i, move in enumerate(valid_moves):
    print(f"{i+1}. {move}")

# Check if the valid moves are actually reachable within 1 step from any entrance
print("\nChecking if valid moves are reachable within 1 step from any entrance:")
for move in valid_moves:
    min_distance = float('inf')
    closest_entrance = None
    for entrance in clue_room.room_entrance_list:
        entrance_pos = (entrance.row, entrance.column)
        distance = abs(move[0] - entrance_pos[0]) + abs(move[1] - entrance_pos[1])
        if distance < min_distance:
            min_distance = distance
            closest_entrance = entrance_pos
    print(f"Move {move} is {min_distance} steps away from entrance {closest_entrance}")
