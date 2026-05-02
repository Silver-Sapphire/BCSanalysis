
#card_data_collection_pipeline.py

import src.db_operations as db_operations
from src.helpers import get_page as get
import src.helpers as helpers

from bs4 import BeautifulSoup as Soup


BASE_URL = 'https://en.cf-vanguard.com/cardlist/?cardno='


def db_lookup(id_and_name):
    id = helpers.extract_card_id(id_and_name)
    return db_operations.find_first_in_table('main_table', 'card_data', {'id':id})


def url_lookup(id_and_name):
    id = helpers.extract_card_id(id_and_name)
    return add_card_info_to_db(id)


def add_card_info_to_db(set_num: str) -> dict[str|int]:
    """Given a card name, add its information to a central data base"""

    try:
        html_text = get_card_info_from_bushi_site(set_num)

        data_entry = extract_data_from_bushi_site(html_text)

        db_operations.insert_one_into_table('main_table',
                                            'card_data',
                                            data_entry)

        return data_entry

    except Exception as something_went_wrong:
        print(f'Error during data collection of {set_num}: ', something_went_wrong)
        raise LookupError



def get_card_info_from_bushi_site(set_code: str) -> list[list[str]]:
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
    response = get(url)
    soup=Soup(response.text, 'html.parser')
    data = soup.find(attrs={'class':'data'})

    name = data.find(attrs={'class':'name'}).text.strip()
    effect = data.find(attrs={'class':'effect'}).text.strip()
    flavor = data.find(attrs={'class':'flavor'}).text.strip()
    stats_line, bottom_line = data.find_all(attrs={'class':'text-list'})
    bottom_line = bottom_line.text.strip().split('\n')
    split_stats = stats_line.text.strip().split('\n')

    if len(stats_line.find_all(attrs={'class':'nation'})) == 2:
        second_nation = split_stats.pop(2)
        split_stats[1] = split_stats[1] + ' / ' + second_nation

    elif stats_line.find(attrs={'class':'group'}):
        clan = split_stats.pop(3)
        split_stats[2] = clan + ' / ' + split_stats[2]
        
    return [name, split_stats, effect, flavor, bottom_line]



def extract_data_from_bushi_site(test):
    data_entry = dict()
    data_entry['name'] = test[0]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~Section 1~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    card_type = test[1][0]

    # Dual nation cards are longer than expected, so we'll fit them into our zone here
    # if (len(test[1]) == 8 and "Order" in card_type and "Regalis" not in test[1][7])\
    # or (len(test[1]) == 9 and "Normal Unit" == card_type)\
    # or (len(test[1]) == 10 and "Trigger Unit" == card_type):
    #     second_nation = test[1].pop(2)
    #     test[1][1] = test[1][1] + ' / ' + second_nation

    data_entry['type'] = card_type
    data_entry['nation'] = test[1][1]
    data_entry['race'] = test[1][2]
    
    # Crests, Units, and orders each have a different set of attributes which need TLC
    if "Crest" in card_type:
        data_entry['grade'] = None
    else:
        data_entry['grade'] = int(test[1][3].split(' ')[1])

    if "Unit" in card_type:
        data_entry['power'] = int(test[1][4].split(' ')[1])
        # data_entry['crit'] = int(test[1][5].split(' ')[1])

        # Grade 3's have an empty string when checking for shield, so this fixes that bug
        shield = test[1][6].split(' ')[1]
        if shield == '' or '-' == shield:
            data_entry['shield'] = None
        else:
            data_entry['shield'] = int(shield)

        data_entry['ability'] = test[1][7]    

    else: # If "Order" in card_type
        data_entry['power'] =   None
        data_entry['crit'] =    None
        data_entry['shield'] =  None
        data_entry['ability'] = None

    if "Trigger" in card_type:
        data_entry['trigger'] = test[1][8]
    else:
        data_entry['trigger'] = None

    #~~~~~~~~~~~~~~~~~~~~Section 2~~~~~~~~~~~~~~~~~~~~~~~~~~
    # If there's no effect, add a placeholder
    if len(test) == 3:
        test.insert(2, '-')
    data_entry['effect'] = test[2]

    #~~~~~~~~~~~~~~~~~~~~Section 3~~~~~~~~~~~~~~~~~~~~~~~~~
    # If there's no flavor text, add an empty string
    if len(test) == 4:
        test.insert(3, '')

    data_entry['flavor'] = test[3]

    #~~~~~~~~~~~~~~~~~~~~Section 4~~~~~~~~~~~~~~~~~~~~~~~
    data_entry['format'] = test[4][0]
    data_entry['id'] =     test[4][1]
    data_entry['rarity'] = test[4][2]
    data_entry['artist'] = test[4][3]

    return data_entry