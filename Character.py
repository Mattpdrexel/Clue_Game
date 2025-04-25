from Constants import character_name_list

class Character:
    def __init__(self, name):
        self.name = name
        self.position = None  # Starting position will be decided by the player through the game

    def move_to(self, new_position):
        self.position = new_position

    def __repr__(self):
        return f"{self.name} at {self.position}"

character_dict = {name : Character(name) for name in character_name_list}