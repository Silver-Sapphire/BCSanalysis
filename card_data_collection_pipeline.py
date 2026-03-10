
import requests


import db_operations


from bs4 import BeautifulSoup as Soup
from pymongo import MongoClient

BASE_URL = 'https://en.cf-vanguard.com/cardlist/?cardno='

def add_card_info_to_db(set_num: str) -> dict[str|int]:
    """Given a card name, add its information to a central data base"""

    try:
        html_text = _get_card_info_from_bushi_site(set_num)

        data_entry = _exctract_info_from_bushi_site(html_text)

        db_operations.insert_one_into_table('main_table',
                                            TODO,
                                            data_entry)

        return data_entry

    except Exception as something_went_wrong:
        print(something_went_wrong)
        return None


def _get_card_info_from_bushi_site(set_code: str) -> list[list[str]]:
    """Given a name, and maybe decklog, retrieve the text of the official webpage with it's information
    
    The wepbage contains an element, 'data', which has all the informatin about the card for the URL.
    It contains some sub elements, so the easiest way to extract it is to simply retrieve the text from each,
    and put it into a big list.

    There are lots of different atributes of the card that are contained in one element, seperated by `\n`
    new line charachters. So, for each element, we'll turn it into a list of attributes,
    ending us with a list of lists of string. list [ list [ str ] ]

    # name 
    # stats
    # effect 
    # flavor
    # bottomline(set, artist, etc.)

    These are the 5 children of the data element, each with a different number of attributes.
    """
    url = BASE_URL + str(set_code)
    response = requests.get(url)
    soup=Soup(response.text, 'html.parser')
    data_element = soup.find(attrs={'class':'data'})

    data = []
    for child in data_element:
        text = child.text
        if text.strip() != '':
            data.append(text.strip())

    return data


def _exctract_info_from_bushi_site(seperated_soup: list[list[str]]) -> dict:
    """Given the text from a card's bushi site page, return the information we want in our database
    
    We hit a few snags, due to the combinations of order, trigger, and unit atributes that can cause
    some headache.

    For now, Order type (Music, Codex, Fox Art, Etc.) are placed in the 'race' section,
    and orders with no type just have '-' as their race. We can wrange these issues later.
    At least we have the data.
    """

    data_entry = dict()
    test = []
    for i, item in enumerate(seperated_soup):
        if i == 3: test.append(item) # We want to preserve line breaks in flavor text?
        else: test.append(item.split('\n'))

    card_type = test[1][0]

    data_entry['name'] = test[0][0]

    data_entry['type'] = card_type
    data_entry['nation'] = test[1][1]
    data_entry['race'] = test[1][2]
    data_entry['grade'] = int(test[1][3].split(' ')[1])
    # ~~~~~~~~~~~~~~~~~~   UNIT / ORDER / TRIGGER LOGIC ~~~~~~~~~~~~~~~~~~~~~~~
    if "Unit" in card_type:
        data_entry['power'] = int(test[1][4].split(' ')[1])
        data_entry['crit'] = int(test[1][5].split(' ')[1])
        # Grade 3's have an empty string when checking for shield, so this fixes that bug
        shield = test[1][6].split(' ')[1]
        if shield == '':
            data_entry['shield'] = 0
        else:
            data_entry['shield'] = int(shield)

        data_entry['ability'] = test[1][7]

    else:
        data_entry['power'] = "None"
        data_entry['crit'] = "None"
        data_entry['shield'] = "None"
        data_entry['ability'] = "None"

    if "Trigger" in card_type:
        data_entry['trigger'] = test[1][8]
    else:
        data_entry['trigger'] = "None"

    data_entry['effect'] = test[2][0]
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Some cards don't have flavor text, and this 'Magic Number Hack' inserts an empty string
    if len(test) == 4:
        test.insert(3, '')
    data_entry['flavor'] = test[3]

    data_entry['format'] = test[4][0]
    data_entry['id'] = test[4][1]
    data_entry['rarity'] = test[4][2]
    data_entry['illust'] = test[4][3]

    return data_entry
