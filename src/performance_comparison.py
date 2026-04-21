
#performance_comparison.py

from collections import defaultdict

import card_data_collection_pipeline
import db_operations
import helpers

import pandas as pd


def db_lookup(id_and_name):
    id = helpers.extract_card_id(id_and_name)
    return db_operations.find_first_in_table('main_table', 'card_data', {'id':id})


def url_lookup(id_and_name):
    id = helpers.extract_card_id(id_and_name)
    return card_data_collection_pipeline.add_card_info_to_db(id) 


def card_amt_for_boss(df=None, bossname=None, cardname=None):
    if df == None & bossname != None:
        foo = db_operations.get_answer_from_table(query=
                                                 {'boss':
                                                    {'$regex':bossname}
                                                 })
    foo=pd.DataFrame()
    foo = df.apply(
        lambda deck: helpers.card_type_in_deck(
            deck, [cardname]
        ))
    return foo


def main(full_df):
    memoizer = memoizer or dict()
    copy = full_df
    for i, row in full_df.iterrows():
        new_deck = defaultdict(int)
        for card_id_and_name, amount in row.deck['MainDeck'].items():
            id = helpers.extract_card_id(card_id_and_name)
            try:
                if memoizer[id]:
                    lookup = memoizer[id]
            except KeyError:
                lookup = None

            if not lookup:
                lookup = db_lookup(card_id_and_name)
                memoizer[id] = lookup
            if not lookup:
                lookup = url_lookup( card_id_and_name)
                memoizer[id] = lookup

            name = lookup['name']

            if 'Trigger' in lookup['type']:
                if 5000 == lookup['power']:
                    name = 'Vanilla Trigger'

            if '[CONT]:Sentinel' in lookup['effect']:
                if 'Unit' in lookup['type']:
                    name = 'Sentinel'
                else:
                    name = 'Elementaria'

            if '[CONT]:This card is' in lookup['effect']:
                first = lookup['effect'].find('"')+1
                second = lookup['effect'].find('"', first)
                name = lookup['effect'][first:second]

            new_deck[name] += amount
        
        copy.at[i, 'deck']['MainDeck'] = new_deck

        WINS = 5
        top_df = full_df[full_df['wins'] > WINS]
        bot_df = full_df[full_df['wins'] <= WINS]

        top_dict = defaultdict(int)
        bot_dict = defaultdict(int)
        all_dict = defaultdict(int)

        for dict in top_df.deck:
            for k, v in dict['MainDeck'].items():
                top_dict[k] += v
                all_dict[k] += v

        for dict in bot_df.deck:
            for k, v in dict['MainDeck'].items():
                bot_dict[k] += v
                all_dict[k] += v
        
        num_tops = len(top_df)
        num_bots = len(bot_df)
        num_total = num_tops + num_bots

        top_dict = {k: v / num_tops for k,v in top_dict.items()}
        bot_dict = {k: v / num_bots for k,v in bot_dict.items()}
        all_dict = {k: v / num_total for k,v in all_dict.items()}

        top_dict = {k:v for k,v in sorted(top_dict.items(), key=lambda k: k[1], reverse=True)}
        bot_dict = {k:v for k,v in sorted(bot_dict.items(), key=lambda k: k[1], reverse=True)}
        all_dict = {k:v for k,v in sorted(all_dict.items(), key=lambda k: k[1], reverse=True)}

        
        diff_dict = defaultdict(int)
        for k, v in all_dict.items():
            try:
                diff_dict[k] = top_dict[k] - v
            except:
                continue

        diff_dict = {k:v for k,v in sorted(diff_dict.items(), key=lambda k: k[1], reverse=True)}

        return diff_dict