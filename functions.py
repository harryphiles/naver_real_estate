# v1.0

from operator import itemgetter
import requests
import json
import logging
import random
import time
import sys
from telegram import sendTelegramMsg
from watch_list import *
import pickle
from os import path
import os
from datetime import datetime, timedelta
from config import chatId1, chatId2

url = 'https://m.land.naver.com/complex/getComplexArticleList' #base url

list_add_new = []
list_result = []

##########################
### new core functions ###
##########################
def get_info_new(tradTpCd, spc_min, spc_max, hscpNo):
    list = []
    param = {
        'tradTpCd': tradTpCd, # A1: 매매, B1: 전세, B2: 월세
        'hscpNo': hscpNo, # building complex unique number
        'order': 'prc', # order of list (point_, date_, prc)
        'showR0': 'N',
    }

    header = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 6P Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36',
        'Referer': 'https://m.land.naver.com/'
    }

    page = 0

    while True:
        page += 1
        param['page'] = page

        r = requests.get(url, params=param, headers=header)
        if r.status_code != 200:
            logging.error('status code: %d' % r.status_code)
            sendTelegramMsg(chatId1, "Error! {r.status_code}")
            sys.exit(0)

        load_json = json.loads(r.text)
        result = load_json['result']
        if result is None:
            #logging.error('no result')
            break
  
        for item in result['list']:
            if float(item['spc2']) >= spc_min and float(item['spc2']) < spc_max:
                atclNm = item['atclNm']
                spc2 = '{:.4}'.format(item['spc2'])
                prc = '{:8}'.format(item['prcInfo'])
                prc_min = '{:8}'.format(item['sameAddrMinPrc'])
                try:
                    desc = item['atclFetrDesc']
                except:
                    desc = 'none'
                if item['flrInfo'][:item['flrInfo'].find('/')].isnumeric():
                    flrInfo = '{:>5}'.format(item['flrInfo'])
                else:
                    flrInfo = '{:>4}'.format(item['flrInfo'])
                x = [atclNm, spc2, prc, prc_min, flrInfo, desc]
                list.append(x)        

        if result['moreDataYn'] == 'N':
            break

    list_add_new.append(list)

def get_data_new(watch_list):
    """to list_test_add"""
    list_add_new.clear()
    for i in range(len(watch_list)):
        rand_num = random.uniform(0.5, 2)
        time.sleep(rand_num)
        print(watch_list[i])
        if i < 10:
            get_info_new('B1', watch_list[i][1], 85, watch_list[i][0])
        if i == 10:
            time.sleep(random.uniform(10, 12))
        if 10 <= i < 20:
            get_info_new('B1', watch_list[i][1], 85, watch_list[i][0])
        if i == 20:
            time.sleep(random.uniform(30, 45))
        if 20 <= i < 30:
            get_info_new('B1', watch_list[i][1], 85, watch_list[i][0])

def data_processing(list_add_new, prc_max):
    """list_add_new is processed and produce list_result"""
    list_result.clear()
    ## only get values below condition
    list1 = []
    for i in list_add_new:
        list_temp = []
        for j in i:
            try:
                if j[3].find("억") == 1:
                    prc = int('{:.1}{:.1}{}'.format(j[3].split()[0], j[3].split()[1], j[3].split(",")[1]))
                else:
                    prc = int('{:.2}{:.1}{}'.format(j[3].split()[0], j[3].split()[1], j[3].split(",")[1]))
            except:
                if j[3].find("억") == 1:
                    prc = int('{:.1}0000'.format(j[3].split()[0]))
                else:
                    prc = int('{:.2}0000'.format(j[3].split()[0]))
            if prc <= prc_max:
                list_temp.append(j)
        if list_temp != []:
            list1.append(list_temp)

    ## sort by minimum prc
    list2 = []
    for i in list1:
        s = sorted(i, key=itemgetter(3))
        list_temp = []
        for j in s:
            list_temp.append(j)
        list2.append(list_temp)

    ### minimum values for each spc for each complex
    # list3 = []
    for i in list2:
        s = sorted(i, key=itemgetter(1))
        list_temp = []
        for j in s:
            list_temp.append(j[1])
        set_s = sorted(set(list_temp))
        list_temp2 = []
        for k in set_s:
            list_temp2.append(s[list_temp.index(k)])
        list_result.append(list_temp2)

def is_identical(data):
    """compare data (check for differences)"""
    if path.isfile(data):
        with open (data, 'rb') as fp:
            former = pickle.load(fp)
            if former == list_result:
                return True
            else:
                with open (data, 'wb') as fp:
                    pickle.dump(list_result, fp)
                return False
    else:
        with open (data, 'wb') as fp:
            pickle.dump(list_result, fp)
    return False

def send_msg_with_list_new(prc_max):
    print(list_result)
    x = ''
    if list_result != []:
        x += f"Price(max): {prc_max} \n"
        for i in list_result:
            for j in i:
                x += f"{j[1]} | {j[3]} | {j[0]} \n"
        sendTelegramMsg(chatId1, x)
        sendTelegramMsg(chatId2, x)
    # else:
    #     sendTelegramMsg(chatId1, "No result")

def time_check_and_delete():
    """time check and delete data files"""
    t_now = datetime.now()
    t_range_max = t_now.replace(hour=9, minute=10, second=0, microsecond=0)
    t_range_min = t_range_max - timedelta(minutes=11)

    if t_range_min <= t_now <= t_range_max:
        for i in range(1,4):
            try:
                os.remove(f'data_{i}')
            except:
                continue

################
### combined ###
################
def alert(watch_list, prc_max, data):
    get_data_new(watch_list)
    data_processing(list_add_new, prc_max)
    if not is_identical(data):
        send_msg_with_list_new(prc_max)
