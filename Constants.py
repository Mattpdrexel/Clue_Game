character_name_list = [
    "Miss Scarlet", "Colonel Mustard", "Mrs White",
    "Reverend Green", "Mrs Peacock", "Professor Plum"
]

weapon_name_list = [
    "Candlestick", "Lead Pipe", "Wrench",
    "Knife", "Revolver", "Rope"
]

room_name_list = [
    "Study", "Hall", "Lounge", "Dining Room", "Kitchen",
    "Ball Room", "Conservatory", "Billiard Room", "Library",
    "Clue"          # central room
]

# Secret passages between rooms (diagonally opposite rooms)
SECRET_PASSAGES = {
    "Study": "Kitchen",
    "Kitchen": "Study",
    "Lounge": "Conservatory",
    "Conservatory": "Lounge"
}

# Bonus card types
BONUS_CARD_TYPES = [
    "Extra Turn",
    "See A Card",
    "Move Any Character",
    "Teleport",
    "Peek At Envelope"
]

# convenience groups
SUSPECTS = character_name_list
WEAPONS  = weapon_name_list
ROOMS    = [r for r in room_name_list if r != "Clue"]

ALL_CARDS = SUSPECTS + WEAPONS + ROOMS
