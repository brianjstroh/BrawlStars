# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 12:22:10 2021

@author: brian
"""
import requests
import json
import os
import time
import pandas as pd
import numpy as np
import pickle
import psycopg2
from sqlalchemy import create_engine

def load_json(battle_logs, directory):
    for subdir, dirs, files in os.walk(directory):
        for filename in files:
            filepath = subdir + '/' + filename
            if filepath.endswith(".json"):
                with open(filepath) as f:
                    try:
                        data = json.load(f)
                        battle_logs['#' + filename[2:-5]] = data['items']
                    except Exception as e:
                        print(str(e) + ' not found in ' + str(filename))
                        pass
    return(battle_logs)

def curr_team_won(curr_player, first_team):
    for player in first_team:
        if player['tag'] == curr_player:
            return(True)
    return(False)

def parse_battles(player_id, battle_logs):
    my_dict = {}
    #Note: bigGame and roboRumble modes do not have win data
    for battle in battle_logs[player_id]:
        try:
            #print(battle)
            #print('\n\n')
            curr_mode = battle['battle']['mode']    #Pull mode from battle instead of event because event isn't always populated
            curr_map = battle['event']['map']
            curr_time = battle['battleTime']
            #Teams not ordered by team that won.
            if curr_mode in ['gemGrab', 'bounty', 'knockout', 'heist', 'siege', 'hotZone', 'brawlBall', 'presentPlunder']:
                first_team_won = curr_team_won(player_id, battle['battle']['teams'][0]) == (battle['battle']['result'] == 'victory')
                for curr_team in range(len(battle['battle']['teams'])):
                    win = first_team_won == (curr_team == 0)
                    for curr_player in range(len(battle['battle']['teams'][curr_team])):
                        player = battle['battle']['teams'][curr_team][curr_player]['tag']
                        idx = curr_time + player
                        brawler = battle['battle']['teams'][curr_team][curr_player]['brawler']['name']
                        
                        #tournament type battles don't have trophies
                        try:
                            trophies = battle['battle']['teams'][curr_team][curr_player]['brawler']['trophies']
                        except:
                            trophies = None
                        #print(idx + ' ' + curr_mode + ' ' + curr_map + ' ' + player + ' ' + brawler + ' ' + str(trophies) + ' ' + str(win))
                        my_dict[idx] = {'mode': curr_mode, 'map': curr_map, 'time': curr_time, 'player': player, 'brawler': brawler, 'trophies': trophies, 'win': win*1, 'rank': None}
            #Rank data sorted by order within the players list.
            elif curr_mode in ['soloShowdown', 'loneStar']:
                for curr_player in range(len(battle['battle']['players'])):
                    player = battle['battle']['players'][curr_player]['tag']
                    idx = curr_time + player
                    brawler = battle['battle']['players'][curr_player]['brawler']['name']
                    rank = curr_player + 1
                        
                    #tournament type battles don't have trophies
                    try:
                        trophies = battle['battle']['players'][curr_player]['brawler']['trophies']
                    except:
                        trophies = None
                    #print(idx + ' ' + curr_mode + ' ' + curr_map + ' ' + player + ' ' + brawler + ' ' + str(trophies) + ' ' + str(rank))
                    my_dict[idx] = {'mode': curr_mode, 'map': curr_map, 'time': curr_time, 'player': player, 'brawler': brawler, 'trophies': trophies, 'win': None, 'rank': rank}
            #Rank data sorted by order within the teams list.
            elif curr_mode == 'duoShowdown':
                for curr_team in range(len(battle['battle']['teams'])):
                    for curr_player in range(len(battle['battle']['teams'][curr_team])):
                        player = battle['battle']['teams'][curr_team][curr_player]['tag']
                        idx = curr_time + player
                        brawler = battle['battle']['teams'][curr_team][curr_player]['brawler']['name']
                        rank = curr_team + 1
                        
                        #tournament type battles don't have trophies
                        try:
                            trophies = battle['battle']['teams'][curr_team][curr_player]['brawler']['trophies']
                        except:
                            trophies = None
                        #print(idx + ' ' + curr_mode + ' ' + curr_map + ' ' + player + ' ' + brawler + ' ' + str(trophies) + ' ' + str(rank))
                        my_dict[idx] = {'mode': curr_mode, 'map': curr_map, 'time': curr_time, 'player': player, 'brawler': brawler, 'trophies': trophies, 'win': None, 'rank': rank}
            elif curr_mode in ['bossFight', 'bigGame']:
                win = battle['battle']['result'] == 'victory'
                for curr_player in range(len(battle['battle']['players'])):
                    player = battle['battle']['players'][curr_player]['tag']
                    idx = curr_time + player
                    brawler = battle['battle']['players'][curr_player]['brawler']['name']
                        
                    #tournament type battles don't have trophies
                    try:
                        trophies = battle['battle']['players'][curr_player]['brawler']['trophies']
                    except:
                        trophies = None
                    #print(idx + ' ' + curr_mode + ' ' + curr_map + ' ' + player + ' ' + brawler + ' ' + str(trophies) + ' ' + str(win))
                    my_dict[idx] = {'mode': curr_mode, 'map': curr_map, 'time': curr_time, 'player': player, 'brawler': brawler, 'trophies': trophies, 'win': win*1, 'rank': None}
            else:    
                print(battle['battle']['mode'])
        except:
            try:
                if battle['battle']['type'] != 'friendly':
                    print(battle)
            except:
                print(battle['battle']['mode'])
                pass
            pass
    return(my_dict)

def get_pop_win_rates(df, my_mode, my_map, trophy_min = 550, rank_threshold = 5):
    win_rates = df[df['trophies'] >= trophy_min]
    win_rates = win_rates.groupby(['mode', 'map']).get_group((my_mode, my_map))[['win', 'rank', 'brawler']]
    if my_mode not in ['soloShowdown', 'duoShowdown', 'loneStar']:
        win_rates['win'] = pd.to_numeric(win_rates['win'])
        win_rates = win_rates.groupby('brawler')['win'].agg(['mean', 'count'])
    else:
        win_rates['is_win'] = np.where(win_rates['rank'] <= rank_threshold, 1, 0)
        win_rates = win_rates.groupby('brawler')['is_win'].agg(['mean', 'count'])
    win_rates = win_rates.sort_values(by = 'mean', ascending = False)
    win_rates.columns = ['win_rate', 'matches_played']
    return(win_rates)

def get_player_win_rates(df, player, my_mode, my_map, trophy_min = 550, rank_threshold = 5):
    win_rates = df[df['player'] == player]
    win_rates = win_rates[win_rates['trophies'] >= trophy_min]
    win_rates = win_rates.groupby(['mode', 'map']).get_group((my_mode, my_map))[['win', 'rank', 'brawler']]
    if my_mode not in ['soloShowdown', 'duoShowdown', 'loneStar']:
        win_rates['win'] = pd.to_numeric(win_rates['win'])
        win_rates = win_rates.groupby('brawler')['win'].agg(['mean', 'count'])
    else:
        win_rates['is_win'] = np.where(win_rates['rank'] <= rank_threshold, 1, 0)
        win_rates = win_rates.groupby('brawler')['is_win'].agg(['mean', 'count'])
    win_rates = win_rates.sort_values(by = 'mean', ascending = False)
    win_rates.columns = ['win_rate', 'matches_played']
    return(win_rates)

def parse_tags(raw_tags):
    return([tag.replace('#', '%23') for tag in raw_tags])

def get_daily_extract():
    MY_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjNmMTRmNWNkLWFlZTUtNDI4Yy1hZWRlLTFjMjQ3N2ExODMwNyIsImlhdCI6MTU5OTkyODY4OCwic3ViIjoiZGV2ZWxvcGVyLzE5OWFiZTVkLTE4YWMtNDA3Ni03MDBjLWIzZDkxNjRiM2M3YiIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMjQuMTcuMTI5LjcxIl0sInR5cGUiOiJjbGllbnQifV19.6Ai-uFT_csb3pcttwVWqGx-bKfa3ZDUryRC8Pvd6d1DXsrBxrmommHQmj0Wc9FtWnjyOGyCsOZU5uxfTeGR06g'
    headers = {"Authorization": "Bearer " + MY_KEY}
    year, month, day, hour, minute = map(int, time.strftime("%Y %m %d %H %M").split())
    date_path = './Data/' + str(month) + str(day) + str(year) + '/'
    
    #Get top 200 clubs
    url = 'https://api.brawlstars.com/v1/rankings/global/clubs'
    response = requests.get(url, headers=headers)
    clubs = response.json()['items']
    club_tags = [club['tag'] for club in clubs]
    club_tags = [tag.replace('#', '%23') for tag in club_tags]
    club_tags.append('%239C02QJ0') #Add my club
    
    member_tags = []
    for club in club_tags:
        url = 'https://api.brawlstars.com/v1/clubs/' + club
        response = requests.get(url, headers=headers)
        members = response.json()['members']
        new_tags = parse_tags([member['tag'] for member in members])
        member_tags.extend(new_tags)
    member_tags
    
    os.mkdir(date_path)
    
    #Get and store raw json data
    print('start time: ' + str(time.perf_counter()))
    for member in member_tags:
        url = 'https://api.brawlstars.com/v1/players/' + member + '/battlelog'
        response = requests.get(url, headers=headers)
        with open(date_path + member[1:] + '.json', 'w') as outfile:
            json.dump(response.json(), outfile)
    print('end time: ' + str(time.perf_counter()))
    
def make_local_pickle_database(data_directories):
    database_path = './Data/database'
    
    temp_df = {}
    for directory in data_directories:
    
        battle_logs = {}
        battle_logs = load_json(battle_logs, directory)
        
        my_keys = list(battle_logs.keys())
        for key in my_keys:
            temp_df.update(parse_battles(key, battle_logs))
        
        df = pd.DataFrame(temp_df).T
        if os.path.exists(database_path):
            file = open(database_path, 'rb')
            df_prior = pickle.load(file)
            file.close()
            df = df_prior.append(df)
            
        df.drop_duplicates(keep = 'first', inplace = True)
        
        file = open(database_path, 'wb')
        pickle.dump(df, file)
        file.close()
        
        all_map_modes = df.groupby(['mode', 'map']).agg('count')
        file = open('./Data/all_map_modes', 'wb')
        pickle.dump(all_map_modes, file)
        file.close()

def sql_delete_duplicates(connection_string):
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    query = """
            DROP TABLE IF EXISTS records_unique;
            CREATE TABLE records_unique (LIKE records);
            INSERT INTO records_unique SELECT idx, mode, map, match_time, player_id, brawler, trophies, win, showdown_rank FROM
              (SELECT *, ROW_NUMBER() OVER 
            (PARTITION BY (idx) ORDER BY idx DESC) rn
               FROM records
              ) tmp WHERE rn = 1;
            ALTER TABLE records RENAME TO records_old;
            ALTER TABLE records_unique RENAME TO records;
            DROP TABLE records_old;
            """
    cursor.execute(query)
    connection.commit()
    
    #Close the connection
    cursor.close()
    connection.close()
    
def to_sql(params, df):
    df = df.reset_index()
    df = df.astype(object).where(pd.notnull(df), None)
    df.columns = ['idx', 'mode', 'map', 'match_time', 'player_id', 'brawler', 'trophies', 'win', 'showdown_rank']
    
    connect = "postgresql+psycopg2://%s:%s@%s:5432/%s" % (
        params['user'],
        params['password'],
        params['host'],
        params['database']
    )
    engine = create_engine(connect)
    df.to_sql(
        'records', 
        con=engine,
        index = False,
        if_exists = 'append',
        chunksize = 500000
    )
    return(True)
