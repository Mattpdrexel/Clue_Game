from Constants import SUSPECTS, WEAPONS, ROOMS, ALL_CARDS


class PossibilityMatrix:
    """
    poss[card][holder] == True   ⇒  card *could* be with holder
    holders = ["P0", "P1", ... , "ENVELOPE"]
    """
    def __init__(self, n_players, my_id, my_hand):
        self.holders = [f"P{i}" for i in range(n_players)] + ["ENVELOPE"]
        self.me      = f"P{my_id}"

        # Start with everything possible
        self.poss = {card: {h: True for h in self.holders} for card in ALL_CARDS}

        # Apply certainty about my own hand
        for card in ALL_CARDS:
            if card in my_hand:
                self.set_holder(card, self.me)
            else:
                self.eliminate(card, self.me)

        self.propagate()

    # ---------- public API ----------
    def set_holder(self, card, holder):
        """Card is definitively with <holder>."""
        for h in self.holders:
            self.poss[card][h] = (h == holder)
        self.propagate()

    def eliminate(self, card, holder):
        """Card cannot be with <holder>."""
        if self.poss[card][holder]:
            self.poss[card][holder] = False
            self.propagate()

    def card_owner(self, card):
        """Return holder if known, else None."""
        row = self.poss[card]
        owners = [h for h, ok in row.items() if ok]
        return owners[0] if len(owners) == 1 else None

    # ---------- core propagation ----------
    def propagate(self):
        changed = True
        while changed:
            changed = False
            # (1) If a card has exactly one possible holder → set it
            for card, row in self.poss.items():
                owners = [h for h, ok in row.items() if ok]
                if len(owners) == 1:
                    holder = owners[0]
                    for h in self.holders:
                        if h != holder and self.poss[card][h]:
                            self.poss[card][h] = False
                            changed = True

            # (2) If a holder has exactly n known cards and
            #     all their open slots filled, eliminate rest

            # Calculate how many cards each holder definitely has
            definite_cards = {h: [] for h in self.holders}
            for card in ALL_CARDS:
                holder = self.card_owner(card)
                if holder:
                    definite_cards[holder].append(card)

            # Calculate how many cards each holder could possibly have
            possible_cards = {h: [c for c in ALL_CARDS if self.poss[c][h]] for h in self.holders}

            # For each player, determine how many cards they should have
            # This is based on the game rules - cards are dealt evenly
            player_holders = [h for h in self.holders if h != "ENVELOPE"]
            cards_per_player = (len(ALL_CARDS) - 3) // len(player_holders)  # 3 cards in envelope

            # If a player has exactly the right number of possible cards,
            # and some are definite, then the rest must also be definite
            for holder in player_holders:
                if holder != self.me:  # Skip self (we already know our cards)
                    if len(possible_cards[holder]) == cards_per_player and len(definite_cards[holder]) > 0:
                        # All possible cards for this holder must be definite
                        for card in possible_cards[holder]:
                            if card not in definite_cards[holder]:
                                self.set_holder(card, holder)
                                changed = True

            # If a player has exactly the right number of definite cards,
            # eliminate all other possibilities
            for holder in player_holders:
                if len(definite_cards[holder]) == cards_per_player:
                    for card in ALL_CARDS:
                        if card not in definite_cards[holder] and self.poss[card][holder]:
                            self.poss[card][holder] = False
                            changed = True

    # ---------- envelope deduction ----------
    def envelope_complete(self):
        """Return (suspect, weapon, room) if all three forced, else None."""
        suspect  = next((c for c in SUSPECTS  if self.card_owner(c) == "ENVELOPE"), None)
        weapon   = next((c for c in WEAPONS   if self.card_owner(c) == "ENVELOPE"), None)
        room     = next((c for c in ROOMS     if self.card_owner(c) == "ENVELOPE"), None)
        if suspect and weapon and room:
            return suspect, weapon, room
        return None
