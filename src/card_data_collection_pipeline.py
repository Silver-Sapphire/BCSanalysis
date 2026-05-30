
#card_data_collection_pipeline.py
from typing import Any

import src.db_operations as db_operations
from src.helpers import get_page as get
import src.helpers as helpers

from bs4 import BeautifulSoup as Soup


BASE_URL = 'https://en.cf-vanguard.com/cardlist/?cardno='


def db_lookup(id_and_name: str) -> dict:
    """ 
    given an id/name line for a card,
    return it's info in our db, if it exists.
    """
    id = helpers.extract_card_id(id_and_name)
    return db_operations.find_first_in_table('main_table', 'card_data', {'id':id})


def url_lookup(id_and_name: str) -> dict:
    """
    given an id/name line for a card;

    lookup the data from the Bushi site,
    deposit it into our db for future retrival,
    and return it's dictionary.
    """
    id = helpers.extract_card_id(id_and_name)
    return add_card_info_to_db(id)


def add_card_info_to_db(set_num: str) -> dict[str|int]:
    """
    Given a set id code;

    lookup the data from the Bushi site,
    deposit it into our db for future retrival,
    and return it's dictionary.
    """

    try:
        soup = get_card_info_from_bushi_site(set_num)

        data_entry = extract_data_from_bushi_site(soup)

        db_operations.insert_one_into_table('main_table',
                                            'card_data',
                                            data_entry)

        return data_entry

    except Exception as something_went_wrong:
        print(f'Error during data collection of {set_num}: ', something_went_wrong)
        raise LookupError
    

def get_soup_from_bushi_site(set_code:str) -> Soup:
    """
    
    """
    url = BASE_URL + str(set_code)
    response = get(url)
    soup = Soup(response.text, 'html.parser')
    data = soup.find(attrs={'class':'data'})

    return data


def extract_text_from_soup(soup, target_class) -> str:
    return soup.find(attrs={'class':target_class}).text.strip()


def extract_data_from_bushi_soup(soup:Soup) -> list[Any]:
    """
    
    """
    data_entry = dict()
    data_entry['name'] = extract_text_from_soup(soup, 'name')
    data_entry['effect'] = extract_text_from_soup(soup, 'effect')
    data_entry['flavor'] = extract_text_from_soup(soup, 'flavor')

    data_entry['type'] = extract_text_from_soup(soup, 'type')

    # nation /dual nation handling.
    nations = soup.find_all(attrs={'class':'nation'})
    if len(nations) > 1:
        second_nation = nations.pop()
        nation_str = nations.pop() + ' / ' + second_nation
        data_entry['nation'] = nation_str

    if len(nations) == 1:
        data_entry['nation'] = extract_text_from_soup(soup, 'nation')
    

    #clan ish
    data_entry['group'] = extract_text_from_soup(soup, 'group')

    data_entry['race'] = extract_text_from_soup(soup, 'race') 
    data_entry['grade'] = extract_text_from_soup(soup, 'grade')
    data_entry['power'] = extract_text_from_soup(soup, 'power')
    data_entry['shield'] = extract_text_from_soup(soup, 'shield')
    data_entry['critical'] = extract_text_from_soup(soup, 'critical')
    data_entry['ability'] = extract_text_from_soup(soup, 'ability')
    data_entry['trigger'] = extract_text_from_soup(soup, 'trigger')
    data_entry['gift'] = extract_text_from_soup(soup, 'gift')

    # bottom_line_list = ['regulation','number','rarity','illustrator']
    # for line in bottom_line_list: 
        # data_entry[line] = extract_text_from_soup(soup, line)
    data_entry['format'] = extract_text_from_soup(soup, 'regulation')
    data_entry['id'] = extract_text_from_soup(soup, 'number')
    data_entry['rarity'] = extract_text_from_soup(soup, 'rarity')
    data_entry['artist'] = extract_text_from_soup(soup, 'illustrator')


    return data_entry


def get_card_info_from_bushi_site(set_code: str) -> list[list[str]]:
    """Given a set id code, 
    retrieve the text of the official webpage,
    and break it into a list of area data,
    broken into smaller lists, creating a matrix of sorts.
    
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



def extract_data_from_bushi_site(test) -> dict[str:any]:
    """
    Given our "Data Matrix" from the Bushi site,

    neatly transform the raw data into a dictionary.

    "Neatly" is doing a lot of heavy lifting there, especially with how messy
    bushi can be with it. It's quite easy to throw errors in 'production'
    because bushi doesn't given the promos correct formatting.

    That being said, the general idea is to figure out what type of card we're
    working with, so we can know what to and not to convert to an int.

    The function is broken into sections based of which row of the data
    it's working on, to keep things organized and 'neat'.
    """
    data_entry = dict()
    data_entry['name'] = test[0]
    # Determine Card type
    card_type = test[1][0]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~Section 1~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # I was told not to delete unused code, but I think this is antiquated :/
    
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
