from Character import Character

class Player:
    def __init__(self, player_id, character: Character):
        self.player_id   = player_id       # e.g. seat number or user name
        self.character   = character       # reference to the board character
        self.hand        = []              # dealt cards
        self.eliminated  = False           # set True after wrong accusation
        self.notes_sheet = {}              # optional: deduction data
        self.bonus_cards = []              # bonus cards the player has drawn
        self.extra_turn  = False           # whether the player gets an extra turn
        self.must_exit_next_turn = False   # whether the player must exit a room next turn

    def add_card(self, card):
        self.hand.append(card)

    def add_bonus_card(self, bonus_card):
        """Add a bonus card to the player's hand"""
        self.bonus_cards.append(bonus_card)

    def use_bonus_card(self, index, game):
        """Use a bonus card from the player's hand"""
        if 0 <= index < len(self.bonus_cards):
            card = self.bonus_cards.pop(index)
            return card.play(game, self)
        return "Invalid bonus card index"

    def reveal_if_matches(self, cards_in_suggestion):
        for c in cards_in_suggestion:
            if c in self.hand:
                return c
        return None

# Player can move their character manhattan distance to objective
# Need to determine sub objectives along the way (like which room to go in)
