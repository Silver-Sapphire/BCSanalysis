# get_table_from_db

"""
Dev Notes:

I don't like how each command connects, does it's 'thing', then closes.

If they all do the first and last thing, can we make some way of passing in
'the thing'?
"""

import pandas as pd
from pymongo import MongoClient


#TODO FIX SECURITY ISSUES
USERNAME = 'sjmichael17_db_user'
PASSWORD = 'rVtL43eBjseB5XkS' # plz don't hack me bro ;-;
CLUSER_ADDRESS = 'bcsproto.peazuyx.mongodb.net/?appName=BCSproto'

DEFAULT_DB = 'main_table'
DEFAULT_TABLE = 'all_events'

def connect_to_db(database=DEFAULT_DB, table=DEFAULT_TABLE) -> tuple[MongoClient, None]:
    """
    Returns a client connection to close later, and a target table from our db.
    """
    client = MongoClient(f'mongodb+srv://{USERNAME}:{PASSWORD}@{CLUSER_ADDRESS}')
    db = client[database]
    collection = db[table]

    return client, collection



def get_table(database=DEFAULT_DB, table=DEFAULT_TABLE):
    """
    Returns an entire table from our database as a data frame.
    """

    return get_answer_from_table(database, table, query={})



def get_answer_from_table(database=DEFAULT_DB, table=DEFAULT_TABLE, query={}):
    """
    Instead of finding all of a table, finds a given query.

    ex: {'boss': 'Sugary and Scary Land, Heartluru'}
    ex. {}
    """
    client, collection = connect_to_db(database, table)

    full_df= pd.DataFrame(collection.find(query))

    client.close()
    return full_df



def find_first_in_table(database=DEFAULT_DB, table=DEFAULT_TABLE, query=None):
    """
    Returns the first element that fits a query
    """
    if query==None: raise ValueError("Input a query as 3rd arg.")
    client, collection = connect_to_db(database, table)

    item_dict= collection.find_one(query)

    client.close()
    return item_dict




def insert_one_into_table(database, table, payload):
    """
    
    """
    client, collection = connect_to_db(database, table)

    collection.insert_one(payload)

    client.close()
    return None



def insert_many_into_table(database, table, payload):
    """
    TODO move logic implemented elsewhere.
    """
    return insert_into_table(database, table, payload)



def insert_into_table(database, table, payload):
    """
    aka insert many into table
    TODO move logic implemented elsewhere. here..?
    """
    client, collection = connect_to_db(database, table)

    collection.insert_many(payload)

    client.close()
    return None



def overwrite_table(database, table, payload):
    """
    
    """
    client, collection = connect_to_db(database, table)

    collection.drop()
    collection.insert_many(payload)

    client.close()
    return None



def update_table(database, table, updates):
    """
    
    """
    client, collection = connect_to_db(database, table)

    collection.bulk_write(updates)

    client.close()
    return None



def aggregate_table(database, table, aggregate):
    """
    
    """
    client, collection = connect_to_db(database, table)

    col = collection.aggregate(aggregate)

    client.close()
    return col
