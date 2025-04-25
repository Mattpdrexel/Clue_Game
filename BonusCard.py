import random
from Constants import BONUS_CARD_TYPES

class BonusCard:
    def __init__(self, card_type=None):
        """
        Initialize a bonus card with a specific type or random type
        
        Args:
            card_type (str, optional): The type of bonus card. If None, a random type is chosen.
        """
        self.card_type = card_type if card_type else random.choice(BONUS_CARD_TYPES)
        self.description = self._get_description()
        self.immediate = self._is_immediate()
        
    def _get_description(self):
        """Get the description of the bonus card based on its type"""
        descriptions = {
            "Extra Turn": "Take an extra turn after this one.",
            "See A Card": "Look at one card from any player's hand.",
            "Move Any Character": "Move any character to any room.",
            "Teleport": "Move your character to any room.",
            "Peek At Envelope": "Peek at one card in the envelope."
        }
        return descriptions.get(self.card_type, "Unknown bonus card type")
    
    def _is_immediate(self):
        """Check if the bonus card should be played immediately or kept for later"""
        immediate_cards = ["See A Card", "Peek At Envelope"]
        return self.card_type in immediate_cards
    
    def play(self, game, player):
        """
        Play the bonus card and apply its effect
        
        Args:
            game: The game instance
            player: The player who is playing the card
            
        Returns:
            str: A message describing the effect of the card
        """
        if self.card_type == "Extra Turn":
            # This will be handled in the game loop
            return f"{player.character.name} will get an extra turn."
        
        elif self.card_type == "See A Card":
            # Choose a player and see one of their cards
            other_players = [p for p in game.players if p.player_id != player.player_id and not p.eliminated]
            if not other_players:
                return "No other players to see cards from."
            
            print("Choose a player to see a card from:")
            for i, p in enumerate(other_players):
                print(f"{i+1}. {p.character.name}")
            
            choice = int(input("Enter your choice: ")) - 1
            target_player = other_players[choice]
            
            if not target_player.hand:
                return f"{target_player.character.name} has no cards."
            
            card = random.choice(target_player.hand)
            return f"You saw {card} from {target_player.character.name}'s hand."
        
        elif self.card_type == "Move Any Character":
            # Choose a character and move them to a room
            print("Choose a character to move:")
            for i, name in enumerate(game.char_board.positions.keys()):
                print(f"{i+1}. {name}")
            
            choice = int(input("Enter your choice: ")) - 1
            character_name = list(game.char_board.positions.keys())[choice]
            
            print("Choose a room to move to:")
            for i, room_name in enumerate(game.mansion_board.room_dict.keys()):
                print(f"{i+1}. {room_name}")
            
            choice = int(input("Enter your choice: ")) - 1
            room_name = list(game.mansion_board.room_dict.keys())[choice]
            
            # Find a position in the room
            room = game.mansion_board.room_dict[room_name]
            if room.room_entrance_list:
                new_pos = (room.room_entrance_list[0].row, room.room_entrance_list[0].column)
                game.char_board.move(character_name, new_pos[0], new_pos[1])
                return f"Moved {character_name} to {room_name}."
            else:
                return f"Could not move {character_name} to {room_name} (no entrances found)."
        
        elif self.card_type == "Teleport":
            # Move the player's character to any room
            print("Choose a room to teleport to:")
            for i, room_name in enumerate(game.mansion_board.room_dict.keys()):
                print(f"{i+1}. {room_name}")
            
            choice = int(input("Enter your choice: ")) - 1
            room_name = list(game.mansion_board.room_dict.keys())[choice]
            
            # Find a position in the room
            room = game.mansion_board.room_dict[room_name]
            if room.room_entrance_list:
                new_pos = (room.room_entrance_list[0].row, room.room_entrance_list[0].column)
                player.character.move_to(new_pos)
                game.char_board.move(player.character.name, new_pos[0], new_pos[1])
                return f"Teleported to {room_name}."
            else:
                return f"Could not teleport to {room_name} (no entrances found)."
        
        elif self.card_type == "Peek At Envelope":
            # Look at one card in the envelope
            envelope_cards = list(game.solution.values())
            card_type = random.choice(["suspect", "weapon", "room"])
            card = game.solution[card_type]
            return f"You peeked at the envelope and saw: {card} ({card_type})."
        
        return "Unknown bonus card effect."
    
    def __repr__(self):
        return f"BonusCard({self.card_type}): {self.description}"