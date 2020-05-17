# -*- coding: UTF-8 -*-
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
config.read('config.ini')

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
    num = random.sample(src_digits,2) #随机取1位数字
    lower = random.sample(src_uppercase,2) #随机取1位小写字母
    upper = random.sample(src_lowercase,2) #随机取1位大写字母
    special = random.sample(src_special,2)  #随机取1位大写字母特殊字符
    other = random.sample(string.ascii_letters+string.digits+string.punctuation,4) #随机取4位
    # 生成字符串
    # print(num, lower, upper, special, other)
    pwd_list = num + lower + upper + special + other
    # shuffle将一个序列中的元素随机打乱，打乱字符串
    random.shuffle(pwd_list)
    # 列表转字符串
    password_str = ''.join(pwd_list)
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
    db=constructor()
    # 取得資料表
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
    # 取得資料表
    collect = db['mydb']
    collect.remove({"stock": stock})   
#----------------------------秀出使用者的股票--------------------------
def show_user_stock_fountion():  
    db=constructor()
    # 取得資料表
    collect = db['mydb']
    cel=list(collect.find({"data": 'care_stock'}))
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
    newcoming_text = "謝謝邀請「晴股偵測儀」來至此群組！！我會盡力為大家服務的～"
    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=newcoming_text)
        )


@handler.add(LeaveEvent)    #經測試，退群不會觸發
def handle_leave(event):
    print("leave Event =", LeaveEvent)
    print("我被踢掉了QQ 相關資訊", event)
    leave_text = "好狠啊!!我被踢掉了QQ"
    #LeaveEvent事件不會回傳reply_token，所以line_bot_api.reply_message不能用 
    # line_bot_api.reply_message(
    #         event.reply_token,
    #         TextMessage(text=leave_text)
    #     )


@handler.add(MemberJoinedEvent)    #有人加入群組時觸發
def handle_MemberJoinedEvent(event):
    print("MemberJoinedEvent =", MemberJoinedEvent)
    print("有人入群相關資訊", event)
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
    gid = event.source.group_id
    MemberLeftEvent_text = '「晴股偵測儀」依依不捨目送您離去...'

    #MemberLeftEvent事件不會回傳reply_token，所以line_bot_api.reply_message不能用  
    # line_bot_api.reply_message(
    #         event.reply_token,
    #         TextMessage(text=MemberLeftEvent)
    #     )
    #經測試line_bot_api.push_message只能傳訊給有彼此加好友的UID
    #且無法用GID的方式傳訊
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
    if PostbackEvent_text=='取得帳號與密碼':
        # 隨機產生一組密碼
        upasswd = GenPass()
        #到期日(半年後)
        expiredatesixmonth = f'{datetime.date.today() + datetime.timedelta(days=180):%Y/%m/%d}'
        #到期日(一年後)
        expiredateoneyear = f'{datetime.date.today() + datetime.timedelta(days=360):%Y/%m/%d}'
        
        #從雲端資料庫中找到userid相符資料
        db=constructor()    
        # 取得資料表
        results = db.accountandpassword.find({'userid':uid})
        if results.count()==0: #即沒有找到USERID
            db.accountandpassword.insert({"userid": uid,
                            "password": upasswd,
                            "expiredate": f'{datetime.date.today() + datetime.timedelta(days=180):%Y/%m/%d}',
                            "ispay": '0',
                            "date_info": f'{datetime.datetime.today():%Y/%m/%d %H:%M:%S}'
                            })    
            PostbackEvent_text = '帳號：【'+uid+'】\n'
            PostbackEvent_text = PostbackEvent_text+'密碼：【'+upasswd+'】\n'
            PostbackEvent_text = PostbackEvent_text+'到期日：\n'
            PostbackEvent_text = PostbackEvent_text+'1.半年期：'+expiredatesixmonth+'\n'
            #PostbackEvent_text = PostbackEvent_text+'2.一年期：'+expiredateoneyear+'\n'
            PostbackEvent_text = PostbackEvent_text+'註：請將上述帳號及密碼填入電腦端後連線即可'    
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
                PostbackEvent_text = PostbackEvent_text+'到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'1.半年期：'+expiredatevalue
            elif int(ispayvalue)==1 and int(expiredate)<int(TodayDate):
                PostbackEvent_text = '您授權日期已到期\n'
                PostbackEvent_text = PostbackEvent_text+'到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'1.半年期：'+expiredatevalue+'\n'
                PostbackEvent_text = PostbackEvent_text+'系統刻正幫您重新取得帳號及密碼，相關資料如下：\n'                
                PostbackEvent_text = PostbackEvent_text+'原帳號：【'+uid+'】\n'
                PostbackEvent_text = PostbackEvent_text+'新密碼：【'+upasswd+'】\n'
                PostbackEvent_text = PostbackEvent_text+'新到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'1.半年期：'+expiredatesixmonth+'\n'
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
                PostbackEvent_text = '您尚未完成完整授權程序'
    elif PostbackEvent_text=='查詢到期日':
        #從雲端資料庫中找到userid相符資料
        db=constructor()    
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
                PostbackEvent_text = PostbackEvent_text+'1.半年期：'+expiredatevalue
            elif int(ispayvalue)==1 and int(expiredate)<int(TodayDate):
                PostbackEvent_text = '您授權日期已到期\n'
                PostbackEvent_text = PostbackEvent_text+'到期日：\n'
                PostbackEvent_text = PostbackEvent_text+'1.半年期：'+expiredatevalue
            elif int(ispayvalue)==0:    #有會員資料但沒有繳費
                PostbackEvent_text = '您尚未完成完整授權程序'



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
            '''
            profile=line_bot_api.get_profile(event.source.user_id)
            uid=profile.user_id #使用者ID
            uname=profile.display_name #使用者名稱
            upic_url=profile.picture_url    #使用者圖像
            ustatus=profile.status_message  #使用者狀態訊息
            '''
            uid=event.source.user_id    #使用者ID

            #群組的ID與名稱試不出來
            groupprofile=line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
            gid=event.source.group_id  #不能這樣使用
            gname=groupprofile.display_name #會顯示出和使用者一樣的名稱

            #經查取得群組或聊天室內所有用戶的 ID、此功能需要 Premium 帳號才能使用
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
            #若群組使用者輸入'滾'，則自動退群
            if userspeak=='滾':
                message=TextSendMessage('太狠了，群組拜拜!!!')
                line_bot_api.reply_message(event.reply_token, message)
                line_bot_api.leave_group(event.source.group_id) #可以自動退出
            elif userspeak=='請問我的使用者ID':
                message = TextSendMessage(text=str(event))
                line_bot_api.reply_message(event.reply_token, message)
            else: 
                message = TextSendMessage(texttemp)  
                line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)

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
            elif userspeak=='？':
                #TemplateSendMessage - ButtonsTemplate （按鈕介面訊息）OK
                message = TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://i.imgur.com/mBavrc2.png',
                        title='基本設定',
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
                            #     label='查詢到期日',
                            #     text='查詢到期日'
                            # ),
                            URITemplateAction(
                                label='使用說明',
                                uri='https://i.imgur.com/'
                            )
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, message)
            else:
                message = TextSendMessage(texttemp)  
                line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
        #'''


    #取得說話者資料(針對群組)

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
