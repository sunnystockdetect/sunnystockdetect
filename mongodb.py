# -*- coding: utf-8 -*-
from pymongo import MongoClient
import urllib.parse
import datetime
###############################################################################
#                       股票機器人 Python基礎教學 【pymongo教學】                      #
###############################################################################

# Authentication Database認證資料庫
# Authdb='sunnystockdb'
# coll='mydb'

##### 資料庫連接 #####
def constructor():
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    db = client['sunnystockdb']
    return db
   
#----------------------------儲存使用者的股票--------------------------
def write_user_stock_fountion(stock, bs, price):  
    db=constructor()
    collect = db['mydb']
    collect.insert({"stock": stock,
                    "data": 'care_stock',
                    "bs": bs,
                    "price": float(price),
                    "date_info": datetime.datetime.utcnow()
                    })
    
#----------------------------殺掉使用者的股票--------------------------
def delete_user_stock_fountion(stock): 
    db=constructor()
    collect = db['mydb']
    collect.remove({"stock": stock})
    
#----------------------------秀出使用者的股票--------------------------
def show_user_stock_fountion():  
    db=constructor()
    collect = db['mydb']
    cel=list(collect.find({"data": 'care_stock'}))

    return cel



