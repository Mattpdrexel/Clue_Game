import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from Room import Room
from Constants import character_name_list, room_name_list, weapon_name_list

# Define colors for different elements - using brighter, more distinguished colors
COLORS = {
    'wall': '#000000',  # Black
    'empty': '#FFFFFF',  # White
    'entrance': '#FF8C00',  # Dark Orange
    'bonus': '#FF1493',  # Deep Pink
    'character': {
        'Miss Scarlet': '#FF0000',  # Bright Red
        'Colonel Mustard': '#FFD700',  # Gold
        'Mrs White': '#E0E0E0',  # Light Gray (instead of pure white for better visibility)
        'Reverend Green': '#32CD32',  # Lime Green
        'Mrs Peacock': '#1E90FF',  # Dodger Blue
        'Professor Plum': '#9400D3',  # Dark Violet
    },
    'weapon': '#C0C0C0',  # Silver (brighter than gray)
    'room': {
        'Study': '#9370DB',  # Medium Purple
        'Hall': '#FF6347',  # Tomato
        'Lounge': '#20B2AA',  # Light Sea Green
        'Dining Room': '#DAA520',  # Goldenrod
        'Kitchen': '#87CEFA',  # Light Sky Blue
        'Ball Room': '#FF69B4',  # Hot Pink
        'Conservatory': '#00CED1',  # Dark Turquoise
        'Billiard Room': '#3CB371',  # Medium Sea Green
        'Library': '#F4A460',  # Sandy Brown
        'Clue': '#FFFF00',  # Yellow (brighter than Lemon Chiffon)
    }
}

def generate_board_image_sequence(game, board_image_counter):
    """Generate a sequence of board images to show the game progression"""
    # Create a directory for the board images if it doesn't exist
    image_dir = "board_images"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
        print(f"Created directory '{image_dir}' for board images")

    # Generate a unique filename based on the counter
    filename = os.path.join(image_dir, f"clue_board_{board_image_counter:03d}.png")

    # Call display_board_image with the unique filename
    display_board_image(game, filename)

    # Return the incremented counter
    return board_image_counter + 1

def display_board_image(game, filename='clue_board.png'):
    """Generate an image representation of the board state.

    Args:
        game: The ClueGame instance (must expose mansion_board, char_board, weapon_dict, symbols, centre_row/col)
        filename (str): File path for the PNG that will be saved
    """
    # ------------------------------------------------------------------ #
    # 1. Build a textual board (board_df) labelled by cell category
    # ------------------------------------------------------------------ #
    board_df = pd.DataFrame(
        index=range(game.mansion_board.rows),
        columns=range(game.mansion_board.cols)
    )

    for r in range(game.mansion_board.rows):
        for c in range(game.mansion_board.cols):
            cell_type = game.mansion_board.get_cell_type(r, c)

            if cell_type == "out_of_bounds":
                board_df.iloc[r, c] = "wall"
            elif isinstance(cell_type, Room):
                board_df.iloc[r, c] = f"room_{cell_type.name}"
            elif cell_type and hasattr(cell_type, 'room_name'):
                board_df.iloc[r, c] = "entrance"
            elif cell_type == "bonus_card":
                board_df.iloc[r, c] = "bonus"
            else:
                board_df.iloc[r, c] = "empty"

            # Overlay characters (except those still in the 3×3 clue centre)
            char_name = game.char_board.get_cell_content(r, c)
            if char_name:
                in_center = (
                    abs(r - game.centre_row) <= 1 and
                    abs(c - game.centre_col) <= 1
                )
                if not in_center:
                    board_df.iloc[r, c] = f"character_{char_name}"

    # Overlay weapons (only those moved to a non-Clue room)
    for weapon_name, weapon in game.weapon_dict.items():
        if weapon.location and weapon.location != "Clue":
            room = game.mansion_board.room_dict[weapon.location]
            if room.room_entrance_list:
                r, c = room.room_entrance_list[0].row, room.room_entrance_list[0].column
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < game.mansion_board.rows and
                        0 <= nc < game.mansion_board.cols and
                        isinstance(game.mansion_board.get_cell_type(nr, nc), Room)):
                        board_df.iloc[nr, nc] = f"weapon_{weapon_name}"
                        break

    # ------------------------------------------------------------------ #
    # 2. Convert board_df to numeric matrix for colour-mapping
    # ------------------------------------------------------------------ #
    board_numeric = np.zeros((game.mansion_board.rows, game.mansion_board.cols))
    board_text    = [['' for _ in range(game.mansion_board.cols)]
                     for _ in range(game.mansion_board.rows)]

    cell_type_to_num = {"wall": 1, "entrance": 12, "bonus": 13, "empty": 0}
    room_to_num      = {name: i + 2  for i, name in enumerate(room_name_list)}
    char_to_num      = {name: i + 14 for i, name in enumerate(character_name_list)}
    weapon_to_num    = {name: 20     for name in weapon_name_list}

    for r in range(game.mansion_board.rows):
        for c in range(game.mansion_board.cols):
            cell_value = board_df.iloc[r, c]

            if cell_value == "wall":
                board_numeric[r, c] = cell_type_to_num["wall"]
            elif cell_value == "entrance":
                board_numeric[r, c] = cell_type_to_num["entrance"]
                board_text[r][c] = 'E'
            elif cell_value == "bonus":
                board_numeric[r, c] = cell_type_to_num["bonus"]
                board_text[r][c] = '?'
            elif cell_value == "empty":
                board_numeric[r, c] = cell_type_to_num["empty"]
            elif cell_value.startswith("room_"):
                room_name = cell_value[5:]
                board_numeric[r, c] = room_to_num[room_name]
                board_text[r][c] = ''
            elif cell_value.startswith("character_"):
                char_name = cell_value[10:]
                board_numeric[r, c] = char_to_num[char_name]
                # Use two letters for character initials (first and last name)
                name_parts = char_name.split()
                initials = name_parts[0][0] + name_parts[-1][0]
                board_text[r][c] = initials
            elif cell_value.startswith("weapon_"):
                weapon_name = cell_value[7:]
                board_numeric[r, c] = weapon_to_num[weapon_name]
                board_text[r][c] = game.symbols['weapon'](weapon_name)

    # ------------------------------------------------------------------ #
    # 3. Build custom colour-map (unchanged)
    # ------------------------------------------------------------------ #
    cmap_colors = [COLORS['empty'], COLORS['wall']]             # 0-1
    for room_name in room_name_list:                            # 2-11
        cmap_colors.append(COLORS['room'][room_name])
    cmap_colors.extend([COLORS['entrance'], COLORS['bonus']])   # 12-13
    for char_name in character_name_list:                       # 14-19
        cmap_colors.append(COLORS['character'][char_name])
    cmap_colors.append(COLORS['weapon'])                        # 20

    custom_cmap = mcolors.ListedColormap(cmap_colors)

    # ------------------------------------------------------------------ #
    # 4. Plot with *fixed* data range so colours don’t shift
    # ------------------------------------------------------------------ #
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(
        board_numeric,
        cmap=custom_cmap,
        interpolation='nearest',
        vmin=0,
        vmax=len(cmap_colors) - 1      # <-- fixes shifting colours
    )

    # Text overlays
    for r in range(game.mansion_board.rows):
        for c in range(game.mansion_board.cols):
            if board_text[r][c]:
                bg_val = board_numeric[r, c]
                text_color = 'white' if bg_val >= 14 or bg_val == 1 else 'black'
                ax.text(c, r, board_text[r][c],
                        ha='center', va='center', color=text_color, fontsize=8)

    # Add room name annotations with 50% transparency
    room_centers = {}
    room_cells = {}

    # First, collect all cells for each room
    for r in range(game.mansion_board.rows):
        for c in range(game.mansion_board.cols):
            cell_value = board_df.iloc[r, c]
            if cell_value.startswith("room_"):
                room_name = cell_value[5:]
                if room_name not in room_cells:
                    room_cells[room_name] = []
                room_cells[room_name].append((r, c))

    # Calculate the center of each room
    for room_name, cells in room_cells.items():
        if cells:
            avg_r = sum(r for r, _ in cells) / len(cells)
            avg_c = sum(c for _, c in cells) / len(cells)
            room_centers[room_name] = (avg_r, avg_c)

    # Add room name annotations
    for room_name, (r, c) in room_centers.items():
        ax.text(c, r, room_name, 
                ha='center', va='center', 
                color='black', fontsize=12, 
                fontweight='bold', alpha=0.5)  # 50% transparency

    # Grid, ticks, labels -----------------
    # Set grid lines at cell boundaries
    ax.set_xticks(np.arange(-0.5, game.mansion_board.cols, 1))
    ax.set_yticks(np.arange(-0.5, game.mansion_board.rows, 1))
    ax.grid(which='major', linestyle='-', color='k', linewidth=0.5)

    # Set tick labels at cell centers
    ax.set_xticks(np.arange(0, game.mansion_board.cols, 1), minor=True)
    ax.set_yticks(np.arange(0, game.mansion_board.rows, 1), minor=True)
    ax.set_xticklabels([str(i) for i in range(game.mansion_board.cols)], minor=True)
    ax.set_yticklabels([str(i) for i in range(game.mansion_board.rows)], minor=True)

    # Hide major tick labels (grid lines)
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # Format minor tick labels (cell centers)
    plt.setp(ax.get_xticklabels(minor=True), rotation=0, ha="center", va="top", fontsize=8)
    plt.setp(ax.get_yticklabels(minor=True), rotation=0, ha="right", va="center", fontsize=8)

    plt.title('Clue Game Board')

    # Add legend for characters only
    legend_elements = []
    for char_name in character_name_list:
        name_parts = char_name.split()
        initials = name_parts[0][0] + name_parts[-1][0]
        color = COLORS['character'][char_name]
        legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                         markerfacecolor=color, markersize=10, 
                                         label=f'{initials}: {char_name}'))

    # Add legend for weapons
    weapon_legend_elements = []
    for weapon_name in weapon_name_list:
        color = COLORS['weapon']
        weapon_legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                         markerfacecolor=color, markersize=10, 
                                         label=f'{game.symbols["weapon"](weapon_name)}: {weapon_name}'))

    # Place legends outside the plot
    ax.legend(handles=legend_elements + weapon_legend_elements, loc='upper left', 
              bbox_to_anchor=(1.05, 1), title="Characters & Weapons")

    plt.tight_layout()

    # ------------------------------------------------------------------ #
    # 5. Save files
    # ------------------------------------------------------------------ #
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

    board_df.to_csv(filename.replace('.png', '.csv'))
    print(f"Board image saved as {filename}")
