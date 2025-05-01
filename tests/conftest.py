import pytest
from game import ClueGame

@pytest.fixture
def mini_game():
    """Create a small game instance for testing"""
    game = ClueGame(num_players=3, use_ai_players=False, log_to_csv=False, enable_visualization=False)
    return game
