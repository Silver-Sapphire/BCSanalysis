

from os import path


import src.db_operations as db_operations
from src.feature_extraction import main as add_features


import pandas as pd

from bs4 import BeautifulSoup as Soup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions\
    import presence_of_element_located as present
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import requests

# EVENT = 'bcs2526-california'
# BASE_URL = "https://en.cf-vanguard.com/event/bcs2526/"
# URL = "https://en.cf-vanguard.com/event/bcs2526/bcs2526-california/"

# After creation, we've started tracking more data. 
# WOP: Updateing the function to work with this new input:
# Event info schema
# event_info =[
#     url_extension, # <- this was the original input
#     converted_name,
#     region,
#     date
# ]

# These are for indexing into the event info list object
URL_EXT = 0
NAME = 1
REGION = 2
DATE = 3


def get_decklogs(base_url, extension) -> pd.DataFrame:
    url = f'{base_url}{extension}'
    soup = Soup(requests.get(url).text, features='html.parser')
    rows = soup.table.find_all('tr')
    # Remove header row, so all rows have td, and not th
    rows.pop(0)

    dataDict = dict()
    
    for row in rows:
        # Decklog as the key
        key = row['data-deck-id']
        values = get_values(row.find_all('td'))
        values.append(key)
        values.append(None) # place holder

        dataDict[key] = values

    df = pd.DataFrame(dataDict).transpose()
    df = df.set_axis([
                        'rank',#
                        'name',
                        'boss',
                        'wins',#
                        'nation',
                        'decklog',
                        'deck'
                    ], 
                    axis=1)
    
    return df


def get_decks_from_decklogs(df):
    # Setup Chrome to run headless (without a visible window)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    # Initialize the browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                              options=chrome_options) 
    waiter = WebDriverWait(driver=driver, timeout=30)

    # Maybe we can set up a while loop to keep trying till we finish?
    # Go to each page
    DECKLOG_BASE_URL = "https://decklog-en.bushiroad.com/view/" 
    code = "None Added"
    for i, row in df.iterrows():
        # I've seen a few valid logs fail to make it through,
        # They usually just need a second try.
        tries = 0
        while tries < 3:
            tries += 1
            try:
                if df.at[i, 'deck'] != None: continue # skip completed decks on re-run
                code = df.at[i, 'decklog']
                url = DECKLOG_BASE_URL + str(code)
                driver.get(url)
                waiter.until(
                    present((By.CLASS_NAME, "card-controller"))
                )                
                html = driver.page_source
                deckSoup = Soup(html, features='html.parser')
                deckDict, boss = decklogToDict(deckSoup)
                df.at[i, 'deck'] = deckDict
                #TODO MAKE WORK WITH PREMIUM DECKS
                df.at[i, 'boss'] = boss
                
            except Exception as e:
                if tries == 3:
                    print(f"faild on deck {code} on try {tries}")
                # todo = df.deck.isnull().sum()
                # print(f'null decks: {todo}, \ncode: {code}','\n- - - - - - - - - - -')

    # clean-up
    print(df.deck.isnull().sum(), " empty decks collected")
    df.drop(columns=['index'], inplace=True, errors='ignore')
    driver.quit()

    return df


def save_to_seperate_db(df, event_info):
    # seperate db
    db = 'JSONproto'
    table = event_info[NAME]
    payload = df.to_dict(orient='records')
    db_operations.overwrite_table(database=db, table=table, payload=payload)


def save_to_main_table(df):
    # main db
    db = 'main_table'
    table = 'all_events'
    payload = df.to_dict(orient='records')
    db_operations.insert_into_table(database=db, table=table, payload=payload)


def save_to_local_json(df, event_info):
    # Save as Json localy
    file_path = path.join('.json', f'{event_info[NAME]}.json')
    df.to_json(file_path, orient='records')


def save_to_local_main_table(df):
    #extend local json save
    file = path.join('.json', 'ROADTRIP.json')
    full_df = pd.read_json(file)
    pd.concat([full_df, df]).to_json(file)


def reformat_df(df, event_info):
    # the rank and wins column need to be converted to ints,
    # and now we have some new attributes that need to be encoded.`
    df['rank'] = df['rank'].str[:-2].astype(int)
    df['wins'] = df['wins'].astype(int)
    df['location'] = event_info[NAME]
    df['region'] = event_info[REGION]
    df['date'] = event_info[DATE]

    return df


def main(base_url, event_info):
    """
    
    alias - get_data (used in our main file)
    """
    # Part 1: Get basic info and decklog from event page ~~~~~~~~~~~~~~~~~~~~~~
    raw_df = get_decklogs(base_url, event_info[URL_EXT])
    
    # Part 1.5 - Wrangle the data ~~~~~~~~~~~~~`
    deckless_df = reformat_df(raw_df, event_info)

    # Part 2: Get deck info from decklog ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ddf = get_decks_from_decklogs(deckless_df)

    # Part 2.5 - Remove rows with no deck ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ddf = ddf[~ddf.deck.isnull()]

    # Part 2.6 - Add Engineered Features ~~~~~
    df = add_features(ddf)

    # Part 3: Save Data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # for posterity, we'll save the data to two tables;
    # one for just this event, and one for all events.
    save_to_local_json(df, event_info)
    save_to_seperate_db(df, event_info)

    save_to_local_main_table(df)
    save_to_main_table(df)


    return None


def get_values(row):
    """This procederal function deals with the fact that the first 3 rows of
    the table have a slightly different structure than the rest.

    While I could write two functions, one for the first 3 rows, 
    and one for the rest, this just felt more simple and natural to write,
    allthough it's a bit tough to read.

    Our i counter being manual allows us to skip over the missing row
    for our top 3 players, while still keeping the incremental couting logic.

    Since the first 3 rows are a different size, 
    we need to adjust the amount of values, so our data frame is happy. 
    It ended up seeming simplest to just add `None` as we pass through
    """
    values=list()
    for i, item in enumerate(row):
        if i == 1: # This double conditional is true when the first 3 row's second element
            if item.div: # is a division, instead of text. we need to treat it different
                values.append("Champion") # we could extract the name, but it would be very complex
                values.append(None) # Add a none placeholder for our missing value
                continue # this continue statement seperates this special behaviour from the simple case

        values.append(row[i].text.strip())

    return values


def decklogToDict(soup):
    """
    TODO make work with premium
    
    Given the BeautifulSoup for a decklogs...
    """
    # Initialize the decks we return
    # We also retrive the boss, bc the top 3 decks lose that info
    boss = None
    rideDeckDict = dict()
    mainDeckDict = dict()
    gDeckDict = dict()
    deckDict = {
        'RideDeck': rideDeckDict,
        'MainDeck': mainDeckDict,
        'GDeck': gDeckDict
    }

    # obtain data from soup
    rows =  soup.find_all('div', 'row')
    rideDeck = rows[5].find_all('div', 'card-controller')
    mainDeck = rows[6].find_all('div', 'card-controller')
    if len(rows) == 8:
        gDeck = rows[7].find_all('div', 'card-controller')
    else:
        gDeck = None

    # pair soup data with dict
    decks = {
        "RideDeck": rideDeck, 
        "MainDeck": mainDeck,
        "GDeck": gDeck
    }

    # extract data from the soup into the dictionary
    for deck in deckDict:
        if not decks[deck]: continue
        for card in decks[deck]:
            spans = card.find_all('span')
            #########refactor point #############
            namespan= str(spans[0])
            start = 'title="'
            end = '"></span>'
            ststart = namespan.find(start) + len(start) #trim whitespace
            stend = namespan.find(end)    
            card_name_and_set_id = namespan[ststart:stend]       
            card_name = card_name_and_set_id
            #####################################
            quant = int(spans[1].text)
        
            if card_name in deckDict[deck]:
                deckDict[deck][card_name] += quant
            else:
                boss = boss or card_name
                deckDict[deck][card_name] =  quant
            
    return deckDict, boss

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NEW EVENT INFO SCRAOING TOOL
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def scrape_event_info():
    """
    This function is to prepare our event list for our main function.
    The output of this function is expected to be manually edited
    before being fed into main;
    ) Names need to be changed
    _ URLs need to be manually obtained from the event report site

    When re-using this function, start by changing the URL,
    and go from there. Good luck :P
    """

    URL = 'https://en.bushiroad.com/events/bcs2526/schedule/'
    request = requests.get(URL)
    soup=Soup(request.text, 'html.parser')

    region_map = {
        'regional-na': 'NA',
        'regional-eu': 'EU',
        'regional-asia': 'AO'
    }
    final_event_list = []
    # Credt: Geminin Pro
    # 3. Iterate through the defined regions
    for region_id, continent_code in region_map.items():
        # Find the main container for this specific continent
        region_container = soup.find('div', id=region_id)

        if not region_container:
            print(f"-> Info: Container for ID '{region_id}' ({continent_code}) not found in this HTML snippet. Skipping.")
            continue

        # print(f"-> Processing continent: {continent_code}")

        # 4. Find individual event cards within this region container.
        # In your HTML, every event seems to be wrapped in a div with class="event-card"
        event_cards = region_container.find_all('div', class_='event-card')

        for card in event_cards:
            # Extract Location Name
            # It looks like <h5 class="mb-0">City Name (Country)</h5>
            location_tag = card.find('h5', class_='mb-0')
            if location_tag:
                # .get_text(strip=True) removes surrounding whitespace and HTML tags
                location_name = location_tag.get_text(strip=True)
            else:
                # Fallback: try getting it from the data-city attribute if the h5 fails
                location_name = card.get('data-city', 'Unknown Location')

            # Extract Date
            # It looks like <p class="sm-txt schedule-date">Date Range</p>
            date_tag = card.find('p', class_='schedule-date')
            if date_tag:
                date_text = date_tag.get_text(strip=True)
            else:
                date_text = "Unknown Date"

            # Create the sublist [Location, Continent, Date]
            event_info = [location_name, continent_code, date_text]
            final_event_list.append(event_info)

    # print("\nExtraction complete. Here is your list:")
    # print("-" * 30)
    # # Pretty print the final list
    # for item in final_event_list:
        # print(item)

    # If you want to use this list later in the script, it is stored in `final_event_list`
    # print("\nRaw list output:")
    # print(final_event_list)# Credt: Geminin Pro
    # 3. Iterate through the defined regions
    for region_id, continent_code in region_map.items():
        # Find the main container for this specific continent
        region_container = soup.find('div', id=region_id)

        if not region_container:
            print(f"-> Info: Container for ID '{region_id}' ({continent_code}) not found in this HTML snippet. Skipping.")
            continue

        # print(f"-> Processing continent: {continent_code}")

        # 4. Find individual event cards within this region container.
        # In your HTML, every event seems to be wrapped in a div with class="event-card"
        event_cards = region_container.find_all('div', class_='event-card')

        for card in event_cards:
            # Extract Location Name
            # It looks like <h5 class="mb-0">City Name (Country)</h5>
            location_tag = card.find('h5', class_='mb-0')
            if location_tag:
                # .get_text(strip=True) removes surrounding whitespace and HTML tags
                location_name = location_tag.get_text(strip=True)
            else:
                # Fallback: try getting it from the data-city attribute if the h5 fails
                location_name = card.get('data-city', 'Unknown Location')

            # Extract Date
            # It looks like <p class="sm-txt schedule-date">Date Range</p>
            date_tag = card.find('p', class_='schedule-date')
            if date_tag:
                date_text = date_tag.get_text(strip=True)
            else:
                date_text = "Unknown Date"

            # Create the sublist [Location, Continent, Date]
            event_info = [location_name, continent_code, date_text]
            final_event_list.append(event_info)

    # print("\nExtraction complete. Here is your list:")
    # print("-" * 30)
    # # Pretty print the final list
    # for item in final_event_list:
        # print(item)

    # If you want to use this list later in the script, it is stored in `final_event_list`
    # print("\nRaw list output:")
    # print(final_event_list)

    return final_event_list

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# END TOOL
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    # print("""
    #     Ussage: main({circut event report base URL, event specific URL extension })
    #       """)
    import sys
    main(sys.argv[1], sys.argv[2])
