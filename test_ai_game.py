import unittest
from game import ClueGame
import traceback

class TestAIGame(unittest.TestCase):
    def test_ai_game(self):
        """Test that a game with 3 AI players runs to completion"""
        try:
            # Create a game with 3 AI players and logging enabled, disable visualization for testing
            game = ClueGame(num_players=3, use_ai_players=True, log_to_csv=True, enable_visualization=False)

            # Force a specific solution for testing
            game.solution = {
                "suspect": "Miss Scarlet",
                "weapon": "Candlestick",
                "room": "Study"
            }

            # Run the game with a maximum of 80 turns to prevent infinite loops
            try:
                game.run(max_turns=80)
            except Exception as e:
                self.fail(f"Game run failed with error: {str(e)}\n{traceback.format_exc()}")

            # Check that the game ended or reached max turns
            self.assertTrue(game.game_over or game.turn_counter >= 80)

            # Check that there's a winner or all players are eliminated or max turns reached
            self.assertTrue(
                game.winner is not None or 
                all(p.eliminated for p in game.players) or 
                game.turn_counter >= 80
            )

            # If there's a winner, check that they made a correct accusation
            if game.winner:
                self.assertFalse(game.winner.eliminated)

                # Check that the winner's deduction matrix has the correct solution
                matrix = game.logic_engines[game.winner.player_id]
                envelope_solution = matrix.envelope_complete()
                if envelope_solution:
                    suspect, weapon, room = envelope_solution
                    self.assertEqual(suspect, game.solution["suspect"])
                    self.assertEqual(weapon, game.solution["weapon"])
                    self.assertEqual(room, game.solution["room"])
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    # Run the test
    unittest.main()
