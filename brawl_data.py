# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 12:22:10 2021

@author: brian
"""
import os
import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportion_confint
import psycopg2
from sqlalchemy import create_engine

def get_recommendation(connection_string, my_id, my_mode, my_map, my_trophies = 'high'):
    #Set tables to collect from
    ind_table = 'individual_aggs_' + my_trophies
    pop_table = 'population_aggs_' + my_trophies
     
    #Get population results
    pop = sql_get_results(connection_string, pop_table, my_mode, my_map, my_trophies)
    pop = sql_get_results(connection_string, pop_table, my_mode, my_map, my_trophies)
    pop['win_rate'] = pop['wins'] / pop['matches_played']
    
    #Get player results and calculate win rate confidence intervals
    df = sql_get_results(connection_string, ind_table, my_mode, my_map, my_trophies, my_id)
    
    #Add empty row so player columns are retained
    if df.empty:
        df = df.append(pd.Series(), ignore_index=True)    
    df['win_rate'] = df['wins'] / df['matches_played']
    df['ci.lower'],df['ci.upper'] = zip(*df.apply(lambda row : proportion_confint(count = row['wins'], nobs = row['matches_played'], alpha = .1, method = 'agresti_coull'), axis = 1))

    #Merge population data with individual data
    df = pop.merge(df, how = 'left', left_on = 'brawler', right_on = 'brawler')
    
    #Compare population to individual history and inform recommendation
    better = (df['win_rate_x'] < df['ci.lower']) & (df['matches_played_y'] >= 5)
    worse = (df['win_rate_x'] > df['ci.upper']) & (df['matches_played_y'] >= 5)
    df['reason'] = 'Population win rate'
    df.loc[better,'reason'] = 'Outperforming population win rate'
    df.loc[worse,'reason'] = 'Underperforming population win rate'
    df['estimated_win_rate'] = df['win_rate_x']
    df.loc[better,'estimated_win_rate'] = df.loc[better,'win_rate_y']
    df.loc[worse,'estimated_win_rate'] = df.loc[worse,'win_rate_y']
    df = df[['map_x', 'mode_x', 'brawler', 'estimated_win_rate', 'win_rate_x', 'win_rate_y', 'wins_y', 'matches_played_y', 'ci.lower', 'ci.upper', 'reason']].sort_values(by = 'estimated_win_rate', ascending = False)
    df.columns = ['Map', 'Mode', 'Brawler', 'Estimated Win Rate', 'Population Win Rate', 'Your Win Rate', 'Your Wins', 'Your Matches Played', 'Estimated Lower Bound', 'Estimated Upper Bound', 'Reason']
    to_percent = ['Estimated Win Rate', 'Population Win Rate', 'Your Win Rate', 'Estimated Lower Bound', 'Estimated Upper Bound']
    for col in to_percent:
        df[col] = pd.Series(["{0:.2f}%".format(num * 100) for num in df[col]], index=df.index)
    no_decimals = ['Your Wins', 'Your Matches Played']
    for col in no_decimals:
        df[col] = pd.Series(["{0:.0f}".format(num) for num in df[col]], index=df.index)
    df = df.replace(to_replace='nan%', value='-').replace(to_replace='nan', value='-')
    return(df)

def get_all_recommendations(connection_string, my_id, my_trophies='high'):
    #Set tables to collect from    
    ind_table = 'individual_aggs_' + my_trophies
    pop_table = 'population_aggs_' + my_trophies
    
    #Get player results
    query = "SELECT mode, map, brawler,"
    query += " SUM(wins) as wins,"
    query += " SUM(matches_played) AS matches_played"
    query += " FROM " + ind_table
    query += " WHERE player_id = '" + my_id + "'"
    query += " GROUP BY mode, map, brawler;"
    
    #Get individual data
    df = sql_get_results(connection_string, ind_table, '', '', '', my_id, custom_query = query)
    
    #Calculate win rate confidence intervals
    df['win_rate'] = df['wins'] / df['matches_played']
    df['ci.lower'],df['ci.upper'] = zip(*df.apply(lambda row : proportion_confint(count = row['wins'], nobs = row['matches_played'], alpha = .1, method = 'agresti_coull'), axis = 1))
    
    #Get population data
    pop_query = "SELECT mode, map, brawler,"
    pop_query += " SUM(wins) as wins,"
    pop_query += " SUM(matches_played) AS matches_played"
    pop_query += " FROM " + pop_table
    pop_query += " GROUP BY mode, map, brawler;"
    pop = sql_get_results(connection_string, pop_table, '', '', '', my_id, custom_query = pop_query)
    pop['win_rate'] = pop['wins'] / pop['matches_played']
    df = pop.merge(df, how = 'left', left_on = ['mode', 'map', 'brawler'], right_on = ['mode', 'map', 'brawler'])
    
    #Compare population to individual history and inform recommendations
    better = (df['win_rate_x'] < df['ci.lower']) & (df['matches_played_y'] >= 5)
    worse = (df['win_rate_x'] > df['ci.upper']) & (df['matches_played_y'] >= 5)
    df['reason'] = 'Population win rate'
    df.loc[better,'reason'] = 'Outperforming population win rate'
    df.loc[worse,'reason'] = 'Underperforming population win rate'
    df['estimated_win_rate'] = df['win_rate_x']
    df.loc[better,'estimated_win_rate'] = df.loc[better,'win_rate_y']
    df.loc[worse,'estimated_win_rate'] = df.loc[worse,'win_rate_y']
    df = df[['map', 'mode', 'brawler', 'estimated_win_rate', 'win_rate_x', 'win_rate_y', 'wins_y', 'matches_played_y', 'ci.lower', 'ci.upper', 'reason']].sort_values(by = 'win_rate_y', 
                                                                                                                                                ascending = False)
    df.columns = ['Map', 'Mode', 'Brawler', 'Estimated Win Rate', 'Population Win Rate', 'Your Win Rate', 'Your Wins', 'Your Matches Played', 'Estimated Lower Bound', 'Estimated Upper Bound', 'Reason']
    df = df.loc[df['Reason']!= 'Population win rate', :]
    to_percent = ['Estimated Win Rate', 'Population Win Rate', 'Your Win Rate', 'Estimated Lower Bound', 'Estimated Upper Bound']
    for col in to_percent:
        df[col] = pd.Series(["{0:.2f}%".format(num * 100) for num in df[col]], index=df.index)
    no_decimals = ['Your Wins', 'Your Matches Played']
    for col in no_decimals:
        df[col] = pd.Series(["{0:.0f}".format(num) for num in df[col]], index=df.index)
    df = df.replace(to_replace='nan%', value='-').replace(to_replace='nan', value='-')
    return(df)
    
def get_map_weaknesses(connection_string, my_trophies='high'):
    #Set table to collect from    
    table = 'population_aggs_' + my_trophies    
    
    #Build query
    query = "SELECT mode, map, brawler,"
    query += " SUM(wins) as wins,"
    query += " SUM(matches_played) AS matches_played"
    query += " FROM " + table
    query += " WHERE mode != 'bossFight'"
    query += " GROUP BY mode, map, brawler;"
    
    #Get grouped results
    df = sql_get_results(connection_string, table, '', '', '', '', query)
    
    #Calculate win rate confidence intervals
    df = df.loc[df['matches_played'] >= 20, :]
    df['win_rate'] = df['wins'] / df['matches_played']
    df = df.sort_values('win_rate', ascending = False)
    df.columns = ['Mode', 'Map', 'Brawler', 'Wins', 'Matches Played', 'Win Rate']
    df['Win Rate'] = pd.Series(["{0:.2f}%".format(num * 100) for num in df['Win Rate']], index=df.index)
    no_decimals = ['Wins', 'Matches Played']
    for col in no_decimals:
        df[col] = pd.Series(["{0:.0f}".format(num) for num in df[col]], index=df.index)
    df = df.replace(to_replace='nan%', value='-').replace(to_replace='nan', value='-')
    return(df.head(50))
    
def sql_get_results(connection_string, table, my_mode, my_map, my_trophies = 'high', my_id = None, custom_query = None):
    #Set table to collect from
    if custom_query is None:
        if my_id is not None:
            table = 'individual_aggs_' + my_trophies
        else:
            table = 'population_aggs_' + my_trophies      
    
    try:
        #Connect to the database
        connection = psycopg2.connect(connection_string)
        
        #Build SQL query
        if custom_query is not None:
            query = custom_query
        else:
            query = "SELECT mode, map, brawler,"
            query += " SUM(wins) as wins,"
            query += " SUM(matches_played) AS matches_played"
            query += " FROM " + table + " WHERE mode = '" + my_mode + "' AND map = '" + my_map + "'"
            if my_id is not None:
                query += " AND player_id = '" + my_id +"'"
            query += " GROUP BY mode, map, brawler"
        results = pd.read_sql_query(query, connection)
        
        #Close the connection
        connection.close()
    except Exception as e:
        print(e)
        return(None)
    return(results)
