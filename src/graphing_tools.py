
#format_seperators.py

from os import path 

import src.db_operations as db_operations
import src.helpers as helpers

import pandas as pd
import matplotlib.pyplot as plt


def card_count_for_boss(card_name=None, boss_name=None, df=None, group_feature='cardAMT'):
    """
    Given a cardname for a boss in our df,  
    return a dataframe split based on the amount of that card in a deck.

    TODO, extract the group feature function to its own thing.
    This function is a bit specialezed. (#spe-L-ing)
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


def seperate_0_counts(df) -> tuple[pd.DataFrame]:
    """
    Seperates a datafrome with atribute 'cardAMT' into two df's,
    one where the count is 0, 
    and another where the card amount is 1 or more,

    Return them as a tuple of 2 dataframes;
      (with card, wihtout card)
    """
    haves =    df[df['cardAMT']>0]
    havenots = df[df['cardAMT']==0]
    return (haves, havenots)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~``

def graph_values(dfs:list[pd.DataFrame], str1='date',str2='mean', labels=[]):
    """
    Given a dataframe, and 2 attributes of it, and maybe some labels for the graph,
    plot the first 'str' arggument as the x, the second as y, add labels if given,

    create a small legend, and show the graph.

    It defaults to graphing the average date, which isn't very useful.
    """
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
    """
    given a full format df and a boss,
    return the df filted to only have the given boss, grouped by location
    (todo, make group featrue changeable?)

    Sort values, and then try to extract only the data we care about,
    so the data frame is easier to look out, without loads of redundant info
    """
    foo = full_df[full_df.boss == boss].groupby('location').describe()
    foo = foo.loc[:,[
        ('date','count'), 
        ('date','mean'), 
        ('wins','mean'), 
        ('stand_heal_count', 'mean')

        ]].sort_values(('date','mean'))
    
    return foo


def boss_avgs(df, bossname):
    """
    Given a dataframe and a boss name, 

    return a dataframe that shows the averages for the given boss grouped by the location,
    [location, date, count, avg_wins, avg_rs_heal]

    TODO!!!
    This, and the narrow_frame function should probably be reworked to allow for a passing
    of what features we want to avg, allowing for more flexibility.
    """
    foo = narrow_frame(df, bossname)
    foo.reset_index(inplace=True)
    foo.columns = ['location','date','count','avg_wins','avg_rs_heal']
    foo.loc[:, 'boss'] = bossname
    return foo

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def seperate_format(df, format) -> tuple[pd.DataFrame]:
    """
    Given a dataframe and a format (tuple[date, name]),
    
    split the df in two,
    one prior to the date of the format,
    and another leading from the start of that format, to the present.

    This will allow for a recusive call, to seperate each format one by one.

    (present-start, prior)
    """
    fdate = format[0]
    fdate = pd.to_datetime(fdate)
    prior = df[df['date'] < fdate]
    present = df[df['date'] >= fdate]

    return present, prior


def break_df_by_format(df, formats) -> list[pd.DataFrame]:
    """
    Given a data frame, and a list of formats list(tuple[date, name])

    return a list of data frames, broken up based on the formats.

    Unless the first format is before the first tournament,
    there will be one df per format, plus one with any dates prior to the first format.
    """
    format_dfs = []
    remaining = df.loc[:]
    for format in formats:
        present, prior = seperate_format(remaining, format)
        format_dfs.append(prior)
        remaining = present
        
    format_dfs.append(remaining)
    return format_dfs


def graph_over_format(df, split_metric, graph_metric, item_list, format_list):
    """
    Given a dataframe, a metric to aggregate the data on, another metric to graph on the y axis, 
    a list of our 'special format tuple list' to use to shape the x axis and group the dataq
    as well as a list of items from the first metric to graph, to prevent graphing an entire table.

    create a graph of how our split and graph metrics change over the formats.

    Not averaging out by format, and just graphing the events over time creates a lot of noise in the data.
    Using this to average out the data ofer the short stretches of time with the same legal cardpool
    allows for a smoother visualization of trends.

    This could do with a refactor.
    """
    format_dfs = break_df_by_format(df, format_list)

    for i, df in enumerate(format_dfs):
        tmp = df.groupby(split_metric).describe()
        format_dfs[i] = tmp

    metric_dfs = []
    for item in item_list:
        metric_data = []
        for df in format_dfs:
            if not df.empty:
                tmp = df.reset_index()
                metric_data.append(tmp[tmp[split_metric]==item])

        metric_dfs.append(pd.concat(metric_data))

    for df in metric_dfs:
        x=df['date']['mean']
        y=df[graph_metric]['mean']
        plt.plot(x, y, marker='o')

    plt.xlabel("Date")
    plt.ylabel(graph_metric)
    plt.title(f"{graph_metric} over time per {split_metric}")
    plt.legend(item_list, loc='best', fontsize='xx-small')
    plt.grid(True)

    plt.show()


def graph_card_peformance_for_boss(card, boss, df, formats):
    """
    Given a card name, a boss name, a data frame, and a list of format tuples,

    display a graph of the average win rate of each card amount,
    and a graph of the representation of each card amount.

    The results are only for the given boss, and graphed over time binned into the given formats.
    """
    boss_df = card_count_for_boss(card, boss, df)
    format_dfs = break_df_by_format(boss_df, formats)

    # Collect data for each format
    all_card_amounts = set()
    format_compositions = []  # List of dicts: {cardAMT: percentage}

    for format_df in format_dfs:
        if format_df.empty:
            continue

        # Count records in each cardAMT group
        composition = {}
        total_count = len(format_df)

        # Group by cardAMT and calculate percentages
        for card_amt, group in format_df.groupby('cardAMT'):
            count = len(group)
            composition[card_amt] = (count / total_count) * 100
            all_card_amounts.add(card_amt)

        format_compositions.append(composition)

    # Plot each card amount as a line
    for card_amt in sorted(all_card_amounts):
        percentages = [
            comp.get(card_amt, 0) for comp in format_compositions
        ]
        plt.plot(percentages, marker='o', label=f'{card_amt}')

    plt.xlabel("Format")
    plt.ylabel("Percentage of Decks (%)")
    plt.title(f"{card} in {boss} decks")
    plt.legend(loc='best', fontsize='small')
    plt.grid(True)
    plt.show()

    graph_over_format(
        boss_df, 
        'cardAMT', 
        'wins',
        [i for i in range(5)],
        formats
    )

     
def create_ratio_list(df: pd.DataFrame) -> list[float]:
    """
    Given a data frame, 
    return a list of ratios for the 'count' column.
    
    Ratio =  Total count of all columns / count for this onen column
    """
    total = int(df['rank']['count'].sum())
    ratios = []
    
    for row in df['rank']['count']:
        ratios.append(row / total)
    
    return ratios
 