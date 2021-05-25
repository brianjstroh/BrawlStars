# -*- coding: utf-8 -*-
"""
Created on Sun Apr 18 21:15:27 2021

@author: brian
"""

import os
import time
import pickle

os.chdir('C:/Users/brian/Desktop/All/UWEC/DS785_Capstone/Project')

import Update_Master_Database as udb
    

udb.get_daily_extract()

data_directories = ['./Data/522021',
                    './Data/522021_v1',
                    './Data/532021',
                    './Data/542021',
                    './Data/542021_v1']
udb.make_local_pickle_database(data_directories)

infile = open('./Data/database', 'rb')
db = pickle.load(infile)
infile.close()

params = {}
params['user'] = 'postgres'
params['password'] = 'PG!3%7('
params['host'] = 'localhost'
params['database'] = 'BrawlStars'
print('start time: ' + str(time.perf_counter()))
udb.to_sql(params, db.copy())
print('load end time: ' + str(time.perf_counter()))
udb.sql_delete_duplicates('dbname=BrawlStars user=postgres password=PG!3%7(')
print('delete dupes time: ' + str(time.perf_counter()))