# get_table_from_db

import pandas as pd
from pymongo import MongoClient


# Connect to MongoDB
#TODO FIX SECURITY ISSUE
def get_table_from_db(database, table):
    """
    Returns an entire table from our database as a data frame.
    """
    username = 'sjmichael17_db_user'
    password = 'rVtL43eBjseB5XkS' # plz don't hack me bro ;-;
    cluster_address = 'bcsproto.peazuyx.mongodb.net/?appName=BCSproto'

    client = MongoClient(f'mongodb+srv://{username}:{password}@{cluster_address}')

    db = client[database]
    collection = db[table]

    full_df= pd.DataFrame(collection.find({}))

    client.close()

    return full_df


def get_answer_from_table(database, table, query):
    """
    Instead of finding all of a table, finds a given query.

    ex: {'boss': 'Sugary and Scary Land, Heartluru'}
    ex. {}
    """
    username = 'sjmichael17_db_user'
    password = 'rVtL43eBjseB5XkS' # plz don't hack me bro ;-;
    cluster_address = 'bcsproto.peazuyx.mongodb.net/?appName=BCSproto'

    client = MongoClient(f'mongodb+srv://{username}:{password}@{cluster_address}')

    db = client[database]
    collection = db[table]

    full_df= pd.DataFrame(collection.find(query))

    client.close()

    return full_df
