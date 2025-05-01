import unittest
from game import ClueGame
from Constants import SUSPECTS, WEAPONS, ROOMS
from DeductionMatrix import PossibilityMatrix

class TestDeductionSystem(unittest.TestCase):
    def setUp(self):
        self.game = ClueGame(num_players=3, enable_visualization=False)
        # Force a specific solution for testing
        self.game.solution = {
            "suspect": SUSPECTS[0],
            "weapon": WEAPONS[0],
            "room": ROOMS[0]
        }

    def test_suggestion_history(self):
        """Test that suggestions are correctly recorded in the history."""
        # Create a suggestion
        player = self.game.players[0]
        suspect = SUSPECTS[1]
        weapon = WEAPONS[1]
        room = ROOMS[1]

        # Make the suggestion
        self.game.make_suggestion(player, suspect, weapon, room)

        # Check that the suggestion was recorded
        self.assertEqual(len(self.game.suggestion_history.suggestions), 1)
        suggestion = self.game.suggestion_history.suggestions[0]
        self.assertEqual(suggestion.player_id, player.player_id)
        self.assertEqual(suggestion.suspect, suspect)
        self.assertEqual(suggestion.weapon, weapon)
        self.assertEqual(suggestion.room, room)

    def test_refutation(self):
        """Test that refutations are correctly recorded."""
        # Set up a scenario where a suggestion will be refuted
        player0 = self.game.players[0]
        player1 = self.game.players[1]

        # Give player1 a specific card
        test_card = SUSPECTS[1]
        player1.hand = [test_card]

        # Clear player0's hand to avoid interference
        player0.hand = []

        # Set up the game state for the suggestion
        self.game.current_player_idx = 0

        # Make a suggestion that includes the card player1 has
        suspect = test_card
        weapon = WEAPONS[1]
        room = ROOMS[1]

        # Make the suggestion
        responder, card = self.game.make_suggestion(player0, suspect, weapon, room)

        # Check that the refutation was recorded
        self.assertEqual(responder, player1)
        self.assertEqual(card, test_card)

        # Check that the suggestion history was updated
        suggestion = self.game.suggestion_history.suggestions[0]
        self.assertEqual(suggestion.refuted_by, player1.player_id)
        self.assertEqual(suggestion.card_shown, test_card)

    def test_deduction_matrix_update(self):
        """Test that the deduction matrix is updated correctly after a suggestion."""
        # Set up a scenario where a suggestion will be refuted
        player0 = self.game.players[0]
        player1 = self.game.players[1]

        # Give player1 a specific card
        test_card = SUSPECTS[1]
        player1.hand = [test_card]

        # Clear player0's hand to avoid interference
        player0.hand = []

        # Reset the deduction matrix for player0
        self.game.logic_engines[player0.player_id] = PossibilityMatrix(len(self.game.players), player0.player_id, player0.hand)

        # Set up the game state for the suggestion
        self.game.current_player_idx = 0

        # Make a suggestion that includes the card player1 has
        suspect = test_card
        weapon = WEAPONS[1]
        room = ROOMS[1]

        # Make the suggestion
        self.game.make_suggestion(player0, suspect, weapon, room)

        # Check that the deduction matrix was updated
        matrix = self.game.logic_engines[player0.player_id]
        self.assertEqual(matrix.card_owner(test_card), f"P{player1.player_id}")

    def test_deduction_from_no_refutation(self):
        """Test that deductions are made when no one can refute a suggestion."""
        # Set up a scenario where no one can refute a suggestion
        player0 = self.game.players[0]
        player1 = self.game.players[1]
        player2 = self.game.players[2]

        # Give players specific cards that don't match the suggestion
        player0.hand = [SUSPECTS[2], WEAPONS[2]]
        player1.hand = [SUSPECTS[3], WEAPONS[3]]
        player2.hand = [SUSPECTS[4], WEAPONS[4]]

        # Reset the deduction matrices
        for player in self.game.players:
            self.game.logic_engines[player.player_id] = PossibilityMatrix(len(self.game.players), player.player_id, player.hand)

        # Set up the game state for the suggestion
        self.game.current_player_idx = 0

        # Make a suggestion that no one can refute (using cards in the solution)
        suspect = self.game.solution["suspect"]
        weapon = self.game.solution["weapon"]
        room = self.game.solution["room"]

        # Make the suggestion
        responder, card = self.game.make_suggestion(player0, suspect, weapon, room)

        # Check that no one could refute
        self.assertIsNone(responder)
        self.assertIsNone(card)

        # Check that the deduction matrix was updated
        # The cards might be in the envelope or with the suggester
        matrix = self.game.logic_engines[player0.player_id]

        # Check that the cards are not with player1 or player2
        self.assertFalse(matrix.poss[suspect][f"P{player1.player_id}"])
        self.assertFalse(matrix.poss[suspect][f"P{player2.player_id}"])
        self.assertFalse(matrix.poss[weapon][f"P{player1.player_id}"])
        self.assertFalse(matrix.poss[weapon][f"P{player2.player_id}"])
        self.assertFalse(matrix.poss[room][f"P{player1.player_id}"])
        self.assertFalse(matrix.poss[room][f"P{player2.player_id}"])

if __name__ == "__main__":
    unittest.main()
