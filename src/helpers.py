# helpers.py

def extract_card_name(id_and_name):
    """
    Given an ID + Name line, return just the name.

    The Id + Name line is sturcured:
    ' IDstring/000EN : Card Name'
    with the spaces on either side of the colon. 
    
    By simply splitting the string there, we can easily return the name, or the ID
    """
    if ('EN' in id_and_name) and (' : ' in id_and_name):
        return id_and_name.split(' : ')[1]
    
    return id_and_name # No : to exctract


def extract_card_id(id_and_name:str):
    """
    Given an ID + Name line, return just the ID.

    The Id + Name line is sturcured:
    ' IDstring/000EN : Card Name'
    with the spaces on either side of the colon. 
    
    By simply splitting the string there, we can easily return the name, or the ID
    """
    return id_and_name.split(' : ')[0]
    

# this is redundant. we can check for truthiness of next func \|/
# def card_is_in_deck(decks_dict, card_name, deck='MainDeck'):
#     # return card_name in decks_dict[deck]
#     for id_and_name in decks_dict[deck]:
#         if card_name in id_and_name:
#             return True
    
#     return False



def card_count_in_deck(decks_dict, card_name, deck='MainDeck'):
    # return decks_dict[deck].get(card_name, 0)
    for id_and_name, amount in decks_dict[deck].items():
        if card_name in id_and_name:
            return amount
    
    return False



# This function combines the former two, and allows a list of cards as input
def card_type_in_deck(decks_dict, card_list, deck='MainDeck'):
    for card in card_list:
        foo = card_count_in_deck(decks_dict, card, deck)
        if foo:
            return foo
        
    return 0


def sort_dict_by_values(dict) -> dict:
    sort = {k:v for k,v in sorted(
        dict.items(), 
        key=lambda k: k[1], 
        reverse=True)}
    return sort