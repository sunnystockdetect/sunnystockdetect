# -*- coding:UTF-8 -*-
'''
# 取得日期時間格式方式：
	DateTimeTemp = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
	t = datetime.datetime.strptime(f'{row.成交時間}', '%Y%m%d%H%M%S%f')
	results.datevalue =	f'{datetime.datetime.now():%Y/%m/%d}'
	results.timevalue = f'{datetime.datetime.now():%H:%M:%S.%f}'
	TodayDate = f'{datetime.date.today():%Y%m%d}'
	receivetime = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
'''
from __future__ import unicode_literals
from apscheduler.schedulers.blocking import BlockingScheduler
# 增加了 render_template
from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
from pymongo import MongoClient
import urllib.parse
import datetime
import re
import os
import configparser
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
import random   #调用random模块
import string   #调用string模块
#import time
#from threading import Timer

# 全域變數
#isChangeDay = 0	#用來判斷是否已經過日，若過日，則需重新更新所需資訊
#TodayDate = f'{datetime.date.today():%Y%m%d}'	#記錄今日的年月日(格式YYYYMMDD)

# 啟動網頁監聽
app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')

# Channel Access Token
#line_bot_api = LineBotApi('fkZZVXaAF/e48XU6uQ5m/Ma1UdPVo2Cz7s+risWsSmh4NyMUGj0OqzxPWfoq02jah1VQa+9uZTUWDWP/ItVz2ILXr8EaKACOM/XttyexVjZl8XP4us8yztBS//D+PHai6iyDoJk/nTx/2RSuxO9yAAdB04t89/1O/w1cDnyilFU=')
line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
# Channel Secret
#handler = WebhookHandler('1c947d2476365222ae038aebe1b202c0')
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
# 必須放上自己的You User ID (PUSH指令要收費)
#line_bot_api.push_message('U53b88e7039478edcee8eef5ae6c72142', TextSendMessage(text='您好!我已準備提供服務...'))

'''
# 計時器在本機端測試時沒問題，但送上HEROKU就不會執行，故改寫成排程並放在clock.py中送上去HEROKU執行
# 定義計時器類別
class RepeatingTimer(Timer):
    def run(self):
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)
# 定義定時器要做的事項(自己寫的定時器)
def TimeFunc():
    ##### 資料庫連接(用來判斷是否已經過日，若過日，則需重新更新所需資訊) #####
    # 一次性連線
    # 建立連線用戶端
    client1 = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db1 = client1['sunnystockdb']
    results = db1.needupdate.find()
    for result in results:
        TodayDateLast = f'{result["ischangeday"]}'
    if (TodayDate.strip()==TodayDateLast.strip()):
        isChangeDay=0
    else:
        isChangeDay=1
        try:
            # 執行命令清空資料表內容

            # 更新上一次更新日期紀錄   
            try:
                db1.needupdate.update_one({'ischangeday': TodayDateLast}, [{'$set': {'ischangeday': TodayDate}}])
            except Exception as e:
                print('更新資料失敗(更新上一次更新日期紀錄)')
                print(e)
                pass
        except Exception as e:
            pass
    # 關閉連線用戶端
    client1.close()
'''
class AESCipher(object):
    def __init__(self, key): 
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()
    def encrypt(self, raw):
        #raw = self._pad(raw)
        raw = base64.b64encode(raw.encode('utf-8')).decode('ascii')
        iv = Random.new().read(AES.block_size)
        # 初始化加密器
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        #先进行aes加密
        encrypt_aes = cipher.encrypt(self._pad(raw))
        #用base64转成字符串形式
        # 执行加密并转码返回bytes
        #encrypted_text = str(base64.encodebytes(iv+encrypt_aes), encoding='utf-8')        
        iv = str(base64.encodebytes(iv), encoding='utf-8') 
        encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8') 
        encrypted_text = iv+encrypted_text
        return encrypted_text 
    def decrypt(self, enc):
        #取出IV及加密本文
        iv = enc[:25]
        base64_decrypted = enc[25:]
        #优先逆向解密base64成bytes
        iv = base64.decodebytes(iv.encode(encoding='utf-8'))
        base64_decrypted = base64.decodebytes(base64_decrypted.encode(encoding='utf-8'))
        # 初始化加密器
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        #执行解密密并转码返回str
        decrypted_text = str(cipher.decrypt(base64_decrypted),encoding='utf-8') # 执行解密密并转码返回str
        decrypted_text = base64.b64decode(decrypted_text.encode('utf-8')).decode('utf-8')
        return decrypted_text
        #return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
    def _pad(self, s):
        while len(s) % self.bs != 0:
            s += '\0'
        return str.encode(s)  # 返回bytes
    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

# 隨機產生密碼
def GenPass():
    src_digits = string.digits              #string_数字  '0123456789'
    src_uppercase = string.ascii_uppercase  #string_大写字母 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    src_lowercase = string.ascii_lowercase  #string_小写字母 'abcdefghijklmnopqrstuvwxyz'
    src_special = string.punctuation        #string_特殊字符 '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
 
    #sample从序列中选择n个随机独立的元素，返回列表
    num = random.sample(src_digits,2) #随机取2位数字
    lower = random.sample(src_uppercase,2) #随机取2位小写字母
    upper = random.sample(src_lowercase,2) #随机取2位大写字母
    special = random.sample(src_special,2)  #随机取2位大写字母特殊字符
    other = random.sample(string.ascii_letters+string.digits+string.punctuation,4) #随机取4位
    # 生成字符串
    # print(num, lower, upper, special, other)
    pwd_list = num + lower + upper + special + other
    #因為configparser.ConfigParser()讀取到%會變成進行Interpolation動作，故要將%轉換成別的字元
    pwd_listTemp=[]
    for i in pwd_list:
        if i=='%':
            i='!'
        pwd_listTemp.append(i)
        
    # shuffle将一个序列中的元素随机打乱，打乱字符串
    random.shuffle(pwd_listTemp)
    # 列表转字符串
    password_str = ''.join(pwd_listTemp)
    #print(password_str)
    return password_str

##### 資料庫連接 #####
def constructor():
    # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    return db


#----------------------------儲存使用者的股票--------------------------
def write_user_stock_fountion(stock, bs, price):
    #資料庫連接
    #db=constructor()
    # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    # 取得資料表
    collect = db['mydb']
    collect.insert({"stock": stock,
                    "data": 'care_stock',
                    "bs": bs,
                    "price": float(price),
                    "date_info": datetime.datetime.utcnow()
                    })
    #關閉資料庫session
    client.close()

#----------------------------殺掉使用者的股票--------------------------
def delete_user_stock_fountion(stock): 
    #資料庫連接
    #db=constructor()
    # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    # 取得資料表
    collect = db['mydb']
    collect.remove({"stock": stock}) 
    #關閉資料庫session
    client.close()  
#----------------------------秀出使用者的股票--------------------------
def show_user_stock_fountion():  
    #資料庫連接
    #db=constructor()
    # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    # 取得資料表
    collect = db['mydb']
    cel=list(collect.find({"data": 'care_stock'}))
    #關閉資料庫session
    client.close() 
    return cel

@app.route("/")
def home():
    return render_template("home.html")

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 我加了下面那一行(測試用，將訊息輸出去HeroKU的LOG中)
    #print(body)
    # 我加了上面那一行

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(JoinEvent) #經測試，加入新群會觸發
def handle_join(event):
    print("JoinEvent =", JoinEvent)
    print("被邀請入群相關資訊", event)
    gid = event.source.group_id
    giddb = gid+'sayinfo'
    giduserdb = gid+'userinfo'

    ##### 加入群組時，依據groupid創建一個新的集合() #####
    # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    # 經測試，這邊因為找網頁POST方式，故資料庫開啟後，不需用db.close()進行關閉，因為會有錯誤
    #資料庫連接
    #db=constructor()
    '''
    # 1.判断集合是否已存在
    collist = db.list_collection_names()
    # collist = mydb.collection_names()
    if not giddb in collist:   # 判断 giddb 集合是否存在
        #若不存在要創建一個新的集合
        #注意: 在 MongoDB 中，集合只有在内容插入后才会创建!
        #就是说，创建集合(数据表)后要再插入一个文档(记录)，集合才会真正创建。
        #所以就先插入一個空資訊，再刪除它
        collect = db[giddb]
        collect.insert({'saydatetime': '',
                        'userid': '',
                        'username': '',
                        'sayinfo': ''
                        }) 
        collect.delete_one({'userid':''}) 
    '''
    # 2.判断集合是否已存在
    collist = db.list_collection_names()
    # collist = mydb.collection_names()
    if not giduserdb in collist:   # 判断 giduserdb 集合是否存在
        #若不存在要創建一個新的集合
        #注意: 在 MongoDB 中，集合只有在内容插入后才会创建!
        #就是说，创建集合(数据表)后要再插入一个文档(记录)，集合才会真正创建。
        #所以就先插入一個空資訊，再刪除它
        collect = db[giduserdb]
        collect.insert({'userid': '',
                        'username': ''
                        }) 
        collect.delete_one({'userid':''}) 
        ##### 在grouporder集合，依據gid建立資料 #####
        # 建立連線用戶端
        #client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
        # 取得資料庫
        #db = client['sunnystockdb']
        collect = db['grouporder']
        collect.insert({'groupid': gid,
                        'groupname':'',
                        'isorder': '0'
                        })
    else:
        #print("集合已存在！")
        pass
    #關閉資料庫session
    client.close()
    newcoming_text = "謝謝邀請「晴股偵測儀」來至此群組！！我會盡力為大家服務的～"
    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=newcoming_text)
        )


@handler.add(LeaveEvent)    #經測試，退群會觸發
def handle_leave(event):
    print("leave Event =", LeaveEvent)
    print("我被踢掉了QQ 相關資訊", event)
    leave_text = "好狠啊!!我被踢掉了QQ"
    gid = event.source.group_id
    giddb = gid+'sayinfo'
    giduserdb = gid+'userinfo'

    ##### 退出群組時，依據groupid刪除該集合 #####
    # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    #資料庫連接
    #db=constructor()

    '''
    # 1.判断集合是否已存在
    collist = db.list_collection_names()
    # collist = mydb.collection_names()
    if giddb in collist:   # 判断 giddb 集合是否存在
        db.drop_collection(giddb)
    else:
        #print("集合不存在！")
        pass
    '''
    # 2.判断集合是否已存在
    collist = db.list_collection_names()
    # collist = mydb.collection_names()
    if giduserdb in collist:   # 判断 giduserdb 集合是否存在
        db.drop_collection(giduserdb)
    else:
        #print("集合不存在！")
        pass
    ##### 若被退出群組則刪除在grouporder集合中的相關資料 #####
    # 建立連線用戶端
    #client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    #db = client['sunnystockdb']
    db.grouporder.delete_one({'groupid':gid})  
    #LeaveEvent事件不會回傳reply_token，所以line_bot_api.reply_message不能用 
    # line_bot_api.reply_message(
    #         event.reply_token,
    #         TextMessage(text=leave_text)
    #     )
    #關閉資料庫session
    client.close() 

@handler.add(MemberJoinedEvent)    #有人加入群組時觸發
def handle_MemberJoinedEvent(event):
    print("MemberJoinedEvent =", MemberJoinedEvent)
    print("有人入群相關資訊", event)
    #取得userid
    uid=event.joined.members[0].user_id 
    #取得群組的ID及使用者名稱
    groupprofile=line_bot_api.get_group_member_profile(event.source.group_id, event.joined.members[0].user_id)
    gid=event.source.group_id  
    gname=groupprofile.display_name #會顯示出和使用者一樣的名稱
    giduserdb = gid+'userinfo'

    # # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    #資料庫連接
    #db=constructor()
    # 取得資料表
    collect = db[giduserdb]
    results = collect.find({'userid':uid})
    if results.count()==0: #即沒有找到USERID
        collect.insert({'userid':uid,
                        'username': gname
                        })
    #關閉資料庫session
    client.close()                         
    #MemberJoinedEvent_text = '('+str(event.joined.members[0].user_id)+')歡迎入群'
    MemberJoinedEvent_text = '「晴股偵測儀」歡迎您入群'
    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=MemberJoinedEvent_text)
        )


@handler.add(MemberLeftEvent)    #有人退出群組時觸發
def handle_MemberLeftEvent(event):
    print("MemberLeftEvent =", MemberLeftEvent)
    print("有人退群相關資訊", event)
    #MemberJoinedEvent_text = '('+str(event.joined.members[0].user_id)+')歡迎入群'
    uid = event.left.members[0].user_id
    #取得群組的ID及使用者名稱
    gid=event.source.group_id
    giduserdb = gid+'userinfo'

    # # 建立連線用戶端
    client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
    # 取得資料庫
    db = client['sunnystockdb']
    #資料庫連接
    #db=constructor()    
    # 取得資料表
    collect = db[giduserdb]
    collect.delete_one({'userid':uid}) 
    #關閉資料庫session
    client.close() 
    MemberLeftEvent_text = '「晴股偵測儀」依依不捨目送您離去...'
    #MemberLeftEvent事件不會回傳reply_token，所以line_bot_api.reply_message不能用  
    # line_bot_api.reply_message(
    #         event.reply_token,
    #         TextMessage(text=MemberLeftEvent)
    #     )
    #經測試line_bot_api.push_message只能傳訊給有彼此加好友的UID
    #且無法用gid的方式傳訊
    # line_bot_api.push_message(        #失敗
    #         uid,
    #         TextMessage(text=MemberLeftEvent)
    #     )    
    # line_bot_api.push_message(        #成功
    #         'U53b88e7039478edcee8eef5ae6c72142', 
    #         TextSendMessage(text=MemberLeftEvent_text)
    #     )

@handler.add(UnfollowEvent)    #有人封鎖時觸發
def handle_UnfollowEvent(event):
    print("UnfollowEvent =", UnfollowEvent)
    print("有人封鎖相關資訊", event)
    uid = event.source.user_id
    UnfollowEvent_text = '封鎖「晴股偵測儀」'
    #UnfollowEvent事件不會回傳reply_token，所以line_bot_api.reply_message不能用    
    # line_bot_api.reply_message(
    #         event.reply_token,
    #         TextMessage(text=UnfollowEvent_text)
    #     )

@handler.add(FollowEvent)    #有人解除封鎖時觸發
def handle_FollowEvent(event):
    print("FollowEvent =", FollowEvent)
    print("有人解除封鎖相關資訊", event)
    uid = event.source.user_id
    FollowEvent_text = '解除封鎖「晴股偵測儀」'
    #FollowEvent事件會回傳reply_token，但是回傳至解封方，沒什麼用
    # line_bot_api.reply_message(
    #         event.reply_token,
    #         TextMessage(text=FollowEvent_text)
    #     )

@handler.add(PostbackEvent)    #按下按鈕回應
def handle_PostbackEvent(event):
    print("PostbackEvent =", PostbackEvent)
    print("按下按鈕回應相關資訊", event)

    PostbackEvent_text = str(event.postback.data).strip()
    #現在日期
    TodayDate = f'{datetime.date.today():%Y%m%d}'
    uid = event.source.user_id   
    uiddb = uid+'sayinfo'
    if PostbackEvent_text=='取得帳號與密碼':    #個人
        # 隨機產生一組密碼
        upasswd = GenPass()
        #到期日(半年後)
        expiredatesixmonth = f'{datetime.date.today() + datetime.timedelta(days=180):%Y/%m/%d}'
        #到期日(一年後)
        expiredateoneyear = f'{datetime.date.today() + datetime.timedelta(days=360):%Y/%m/%d}'
    
        # 建立連線用戶端
        client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
        # 取得資料庫
        db = client['sunnystockdb']
        #從雲端資料庫中找到userid相符資料
        #db=constructor()    
        # 取得資料表
        results = db.accountandpassword.find({'userid':uid})
        if results.count()==0: #即沒有找到USERID
            db.accountandpassword.insert({"userid": uid,
                            "password": upasswd,
                            "expiredate": f'{datetime.date.today() + datetime.timedelta(days=180):%Y/%m/%d}',
                            "ispay": '0',
                            "date_info": f'{datetime.datetime.today():%Y/%m/%d %H:%M:%S}',
                            "logindatetime": '',
                            "onlinedatetime": ''                        
                            })    
            PostbackEvent_text = '1.帳號：【'+uid+'】\n'
            PostbackEvent_text = PostbackEvent_text+'2.密碼：【'+upasswd+'】\n'
            PostbackEvent_text = PostbackEvent_text+'3.到期日：\n'
            PostbackEvent_text = PostbackEvent_text+'(1)半年期：【'+expiredatesixmonth+'】\n'
            #PostbackEvent_text = PostbackEvent_text+'2.一年期：'+expiredateoneyear+'\n'
            PostbackEvent_text = PostbackEvent_text+'註：請將上述帳號及密碼填入電腦端後連線即可'    
            ##### 申請帳號密碼時，依據userid創建一個新的同步產生userdb資料表集合 #####
            # 判断集合是否已存在
            collist = db.list_collection_names()
            # collist = mydb.collection_names()
            if not uiddb in collist:   # 判断 giddb 集合是否存在
                #若不存在要創建一個新的集合
                #注意: 在 MongoDB 中，集合只有在内容插入后才会创建!
                #就是说，创建集合(数据表)后要再插入一个文档(记录)，集合才会真正创建。
                #所以就先插入一個空資訊，再刪除它
                collect = db[uiddb]
                collect.insert({'saydatetime': '',
                                'groupid': '',
                                'userid': '',
                                'username': '',
                                'sayinfo': ''
                                }) 
                collect.delete_one({'userid':''}) 
        else:   #曾經有申請過
            for result in results:
                uidvalue = f'{result["userid"]}'
                upasswdvalue =  f'{result["password"]}'
                expiredatevalue =  f'{result["expiredate"]}'
                ispayvalue =  f'{result["ispay"]}'
            #已繳費且未到期
            expiredate = expiredatevalue[:4]+expiredatevalue[5:7]+expiredatevalue[-2:]
            if  int(ispayvalue)==1 and int(expiredate)>=int(TodayDate):
                PostbackEvent_text = '您目前仍在授權有效中，毋需重新取得帳號及密碼\n'
                PostbackEvent_text = PostbackEvent_text+'原申請資料如下：\n'
                PostbackEvent_text = PostbackEvent_text+'1.帳號：【'+uidvalue+'】\n'
                PostbackEvent_text = PostbackEvent_text+'2.密碼：【'+upasswdvalue+'】\n'
                PostbackEvent_text = PostbackEvent_text+'3.到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'(1)半年期：【'+expiredatevalue+'】'
            elif int(ispayvalue)==1 and int(expiredate)<int(TodayDate):
                PostbackEvent_text = '您授權日期已到期\n'
                PostbackEvent_text = PostbackEvent_text+'到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'(1)半年期：【'+expiredatevalue+'】\n'
                PostbackEvent_text = PostbackEvent_text+'系統刻正幫您重新取得帳號及密碼，相關資料如下：\n'                
                PostbackEvent_text = PostbackEvent_text+'原帳號：【'+uid+'】\n'
                PostbackEvent_text = PostbackEvent_text+'新密碼：【'+upasswd+'】\n'
                PostbackEvent_text = PostbackEvent_text+'新到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'(1)半年期：【'+expiredatesixmonth+'】\n'
                #PostbackEvent_text = PostbackEvent_text+'2.一年期：'+expiredateoneyear+'\n'
                PostbackEvent_text = PostbackEvent_text+'註：請將上述帳號及密碼填入電腦端後連線即可'    
                #重新取得密碼及有效期限
                try:
                    db.accountandpassword.update_many({'userid':uid}, {'$set': {'password': upasswd, 
                        'expiredate': f'{datetime.date.today() + datetime.timedelta(days=180):%Y/%m/%d}',
                        'ispay': '0',
                        'date_info': f'{datetime.datetime.today():%Y/%m/%d %H:%M:%S}'                    
                    }})
                except Exception as e:
                    print('更新資料失敗(重新取得密碼及有效期限)')
                    print(e)
                    pass
            elif int(ispayvalue)==0:    #有會員資料但沒有繳費
                PostbackEvent_text = '您曾申請過授權\n但尚未完成完整授權程序'
            #關閉資料庫session
            client.close()        
    elif PostbackEvent_text=='查詢到期日':  #個人
        #從雲端資料庫中找到userid相符資料
        # 建立連線用戶端
        client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
        # 取得資料庫
        db = client['sunnystockdb']
        #資料庫連接
        #db=constructor()   
        # 取得資料表
        results = db.accountandpassword.find({'userid':uid})
        if results.count()==0: #即沒有找到USERID    
            PostbackEvent_text = '您目前非合法授權使用者\n請取得帳號及密碼後\n並完備申請程序'
        else:#曾經有申請過
            for result in results:
                uidvalue = f'{result["userid"]}'
                upasswdvalue =  f'{result["password"]}'
                expiredatevalue =  f'{result["expiredate"]}'
                ispayvalue =  f'{result["ispay"]}'
            #已繳費且未到期
            expiredate = expiredatevalue[:4]+expiredatevalue[5:7]+expiredatevalue[-2:]
            if  int(ispayvalue)==1 and int(expiredate)>=int(TodayDate):
                PostbackEvent_text = '您目前仍在授權有效中\n'
                PostbackEvent_text = PostbackEvent_text+'到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'(1)半年期：【'+expiredatevalue+'】'
            elif int(ispayvalue)==1 and int(expiredate)<int(TodayDate):
                PostbackEvent_text = '您授權日期已到期\n'
                PostbackEvent_text = PostbackEvent_text+'到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'(1)半年期：【'+expiredatevalue+'】'
            elif int(ispayvalue)==0:    #有會員資料但沒有繳費
                PostbackEvent_text = '您曾申請過授權\n但尚未完成完整授權程序'
        #關閉資料庫session
        client.close()         
    elif PostbackEvent_text=='訂閱「聽我說」':  #群組
        ##### 檢查本群組是否已經訂閱「聽我說」 #####
        gid = event.source.group_id
        # 建立連線用戶端
        client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
        # 取得資料庫
        db = client['sunnystockdb']
        #資料庫連接
        #db=constructor()
        collect = db['grouporder']
        results = collect.find({'groupid':gid})
        for result in results:
            if not results.count()==0: #即找到groupid
                isordervalue =  f'{result["isorder"]}'
        #關閉資料庫session
        client.close() 
        if isordervalue=='0':
            PostbackEvent_text='1.【本群組尚未訂閱「聽我說」系統】\n'
            PostbackEvent_text += '2.【註：只需訂閱一次即可，若本群組已有人訂閱，毋需再次訂閱】\n\n'
            PostbackEvent_text += '3.若需訂閱，請依照下列命令格式鍵入：\nORDER:[群組名稱]'       
        elif isordervalue=='1':
            PostbackEvent_text='【本群組已訂閱「聽我說」系統，毋需重覆訂閱】' 
    elif PostbackEvent_text=='取消訂閱「聽我說」':  #群組
        gid = event.source.group_id
        ##### 取消訂閱「聽我說」在grouporder集合，依據gid將其對應的isorder=1 #####
        # 建立連線用戶端
        client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
        # 取得資┌
        db = client['sunnystockdb']
        #資料庫連接
        #db=constructor()
        results = db.grouporder.find({'groupid':gid})
        if not results.count()==0: #即找到groupid
            # 更新紀錄   
            try:
                db.grouporder.update_many({'groupid': gid}, [{'$set': {'isorder': '0'}}])
            except Exception as e:
                print('更新資料失敗(取消訂閱「聽我說」在grouporder集合，依據gid將其對應的isorder=1)')
                print(e)
                pass 
        #關閉資料庫session
        client.close() 
        PostbackEvent_text = '已取消訂閱「聽我說」'
    elif PostbackEvent_text=='下載電腦端軟體':  #群組
        PostbackEvent_text='請使用您的個人電腦，於下列網址下載晴股偵測儀「聽我說」電腦端軟體\n'
        PostbackEvent_text+='網址：【https://drive.google.com/file/d/1pmrmya51mhOJoNUoRXrdFgRdkCVSD4a8/view?usp=sharing】\n\n'
        PostbackEvent_text+='若您電腦作業系統為WinXP或Win7，請先安裝中文語音庫，下載網址如下：\n'
        PostbackEvent_text+='網址：【https://drive.google.com/file/d/1USZUG3ofcY1a4wiJt5o-HHUbsn-eJBug/view?usp=sharing】\n\n'            
    elif PostbackEvent_text=='問題回饋':  #群組
        PostbackEvent_text = '請依照下列命令格式鍵入：\nQ:[您要回饋的內文]'
    
    #將操作後資訊輸出至LINE
    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=PostbackEvent_text)
    )

@handler.add(MessageEvent, message=TextMessage) # 處理訊息
def handle_message(event):
    #decesion=TextSendMessage(event.message.text)
    #line_bot_api.reply_message(event.reply_token, decesion) #這寫法可以(不要錢)
    #messagetype=TextSendMessage(event.source.type) #若是使用者傳訊息，則傳回user；若是群組傳訊息，則傳回group
    #line_bot_api.reply_message(event.reply_token, messagetype) #這寫法可以(不要錢)

    #'''
    # 這次我加了下面這一行(在LINE DEVELOPERS中進行WEBHOOKS SETTINGS VERIFY有錯誤，此行可排除錯誤)
    if event.source.user_id != 'Udeadbeefdeadbeefdeadbeefdeadbeef':
        if str(event.source.type)=='group':
            #現在日期
            TodayDate = f'{datetime.date.today():%Y%m%d}'
            '''
            profile=line_bot_api.get_profile(event.source.user_id)
            uid=profile.user_id #使用者ID
            uname=profile.display_name #使用者名稱
            upic_url=profile.picture_url    #使用者圖像
            ustatus=profile.status_message  #使用者狀態訊息
            '''
            uid=event.source.user_id    #使用者ID
            #群組的ID能取得
            #群組名稱當無法取得
            groupprofile=line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
            gid=event.source.group_id  
            gname=groupprofile.display_name #會顯示出和使用者一樣的名稱
            giddb = gid+'sayinfo'
            giduserdb = gid+'userinfo'
            #經查取得群組或聊天室內所有用戶的 ID、此功能需要 Premium 帳號才能使用(寫信至LINE官方確認過)
            #member_ids_res=line_bot_api.get_group_member_ids(event.source.group_id)

            #gid='111'
            #gname='TEST'
            #texttemp=uname+'('+uid+')在群組'+gname+'('+gid+')說：'+event.message.text
            #texttemp='('+uname+')在群組('+gid+')說：'+event.message.text
            #texttemp='('+uid+')在群組('+gid+')說：'+event.message.text
            #texttemp='('+gname+')在群組('+gid+')說：'+event.message.text
            #texttemp='('+uname+')說：'+event.message.text
            texttemp='('+gname+')說：'+event.message.text
            userspeak=str(event.message.text).strip() #使用者講的話

            # 建立連線用戶端
            client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
            # 取得資料庫
            db = client['sunnystockdb'] 
            #資料庫連接
            #db=constructor()   
            #若有人發言，先取得其userid及username 存入giduserinfo集合中(目的收集該群組中使用者ID及使用者名稱)
            # 取得資料表
            collect = db[giduserdb]
            results = collect.find({'userid':uid})
            if results.count()==0: #即沒有找到USERID
                collect.insert({'userid':uid,
                                'username': gname
                                })
            #先判斷該群組是否有訂閱「聽我說」
            # 取得資料表
            collect = db['grouporder']
            results = collect.find({'groupid':gid})
            if not results.count()==0: #即找到groupid
                for result in results:
                    isordervalue = f'{result["isorder"]}'    
            if isordervalue=='1': #有訂閱
                #之後將每筆發言收錄至每一個合法授權的uiddb中
                # 取得資料表(從giduserdb讀取群內使用者的userid)
                collect = db[giduserdb]
                results = collect.find()
                for result in results:
                    uidvalue = f'{result["userid"]}'
                    #先判斷是不是自已，若是，則不存儲自己說的話於自己的uiddb中
                    if not uidvalue==uid:
                        #再判斷其否為合法授權使用者
                        collect = db['accountandpassword']
                        results = collect.find({'userid':uidvalue})
                        if not results.count()==0: #即找到非自己的其它USERID
                            for result in results:
                                #uidvalue = f'{result["userid"]}'
                                #upasswdvalue =  f'{result["password"]}'
                                expiredatevalue =  f'{result["expiredate"]}'
                                ispayvalue =  f'{result["ispay"]}'
                                LoginDateTime = f'{result["logindatetime"]}'
                                OnlineDateTime = f'{result["onlinedatetime"]}'
                                #(已繳費)且(未到期)且(判定為在線，即電腦端有登入者:若小於10秒，則表示在線)
                                DateTimeTemp = TodayDate + f'{datetime.datetime.now():%H%M%S}'
                                expiredate = expiredatevalue[:4]+expiredatevalue[5:7]+expiredatevalue[-2:]
                                if not OnlineDateTime=='':
                                    if  int(ispayvalue)==1 and int(expiredate)>=int(TodayDate) and (int(DateTimeTemp)-int(OnlineDateTime)<10):
                                        uiddb = uidvalue+'sayinfo'
                                        collect = db[uiddb]
                                        collect.insert({'saydatetime': datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),
                                                        'groupid': gid,
                                                        'userid': uid,
                                                        'username': gname,
                                                        'sayinfo': userspeak
                                                        }) 
            #關閉資料庫session
            client.close()                                         
            #若群組使用者輸入'我命令你滾'，則自動退群
            if userspeak=='我命令你滾':
                message=TextSendMessage('太狠了，真的不需要我了嗎？群組拜拜!!!')
                line_bot_api.reply_message(event.reply_token, message)
                line_bot_api.leave_group(event.source.group_id) #可以自動退出
            elif userspeak=='請問我的使用者ID':
                message = TextSendMessage(text=str(event))
                line_bot_api.reply_message(event.reply_token, message)
            elif userspeak=='？' or userspeak=='?':
                #TemplateSendMessage - ButtonsTemplate （按鈕介面訊息）OK
                message = TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://i.imgur.com/mBavrc2.png',
                        title='基本設定(群組)',
                        text='鍵入【？Q】可進入「問題回饋選單」\n請選擇所需功能：',
                        actions=[
                            PostbackTemplateAction(
                                label='訂閱「聽我說」',
                                text='訂閱「聽我說」',
                                data='訂閱「聽我說」'
                            ),
                            PostbackTemplateAction(
                                label='取消訂閱「聽我說」',
                                text='取消訂閱「聽我說」',
                                data='取消訂閱「聽我說」'
                            ),
                            PostbackTemplateAction(
                                label='下載電腦端軟體',
                                text='下載電腦端軟體',
                                data='下載電腦端軟體'
                            ),
                            # MessageTemplateAction(
                            #     label='查詢到期日',
                            #     text='查詢到期日'
                            # ),
                            URITemplateAction(
                                label='使用說明',
                                uri='https://drive.google.com/open?id=1dBCfB6GqXUSRmcHUVOCvgnbRVQvHyYps'
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, message)
            elif userspeak=='？Q' or userspeak=='？q' or userspeak=='?Q' or userspeak=='?q':
                #TemplateSendMessage - ButtonsTemplate （按鈕介面訊息）OK
                message = TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://i.imgur.com/mBavrc2.png',
                        title='基本設定(群組)',
                        text='鍵入【？】請進入「主選單」\n請選擇所需功能：',
                        actions=[
                            PostbackTemplateAction(
                                label='問題回饋',
                                text='問題回饋',
                                data='問題回饋'
                            ),
                            # MessageTemplateAction(
                            #     label='查詢到期日',
                            #     text='查詢到期日'
                            # ),
                            URITemplateAction(
                                label='使用說明',
                                uri='https://drive.google.com/open?id=1dBCfB6GqXUSRmcHUVOCvgnbRVQvHyYps'
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, message)                
            elif userspeak[:2]=='Q：' or userspeak[:2]=='Q:' or userspeak[:2]=='q：' or userspeak[:2]=='q:':
                gid = event.source.group_id
                userspeak = userspeak[2:].strip()   #問題內文
                ##### 在questionandanswer集合，新增一筆資料 #####
                # 建立連線用戶端
                client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
                # 取得資料庫
                db = client['sunnystockdb']
                #資料庫連接
                #db=constructor()
                collect = db['questionandanswer']
                # 更新紀錄   
                try:
                    collect.insert({'questiondatetime':f'{datetime.datetime.today():%Y/%m/%d %H:%M:%S}',
                                    'groupid':gid,
                                    'userid':uid,
                                    'username': gname,
                                    'questioncontent':userspeak
                                    })
                except Exception as e:
                    print('更新資料失敗(問題回饋)')
                    print(e)
                    pass
                #關閉資料庫session
                client.close() 
                message = TextSendMessage('感謝您的問題回饋')  
                line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
            elif userspeak[:6]=='ORDER：' or userspeak[:6]=='order：' or userspeak[:6]=='ORDER:' or userspeak[:6]=='order:':
                gid = event.source.group_id
                gname = userspeak[6:].strip()
                ##### 訂閱「聽我說」在grouporder集合，依據gid將其對應的isorder=1 #####
                # 建立連線用戶端
                client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
                # 取得資料庫
                db = client['sunnystockdb']
                #資料庫連接
                #db=constructor()
                collect = db['grouporder']
                results = collect.find({'groupid':gid})
                if not results.count()==0: #即找到groupid
                    # 更新紀錄   
                    try:
                        collect.update_one({'groupid':gid}, {'$set': {'groupname': gname, 
                        'isorder': '1'
                        }})
                    except Exception as e:
                        print('更新資料失敗(訂閱「聽我說」在grouporder集合，依據gid將其對應的isorder=1)')
                        print(e)
                        pass
                #關閉資料庫session
                client.close() 
                message = TextSendMessage('完成訂閱「聽我說」')  
                line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
            else: 
                # message = TextSendMessage(texttemp)  
                # line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
                pass
        #elif str(event.source.type)=='user':
        else:   #若不是群組說話就是使用者了
            #取得說話者資料(針對個人)

            # profile=line_bot_api.get_profile(event.source.user_id)
            # uid=profile.user_id #使用者ID
            # uname=profile.display_name #使用者名稱
            # upic_url=profile.picture_url    #使用者圖像
            # ustatus=profile.status_message  #使用者狀態訊息

            uid=event.source.user_id    #使用者ID

            #texttemp=uname+'('+uid+')說：'+event.message.text
            #texttemp='('+uname+')說：'+event.message.text 
            #texttemp='('+gname+')說：'+event.message.text 
            texttemp='('+uid+')說：'+event.message.text
            #texttemp=event.message.text

            userspeak=str(event.message.text).strip() #使用者講的話
            if re.match('[0-9]{4}[<>][0-9]',userspeak):     # 先判斷是否是使用者要用來存股票的
                write_user_stock_fountion(stock=userspeak[0:4], bs=userspeak[4:5], price=userspeak[5:])
                message = TextSendMessage('儲存股票')
                line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
            elif re.match('刪除[0-9]{4}',userspeak): #刪除存在資料庫裡面的股票
                delete_user_stock_fountion(stock=userspeak[2:])
                message = TextSendMessage('刪除存在資料庫裡面的股票')
                line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
            elif userspeak=='請問我的使用者ID':
                message = TextSendMessage(text=str(event))
                line_bot_api.reply_message(event.reply_token, message)
            elif userspeak=='取得帳號與密碼':
                # message = TextSendMessage(text='執行取得帳號與密碼')
                # line_bot_api.reply_message(event.reply_token, message)
                pass
            elif userspeak=='查詢到期日':
                # message = TextSendMessage(text='執行查詢到期日')
                # line_bot_api.reply_message(event.reply_token, message)
                pass
            elif userspeak=='？' or userspeak=='?':
                #TemplateSendMessage - ButtonsTemplate （按鈕介面訊息）OK
                message = TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://i.imgur.com/mBavrc2.png',
                        title='基本設定(個人)',
                        text='請選擇所需功能：',
                        actions=[
                            PostbackTemplateAction(
                                label='取得帳號與密碼',
                                text='取得帳號與密碼',
                                data='取得帳號與密碼'
                            ),
                            PostbackTemplateAction(
                                label='查詢到期日',
                                text='查詢到期日',
                                data='查詢到期日'
                            ),
                            # MessageTemplateAction(
                            #     label='測試函數區',
                            #     text='測試函數區'
                            # ),
                            URITemplateAction(
                                label='使用說明',
                                uri='https://drive.google.com/open?id=19hvdRkoQWejlTlknmJa_t7VFGljuCAID'
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, message)
            elif userspeak=='測試函數區':    #測試函數區
                '''
                ##### 在grouporder集合，依據gid建立資料 #####
                # 建立連線用戶端
                gid = 'qqqqq'
                client = MongoClient('mongodb+srv://root:rootjimmystock313@cluster0-racxf.gcp.mongodb.net/test?retryWrites=true&w=majority')
                # 取得資料庫
                db = client['sunnystockdb']
                collect = db['grouporder']
                collect.insert({'groupid': gid,
                                'groupname':'',
                                'isorder': '0'
                                })
                #關閉資料庫session
                client.close()                
                ''' 
                pass
            else:
                message = TextSendMessage(texttemp)  
                line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
        #'''


    #TextSendMessage （文字訊息）OK
    #message = TextSendMessage(text=event.message.text)

    #TextSendMessage （文字訊息）OK
    #message = TextSendMessage(texttemp)

    #TextSendMessage （文字訊息）
    #message = TextSendMessage(text='Hello, world')

    #ImageSendMessage（圖片訊息）OK
    '''
    message = ImageSendMessage(
        original_content_url='https://i.imgur.com/0HlQo0e.jpg',
        preview_imag：_url='https://i.imgur.com/0HlQo0e.jpg'
    )    
    '''
    #VideoSendMessage（影片訊息）OK
    '''
    message = VideoSendMessage(
        original_content_url='https://i.imgur.com/5N3ElOk.mp4', #這邊要放影片
        preview_image_url='https://i.imgur.com/0HlQo0e.jpg'   #這邊要放圖片
    )
    '''

    #AudioSendMessage（音訊訊息）找不到可以存放m4a的雲端
    '''
    message = AudioSendMessage(
        original_content_url='https://clyp.it/gieuaa3i.m4a',
        duration=240000 #這邊是使用者看到 UI 的顯示時間
    )
    '''

    #StickerSendMessage（貼圖訊息）OK
    '''
    message = StickerSendMessage(
    package_id='1',
    sticker_id='1'
    )
    '''

    #ImagemapSendMessage （組圖訊息）不知道怎麼用
    '''
    message = ImagemapSendMessage(
    base_url='https://i.imgur.com/',
    alt_text='this is an imagemap',
    base_size=BaseSize(height=1040, width=1040),
    actions=[
            URIImagemapAction(
                link_uri='https://i.imgur.com/',
                area=ImagemapArea(
                    x=0, y=0, width=520, height=1040
                )
            ),
            MessageImagemapAction(
                text='hello',
                area=ImagemapArea(
                    x=520, y=0, width=520, height=1040
                )
            )
        ]
    )
    '''

    #TemplateSendMessage - ButtonsTemplate （按鈕介面訊息）OK
    '''
    message = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url='https://i.imgur.com/0HlQo0e.jpg',
            title='Menu',
            text='Please select',
            actions=[
                PostbackTemplateAction(
                    label='postback',
                    text='postback text',
                    data='action=buy&itemid=1'
                ),
                MessageTemplateAction(
                    label='message',
                    text='message text'
                ),
                URITemplateAction(
                    label='uri',
                    uri='https://i.imgur.com/'
                )
            ]
        )
    )
    '''

    #TemplateSendMessage - ConfirmTemplate（確認介面訊息）OK
    '''
    message = TemplateSendMessage(
        alt_text='Confirm template',
        template=ConfirmTemplate(
            text='Are you sure?',
            actions=[
                PostbackTemplateAction(
                    label='postback',
                    text='postback text',
                    data='action=buy&itemid=1'
                ),
                MessageTemplateAction(
                    label='message',
                    text='message text'
                )
            ]
        )
    )
    '''

    #TemplateSendMessage - CarouselTemplate  OK
    '''
    message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url='https://i.imgur.com/0HlQo0e.jpg',
                    title='this is menu1',
                    text='description1',
                    actions=[
                        PostbackTemplateAction(
                            label='postback1',
                            text='postback text1',
                            data='action=buy&itemid=1'
                        ),
                        MessageTemplateAction(
                            label='message1',
                            text='message text1'
                        ),
                        URITemplateAction(
                            label='uri1',
                            uri='https://i.imgur.com/'
                        )
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url='https://i.imgur.com/0HlQo0e.jpg',
                    title='this is menu2',
                    text='description2',
                    actions=[
                        PostbackTemplateAction(
                            label='postback2',
                            text='postback text2',
                            data='action=buy&itemid=2'
                        ),
                        MessageTemplateAction(
                            label='message2',
                            text='message text2'
                        ),
                        URITemplateAction(
                            label='uri2',
                            uri='https://i.imgur.com/'
                        )
                    ]
                )
            ]
        )
    )
    '''

    #TemplateSendMessage - ImageCarouselTemplate  OK
    '''
    message = TemplateSendMessage(
        alt_text='ImageCarousel template',
        template=ImageCarouselTemplate(
            columns=[
                ImageCarouselColumn(
                    image_url='https://i.imgur.com/0HlQo0e.jpg',
                    action=PostbackTemplateAction(
                        label='postback1',
                        text='postback text1',
                        data='action=buy&itemid=1'
                    )
                ),
                ImageCarouselColumn(
                    image_url='https://i.imgur.com/0HlQo0e.jpg',
                    action=PostbackTemplateAction(
                        label='postback2',
                        text='postback text2',
                        data='action=buy&itemid=2'
                    )
                )
            ]
        )
    )
    '''

    #LocationSendMessage（位置訊息）OK
    '''
    message = LocationSendMessage(
        title='my location',
        address='Tokyo',
        latitude=35.65910807942215,
        longitude=139.70372892916203
    )
    '''
    #line_bot_api.reply_message(event.reply_token, message)
    #line_bot_api.push_message(event.reply_token, message)   #這寫法不行
    #line_bot_api.push_message('U53b88e7039478edcee8eef5ae6c72142', message)    #這寫法可以
    #line_bot_api.push_message(uid, message) #這寫法可以(要錢)
    #line_bot_api.reply_message(uid, message) #這寫法不行
    #line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
if __name__ == "__main__":
    '''
    # 設定計時器並啟動
    timer = RepeatingTimer(10,TimeFunc) #每30分鐘執行一次
    timer.start()
    '''
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)