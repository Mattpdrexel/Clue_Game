from Constants import SUSPECTS, WEAPONS, ROOMS

class Suggestion:
    """A class to represent a suggestion made during the game."""
    def __init__(self, player_id, suspect, weapon, room):
        self.player_id = player_id
        self.suspect = suspect
        self.weapon = weapon
        self.room = room
        self.refuted_by = None
        self.card_shown = None
    
    def refute(self, refuter_id, card):
        """Record that the suggestion was refuted."""
        self.refuted_by = refuter_id
        self.card_shown = card
    
    def __str__(self):
        result = f"Player {self.player_id} suggested {self.suspect} with {self.weapon} in {self.room}"
        if self.refuted_by is not None:
            result += f" - Refuted by Player {self.refuted_by}"
            if self.card_shown is not None:
                result += f" showing {self.card_shown}"
        else:
            result += " - Not refuted"
        return result

class SuggestionHistory:
    """A class to track the history of suggestions made during the game."""
    def __init__(self):
        self.suggestions = []
    
    def add_suggestion(self, player_id, suspect, weapon, room):
        """Add a new suggestion to the history."""
        suggestion = Suggestion(player_id, suspect, weapon, room)
        self.suggestions.append(suggestion)
        return suggestion
    
    def get_player_suggestions(self, player_id):
        """Get all suggestions made by a specific player."""
        return [s for s in self.suggestions if s.player_id == player_id]
    
    def get_suggestions_involving(self, card):
        """Get all suggestions involving a specific card."""
        return [s for s in self.suggestions if s.suspect == card or s.weapon == card or s.room == card]
    
    def get_all_suggestions(self):
        """Get all suggestions made during the game."""
        return self.suggestions
    
    def __str__(self):
        if not self.suggestions:
            return "No suggestions have been made yet."
        
        result = "Suggestion History:\n"
        for i, suggestion in enumerate(self.suggestions):
            result += f"{i+1}. {suggestion}\n"
        return result