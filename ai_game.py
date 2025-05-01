from game import ClueGame

def run_ai_game():
    """Run a game with 3 AI players"""
    print("Starting a game with 3 AI players...")
    
    # Create a game with 3 AI players and logging enabled
    game = ClueGame(num_players=3, use_ai_players=True, log_to_csv=True)
    
    # Run the game
    game.play_game()
    
    # Print the result
    if game.winner:
        print(f"\nGame completed! {game.winner.character.name} won the game!")
    else:
        print("\nGame completed! All players were eliminated.")
        print(f"The solution was: {game.solution['suspect']} with the {game.solution['weapon']} in the {game.solution['room']}")

if __name__ == "__main__":
    run_ai_game()