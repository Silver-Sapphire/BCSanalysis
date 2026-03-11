# helpers.py

def extract_card_name(id_and_name):
    """
    Given an ID + Name line, return just the name.

    The Id + Name line is sturcured:
    ' IDstring/000EN : Card Name'
    with the spaces on either side of the colon. 
    
    By simply splitting the string there, we can easily return the name, or the ID
    """
    return id_and_name.split(' : ')[1]


def extract_card_id(id_and_name):
    """
    Given an ID + Name line, return just the ID.

    The Id + Name line is sturcured:
    ' IDstring/000EN : Card Name'
    with the spaces on either side of the colon. 
    
    By simply splitting the string there, we can easily return the name, or the ID
    """
    return id_and_name.split(' : ')[0]
    