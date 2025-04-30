from Constants import room_name_list
from Room import Room

class CharacterBoard:
    def __init__(self, rows, cols):
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.positions = {}   # name → (row, col)

    # -------- basic API --------
    def place(self, name, row, col):
        if self.grid[row][col] is not None:
            raise ValueError(f"Cell ({row},{col}) already occupied")
        self.grid[row][col] = name
        self.positions[name] = (row, col)

    def move(self, name, new_row, new_col):
        old_row, old_col = self.positions[name]
        self.grid[old_row][old_col] = None
        self.place(name, new_row, new_col)

    def get_cell_content(self, row, col):
        return self.grid[row][col]      # character name or None



class MansionBoard:
    def __init__(self, board_layout):
        self.grid = board_layout.fillna("").to_numpy()
        self.rows, self.cols = self.grid.shape
        self.room_dict = {name: Room(name) for name in room_name_list}
        self.bonus_card_spaces = []  # List of (row, col) tuples for bonus card spaces
        self._scan_for_entrances()
        self._setup_secret_passages()

    def _setup_secret_passages(self):
        """Set up secret passages between rooms"""
        from Constants import SECRET_PASSAGES
        for source_room, dest_room in SECRET_PASSAGES.items():
            if source_room in self.room_dict and dest_room in self.room_dict:
                self.room_dict[source_room].add_secret_passage(dest_room)

    def _scan_for_entrances(self):
        for r in range(self.rows):
            for c in range(self.cols):
                val = str(self.grid[r][c])
                if val.endswith("_e"):
                    room_name = val.replace("_e", "")
                    if room_name in self.room_dict:
                        self.room_dict[room_name].add_room_entrance(r, c)
                elif val == "?":
                    # This is a bonus card space
                    self.bonus_card_spaces.append((r, c))

    def get_cell_type(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return "out_of_bounds"

        val = str(self.grid[r][c])

        if val in room_name_list:
            return self.room_dict[val]
        elif val.endswith("_e"):
            room_name = val.replace("_e", "")
            if room_name in self.room_dict:
                room = self.room_dict[room_name]
                return room.get_room_entrance_from_cell(r, c)
        elif val == "?":
            return "bonus_card"
        else:
            return None

    def is_bonus_card_space(self, r, c):
        """Check if a cell is a bonus card space"""
        return (r, c) in self.bonus_card_spaces


# Get what is currently in cell

# Update cell value

# What could be in a cell
# Out of bounds
# Room (has property, room entrance)
# Character
# ?
