'''
event = {"reply_token":"就是代表reply_token的一串亂碼", 
         "type":"message",
         "timestamp":"1462629479859", 
         "source":{"type":"user",
                   "user_id":"就是代表user的一串亂碼"}, 
         "message":{"id":"就是代表這次message的一串代碼", 
                    "type":"text", 
                    "text":"使用者傳來的文字信息內容"}}
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
import time
from threading import Timer

# 全域變數
isChangeDay = 0	#用來判斷是否已經過日，若過日，則需重新更新所需資訊
TodayDate = f'{datetime.date.today():%Y%m%d}'	#記錄今日的年月日(格式YYYYMMDD)

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
    uid = event.source.user_id
    #PostbackEvent_text = '按下按鈕'
    PostbackEvent_text = str(event.postback.data).strip()
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
            elif userspeak=='查詢到期日':
                message = TextSendMessage(text='執行查詢到期日')
                line_bot_api.reply_message(event.reply_token, message)
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
                            MessageTemplateAction(
                                label='查詢到期日',
                                text='查詢到期日'
                            ),
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
