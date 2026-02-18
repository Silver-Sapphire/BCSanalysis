
import pandas as pd

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions\
    import presence_of_element_located as present
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from pymongo import MongoClient

# EVENT = 'bcs2526-california'
# BASE_URL = "https://en.cf-vanguard.com/event/bcs2526/"
# URL = "https://en.cf-vanguard.com/event/bcs2526/bcs2526-california/"


def main(base_url, event_url_string):
    """

    """
    # Part 1: Get basic info and decklog from event page ~~~~~~~~~~~~~~~~~~~~~~
    url = f'{base_url}{event_url_string}'
    soup = BeautifulSoup(requests.get(url).text, features='html.parser')
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
                        'rank',
                        'name',
                        'boss',
                        "wins",
                        'nation',
                        'decklog',
                        'deck'
                    ], 
                    axis=1)

    # Part 2: Get deck info from decklog ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
    todo = len(df)
    code = "None Added"
    for i, row in df.iterrows():
        # I've seen a few valid logs fail to make it through,
        # They usually just need a second try.
        tries = 0
        while tries < 2:
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
                deckSoup = BeautifulSoup(html, features='html.parser')
                deckDict, boss = decklogToDict(deckSoup)
                df.at[i, 'deck'] = deckDict
                #TODO MAKE WORK WITH PREMIUM DECKS
                df.at[i, 'boss'] = boss
                
            except Exception as e:
                todo = df.deck.isnull().sum()
                print(f'{e}, \n{todo}, \n{code}','\n~~~~~~~~~~~~~~~~~~~~~~~~~')

    # clean-up
    driver.quit()

    # Part 2.5 - Remove rows with no deck ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # df = df[~df.deck.isnull()]

    # Part 3: Save Data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Connect to MongoDB
    username = 'sjmichael17_db_user'
    password = 'rVtL43eBjseB5XkS' # plz don't hack me bro ;-;
    cluster_address = 'bcsproto.peazuyx.mongodb.net/?appName=BCSproto'

    client = MongoClient(f'mongodb+srv://{username}:{password}@{cluster_address}')

    db = client['JSONproto']
    collection = db[event_url_string]

    cleanDF = df.reset_index().rename(columns={'index':'_id'})
    collection.insert_many(cleanDF.to_dict(orient='records'))

    client.close()
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
    TODO make boss work with premium
    
    Given the BeautifulSoup for a decklogs...
    """
    # Initialize the decks we return
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
            namespan= str(spans[0])
            index1 = namespan.find(' : ') + 3 #trim whitespace
            index2 = namespan.find('"></span>')
            
            card_name = namespan[index1:index2]
            quant = int(spans[1].text)
        
            if card_name in deckDict[deck]:
                deckDict[deck][card_name] += quant
            else:
                boss = boss or card_name
                deckDict[deck][card_name] =  quant
            
    return deckDict, boss


if __name__ == "__main__":
    # print("""
    #     Ussage: main({circut event report base URL, event specific URL extension })
    #       """)
    import sys
    main(sys.argv[1], sys.argv[2])
