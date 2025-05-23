# Cluedo (Clue) Game Implementation

This project implements a digital version of the classic murder mystery board game Cluedo (also known as Clue). The game is implemented in Python, allowing players to move around the mansion, make suggestions, and ultimately solve the murder mystery.

## Game Rules

### Setup
- 6 suspects: Miss Scarlet, Colonel Mustard, Mrs White, Reverend Green, Mrs Peacock, Professor Plum
- 6 weapons: Candlestick, Lead Pipe, Wrench, Knife, Revolver, Rope
- 9 rooms: Study, Hall, Lounge, Dining Room, Kitchen, Ball Room, Conservatory, Billiard Room, Library
- One random suspect, weapon, and room are secretly chosen as the solution
- The remaining cards are shuffled and dealt to all players
- All characters start in the center of the board
- Some rooms have secret passages connecting them (Study-Kitchen, Lounge-Conservatory)

### Gameplay
1. Players take turns in clockwise order
2. On your turn, you can:
   - If starting in a room:
     - Stay in the room
     - Use a secret passage (if available)
     - Exit and roll the dice to move
   - Otherwise, roll the dice and move your character orthogonally (no diagonal moves)
3. Movement mechanics:
   - You can enter a room without using the exact number of steps
   - You can choose to enter coordinates directly or select from a list of valid moves
   - Room entrances are always valid destinations if they're reachable
4. If you land on a red question mark, you may draw a bonus card
5. When you enter a room, you must stop and may make a suggestion about the murder
6. A suggestion consists of a suspect, a weapon, and the room you are currently in
7. The suggested character and weapon are moved to the room
8. Other players, starting with the player to your left, must reveal one matching card if they have one
9. Once a player reveals a card, no more cards are shown for that suggestion
10. You can make one accusation per game by moving to the center of the board
11. If the accusation is correct, you win
12. If the accusation is wrong, you are eliminated from making further accusations
13. If all players make incorrect accusations, everyone loses

## Project Structure

- `game.py`: Implements the game loop and mechanics
- `Board.py`: Defines the mansion board and character positions
- `Character.py`: Defines the character class and character dictionary
- `Weapon.py`: Defines the weapon class
- `Room.py`: Defines the room class, room entrances, and secret passages
- `Player.py`: Defines the player class and bonus card handling
- `Constants.py`: Defines game constants like character names, weapon names, room names, and secret passages
- `DeductionMatrix.py`: Implements the logic engine for deducing the solution
- `DeductionViewer.py`: Keep track of information accumulated for players
- `BonusCard.py`: Defines the bonus card class and its effects

## How to Play

1. Run the game:
   ```
   python game.py
   ```

2. Follow the prompts to:
   - Roll the dice
   - Move your character:
     - Choose to enter coordinates directly or select from a list of valid moves
     - Enter a room without using the exact number of steps
     - Room entrances are always valid destinations if they're reachable
   - Make suggestions when in a room
   - Make accusations when you think you know the solution

3. The game ends when a player makes a correct accusation or all players are eliminated.

## Implementation Details

- The game board is loaded from an Excel file (`mansion_board_layout.xlsx`)
  - I created this Excel sheet by hand, modeling it after the classic Clue board game layout ()
  - Each cell in the spreadsheet represents a space on the board with specific values:
    - Room names for spaces inside rooms
    - Room names with "_e" suffix for room entrances
    - "?" for bonus card spaces
    - Empty cells for corridors
  - The board design was inspired by the grid layout from the classic Clue board game: https://www.pinterest.com/pin/clue-board-game-classic-detective-game--10344274143620595/
- Characters and weapons are moved around the board as players make suggestions
- Players can deduce the solution using the information from revealed cards
- The game supports 3 players by default, but can be configured for different numbers
- Movement mechanics:
  - Room entrances are added to valid moves regardless of remaining steps
  - Players can enter coordinates directly or choose from a list of valid moves
  - Coordinate validation ensures that only valid moves are accepted

## Deduction System

The game includes a deduction system that helps players solve the murder mystery:

### Suggestion History

- All suggestions made during the game are tracked in a suggestion history
- For each suggestion, the system records:
  - Who made the suggestion
  - What was suggested (suspect, weapon, room)
  - Whether it was refuted and by whom
  - What card was shown (to the suggester only)
- Players can view the suggestion history during their turn

### Deduction Matrix

- Each player has a deduction matrix that tracks what they know about card ownership
- The matrix shows which cards could be with which players or in the envelope
- The system automatically updates the matrix based on:
  - Cards in the player's hand
  - Cards revealed during suggestions
  - Logical deductions (e.g., if a player couldn't refute a suggestion)
- Players can view their deduction matrix during their turn
- The system can deduce the solution if enough information is gathered

### Making Deductions

- When a player makes a suggestion, other players must reveal a matching card if they have one
- When a player can't refute a suggestion, this information is recorded in the deduction matrix
- The system uses advanced logic to make deductions:
  - If a card has only one possible holder, it must be with that holder
  - If a player has exactly the right number of cards and some are known, the rest can be deduced
  - If a player has all their cards accounted for, they can't have any other cards

## Future Improvements

- Add a graphical user interface
- Implement AI players
- Add network support for multiplayer
- Add more types of bonus cards
- Add a visual grid overlay for coordinate selection
- Implement pathfinding visualization for valid moves

## References
- Played some of SNES simulation of clue to get a sense of how game works (never played the board game before):
- https://funkypotato.com/clue-online-cluedo/
- Image used for clue board:
- https://www.pinterest.com/pin/clue-board-game-classic-detective-game--10344274143620595/
