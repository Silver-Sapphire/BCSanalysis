
#feature_extraction.py

from os import path

import src.db_operations as db_operations
import src.helpers as helpers

import pandas as pd


STAND_HEALS = [
    "Stealth Fiend, Amaviera",
    "Incorruptible Holy Light, Eufha",
    "Lady Healer of the Creaking World",
    "Invigorate Sage",
    "Zypsophila Fairy, Asher",
    "Two Of Us, Rhyme",
]

CRIT_HEALS = [
    'Cure Flare Dracokid',
    'Brilliant Floral, Uania',
    'Whistling Arrow of Recursion, Obifold',
    'Heartiness Tear Sorceress',
    'Alchemic Hedgehog',
    'Two Of Us, Flow',
]

DRAWS = [
    'Flare Veil Dragon',
    'Rouse Wildmaster, Riley',
    'Ameliorate Connector',
    'Protection Magic, Prorobi',
    'Serene Maiden, Lena',
    'Transparent Snowy Night, Beretoi',
]

SHIED_FRONTS = [
    'Blaze Maiden, Parama',
    'Diabolos Girls, Natalia',
    'Cardinal Draco, Enpyro',
    'Bard of Heavenly Song, Alpacc',
    'Frenzied Heiress',
    'Snowskip, Palv',
]

SOUL_FRONTS = [
    'Stealth Fiend, Futakuchiyo',
    'Strange Noise of Ruin, Adore',
    'Endearing Vendor, Mateyna',
    'Divine Sister, Natilla',
    'Tear Knight, Rothion',
    'Spiny∧Spiky, Heis',
]

OVER = [
    'Dragon Deity King of Resurgence, Dragveda',
    'Hades Dragon Deity of Resentment, Gallmageheld',
    'Terrifying Wicked Dragon King, Vamfrieze',
    'Star Dragon Deity of Infinitude, Eldobreath',
    'Light Dragon Deity of Honors, Amartinoa',
    'True Arbiter Dragon of Hundred Swords, Duralvalse',
    'Source Dragon Deity of Blessings, Blessfavor',

    #Lyrical....
    'Greatest Star, Esteranza',
    'Demonic Fever, Garviera',
    'Blessing Diva, Grizael',
    'Fantastic Fur-nale, Catrina',
    'Mysterious Twins, Romia & Rumia',

    #Red Re-skins
    'Great Dragon Emperor of Distant Blaze, Gidoradevalt', #de
    'Sword Emperor Dragon of Supreme Karma, Mordigarra', #ds
    'Ancestral Dragon King of Zenith Colors, Founaherdio', #st
    'Star Quake Dragon of Destroyer Zenith, Vazgueis', #bg
    'Beauteous Eternity, Lururatye', #ls
    'Sage Dragon Emperor of Brave Passion, Coreodigras', #ks

    # 'Generic'
    # 'olbiron's....TODO??
    'Spiritual King of Ignition, Valnout',
    'Spiritual King of Aquatics, Idosfaro',
    'Spiritual King of Brightsky, Meridzanblia',
    'Spiritual King of Nightsky, Nyxlaszelia',
    'Spiritual King of Tempestorm, Violeurm',

    #token ranbu
    'Shichiseiken',
    'Heishishourinken',
    'Kashuu Kiyomitsu Shinken Hissatsu',
    'Kasen Kanesada Shinken Hissatsu',
    'Mutsunokami Yoshiyuki Shinken Hissatsu',
    'Yamanbagiri Kunihiro Shinken Hissatsu',
    'Hachisuka Kotetsu Shinken Hissatsu',

    #cc
    #cc
    'CoroCoro Comic',
    #red
    "'Fiery Dodgeball Girl, Dodge Danko', Dodge Danko",
    #blue
    "'Future Card God Buddyfight', Yuga & Garga",

    #bangdream
    'End of a Camp of Acceptancd for the Five',
    'Starting to Move On for the Five Who Are Lost',
    'Even if This Destiny Was Predetermined',

    #shamen
    'The Close Pair Under the Moonlit Night',
    'Over Soul Strike!',
    #rag
    'Ragnarok',
    # 'The Moment History is Transformed',
    #bf
    'Future Card Buddyfight'
]

OVER_MAP = {
    'Dragon Deity King of Resurgence, Dragveda':"Dragveda",
    'Hades Dragon Deity of Resentment, Gallmageheld':"DS OT",
    'Terrifying Wicked Dragon King, Vamfrieze':"DS OT",
    'Star Dragon Deity of Infinitude, Eldobreath':'Eldobreath',
    'Light Dragon Deity of Honors, Amartinoa':'Keter OT',
    'True Arbiter Dragon of Hundred Swords, Duralvalse':'Keter OT',
    'Source Dragon Deity of Blessings, Blessfavor':'Blessfavor',

    #Lyrical....
    'Greatest Star, Esteranza':'Lyrical',
    'Demonic Fever, Garviera':'Lyrical',
    'Blessing Diva, Grizael':'Lyrical',
    'Fantastic Fur-nale, Catrina':'Lyrical',
    'Mysterious Twins, Romia & Rumia':'Lyrical',

    #Red Re-skins
    'Great Dragon Emperor of Distant Blaze, Gidoradevalt':'Red', #de
    'Sword Emperor Dragon of Supreme Karma, Mordigarra':'Red', #ds
    'Star Quake Dragon of Destroyer Zenith, Vazgueis':'Red', #bg
    'Sage Dragon Emperor of Brave Passion, Coreodigras':'Red', #ks
    'Ancestral Dragon King of Zenith Colors, Founaherdio':'Red', #st
    'Beauteous Eternity, Lururatye':'Red', #ls

    # 'Generic'
    # 'olbiron's....
    'Spiritual King of Ignition, Valnout':'Red',
    'Spiritual King of Aquatics, Idosfaro':'Blue',
    'Spiritual King of Brightsky, Meridzanblia':'Yellow',
    'Spiritual King of Nightsky, Nyxlaszelia':'Purple',
    'Spiritual King of Tempestorm, Violeurm':'Green',

    #token ranbu
    'Shichiseiken':"Shichi",
    'Heishishourinken':"Heishi",
    'Kashuu Kiyomitsu Shinken Hissatsu':'Order',
    'Kasen Kanesada Shinken Hissatsu':'Order',
    'Mutsunokami Yoshiyuki Shinken Hissatsu':'Order',
    'Yamanbagiri Kunihiro Shinken Hissatsu':'Order',
    'Hachisuka Kotetsu Shinken Hissatsu':'Order',

    #cc
    #cc
    'CoroCoro Comic':"CoroCoro",
    #red
    "'Fiery Dodgeball Girl, Dodge Danko', Dodge Danko":"Red",
    #blue
    "'Future Card God Buddyfight', Yuga & Garga":"Blue",
    
    #bangdream
    'End of a Camp of Acceptancd for the Five':"Bang",
    'Starting to Move On for the Five Who Are Lost':"Bang",
    'Even if This Destiny Was Predetermined':"Bang",

    #shamen
    'The Close Pair Under the Moonlit Night':"Shamen",
    'Over Soul Strike!':"Shamen",
    #rag
    'Ragnarok':"Ragnarok",
    # 'The Moment History is Transformed',
    #bf
    'Future Card Buddyfight':"Buddyfight",

}

REGALIS = [
    "Primordial Heartblaze",
    "Shroud in Darkness",
    "Sound of Wave",
    "Fire Regalis",
    "Union the Sky",
    "Protection: Twincast",
    "Radiance Caliburn",
    "Bracing Angel Ladder",
    "Forbidoll Surrogate",  "'Mysterious Joker' Joker",
    "Evergreen Transhpere", "'Homeroom-Ninja Mr. Shinobu' Mr. Shinobu",
    "Gratias Gradale",      "'Croket!' Croket",
]

REGALIS_MAP = {
    "Primordial Heartblaze": None,
    "Shroud in Darkness": None,
    "Sound of Wave": None,
    "Fire Regalis": None,
    "Union the Sky": None,
    "Protection: Twincast": None,
    "Radiance Caliburn": None,
    "Bracing Angel Ladder": None,
    "Forbidoll Surrogate": None,  
    "'Mysterious Joker' Joker": "Forbidoll Surrogate",
    "Evergreen Transhpere": None, 
    "'Homeroom-Ninja Mr. Shinobu' Mr. Shinobu": "Evergreen Transhpere",
    "Gratias Gradale": None,      
    "'Croket!' Croket": "Gratias Gradale",
}

def extract_via_map(decks_dict, card_list, card_map):
    for card_name in card_list:
        if helpers.card_count_in_deck(decks_dict, card_name):
            if card_map[card_name] != None:
                return card_map[card_name]
            else:
                return card_name
        
    return "None"



def main(full_df):
    full_df.loc[:,'stand_heals']      = full_df.deck.apply(lambda deck: helpers.card_type_in_deck(deck, STAND_HEALS))
    full_df.loc[:,'crit_heals']       = full_df.deck.apply(lambda deck: helpers.card_type_in_deck(deck, CRIT_HEALS))

    full_df.loc[:,'sheild_draws']     = full_df.deck.apply(lambda deck: helpers.card_type_in_deck(deck, DRAWS))
    full_df.loc[:,'shield_fronts']    = full_df.deck.apply(lambda deck: helpers.card_type_in_deck(deck, SHIED_FRONTS))
    full_df.loc[:,'soul_fronts']      = full_df.deck.apply(lambda deck: helpers.card_type_in_deck(deck, SOUL_FRONTS))

    full_df.loc[:, 'regalis_piece']   = full_df.deck.apply(lambda deck: extract_via_map(deck, REGALIS, REGALIS_MAP))
    full_df.loc[:, 'over_trigger']    = full_df.deck.apply(lambda deck: extract_via_map(deck, OVER, OVER_MAP))
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    full_df.loc[:, 'boss']            = full_df.boss.apply(lambda boss: helpers.extract_card_name(boss))

    return full_df