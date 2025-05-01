import pytest, random
from simple_ai import SimpleAIPlayer
from game import ClueGame      # or whatever constructs a game

@pytest.fixture
def game3(tmp_path):
    random.seed(42)
    g = ClueGame(num_human=0, ai_class=SimpleAIPlayer)  # adapt to your factory
    g.max_turns = 120
    return g

def test_finishes_under_80(game3):
    game3.play()                       # headless run
    assert game3.winner is not None
    assert game3.turn_counter < 80

def test_no_room_camping(game3):
    history = []
    game3.track_positions = history    # adapt: engine should append (pid,room) each turn
    game3.play()
    for pid in range(3):
        prev_room = None
        for turn_pid, room in history:
            if turn_pid == pid:
                # Only check if the player is in a room (room is not None)
                # and was in a room in the previous turn (prev_room is not None)
                if room is not None and prev_room is not None:
                    assert room != prev_room, f"Player {pid} stayed in {room} for two consecutive turns"
                prev_room = room
