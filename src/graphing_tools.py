
#format_seperators.py

from os import path 

import src.db_operations as db_operations
import src.helpers as helpers

import pandas as pd
import matplotlib.pyplot as plt


def card_count_for_boss(card_name=None, boss_name=None, df=None, group_feature='cardAMT'):
    """
    """
    if card_name == None:
        raise ValueError("Please provide a card name to analyze")
    
    if type(df) == type(None):
        pd.DataFrame(db_operations.get_table('main_table', 'all_events'))
    
    if boss_name != None:
        card_df = df[df.boss==boss_name]
    else:
        card_df = df.loc[:]

    
    card_df.loc[:, "cardAMT"] = card_df.deck.apply((lambda deck: helpers.card_type_in_deck(deck, [card_name])))
    # card_df = card_df[card_df['cardAMT'] > 0]
    # return card_df.groupby(group_feature).describe()
    return card_df


def seperate_0_counts(df):
    """
    Seperates a datafrome with atribute 'cardAMT' into two df's,
    one where the count is 0, and 
    """
    haves =    df[df['cardAMT']>0]
    havenots = df[df['cardAMT']==0]
    return (haves, havenots)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~``

def graph_values(dfs:list[pd.DataFrame], str1='date',str2='mean', labels=[]):
    for df in dfs:
        tmp=df.reset_index()
        plt.plot(tmp[str1],tmp[str2])

    
    plt.xlabel(str1)
    plt.ylabel(str2)
    plt.title(f'{str2} over {str1}')
    plt.legend(labels, loc=3, fontsize='x-small')
    plt.grid(True)

    plt.show()


def graph_mean_over_time(dfs):
    graph_values(dfs, 'date', 'mean', ['with', 'without', 'all'])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def narrow_frame(full_df, boss):
    foo = full_df[full_df.boss == boss].groupby('location').describe()
    foo = foo.loc[:,[('date','max'), ('date','count'), ('wins','mean'), ('stand_heal_count', 'mean')]].sort_values(('date','max'))
    return foo


def boss_avgs(df, bossname):
    foo = narrow_frame(df, bossname)
    foo.reset_index(inplace=True)
    foo.columns = ['location','date','count','avg_wins','avg_rs_heal']
    foo.loc[:, 'boss'] = bossname
    return foo

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def seperate_format(df, format) -> tuple[pd.DataFrame]:
    """
    return the format removed from the df, and the df without the removed format
    """
    fdate = format[0]
    fdate = pd.to_datetime(fdate)
    prior = df[df['date'] < fdate]
    present = df[df['date'] >= fdate]

    return present, prior


def break_df_by_format(df, formats) -> list[pd.DataFrame]:
    format_dfs = []
    remaining = df.loc[:]
    for format in formats:
        present, prior = seperate_format(remaining, format)
        format_dfs.append(prior)
        remaining = present
        
    format_dfs.append(remaining)
    return format_dfs


def graph_over_format(df, split_metric, graph_metric, item_list, format_list):
    format_dfs = break_df_by_format(df, format_list)

    for i, df in enumerate(format_dfs):
        tmp = df.groupby(split_metric).describe()
        format_dfs[i] = tmp

    metric_dfs = []
    for item in item_list:
        metric_data = []
        for df in format_dfs:
            tmp = df.reset_index()
            metric_data.append(tmp[tmp[split_metric]==item])

        metric_dfs.append(pd.concat(metric_data))

    for df in metric_dfs:
        test1=df['date']['mean']
        test2=df[graph_metric]['mean']
        plt.plot(test1, test2)

    plt.xlabel("Date")
    plt.ylabel(graph_metric)
    plt.title(f"{graph_metric} over time per {split_metric}")
    plt.legend(item_list, loc=3, fontsize='xx-small')
    plt.grid(True)

    plt.show()


def graph_card_peformance_for_boss(card, boss, df, formats):
    boss_df = card_count_for_boss(card, boss, df)
    graph_over_format(
        boss_df, 
        'cardAMT', 
        'wins',
        [i for i in range(5)],
        formats)