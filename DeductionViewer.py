from Constants import SUSPECTS, WEAPONS, ROOMS, ALL_CARDS

class DeductionViewer:
    """A class to display deduction information in a user-friendly format."""
    
    @staticmethod
    def display_matrix(matrix, player_id):
        """Display a player's deduction matrix in a readable format."""
        print(f"\n===== Deduction Matrix for Player {player_id} =====")
        
        # Display column headers (holders)
        holders = matrix.holders
        header = "Card".ljust(20)
        for holder in holders:
            header += holder.ljust(8)
        print(header)
        print("-" * (20 + 8 * len(holders)))
        
        # Display rows for each card category
        print("\n--- SUSPECTS ---")
        for card in SUSPECTS:
            row = card.ljust(20)
            for holder in holders:
                if matrix.poss[card][holder]:
                    row += "✓".ljust(8)
                else:
                    row += "✗".ljust(8)
            print(row)
        
        print("\n--- WEAPONS ---")
        for card in WEAPONS:
            row = card.ljust(20)
            for holder in holders:
                if matrix.poss[card][holder]:
                    row += "✓".ljust(8)
                else:
                    row += "✗".ljust(8)
            print(row)
        
        print("\n--- ROOMS ---")
        for card in ROOMS:
            row = card.ljust(20)
            for holder in holders:
                if matrix.poss[card][holder]:
                    row += "✓".ljust(8)
                else:
                    row += "✗".ljust(8)
            print(row)
        
        # Check if the envelope is complete
        envelope_solution = matrix.envelope_complete()
        if envelope_solution:
            suspect, weapon, room = envelope_solution
            print(f"\nDeduced solution: {suspect} with {weapon} in {room}")
        else:
            # Show what's known about the envelope
            print("\nPartial envelope deduction:")
            envelope_suspects = [s for s in SUSPECTS if matrix.poss[s]["ENVELOPE"]]
            envelope_weapons = [w for w in WEAPONS if matrix.poss[w]["ENVELOPE"]]
            envelope_rooms = [r for r in ROOMS if matrix.poss[r]["ENVELOPE"]]
            
            print(f"Possible suspects: {', '.join(envelope_suspects) if envelope_suspects else 'Unknown'}")
            print(f"Possible weapons: {', '.join(envelope_weapons) if envelope_weapons else 'Unknown'}")
            print(f"Possible rooms: {', '.join(envelope_rooms) if envelope_rooms else 'Unknown'}")