from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('fkZZVXaAF/e48XU6uQ5m/Ma1UdPVo2Cz7s+risWsSmh4NyMUGj0OqzxPWfoq02jah1VQa+9uZTUWDWP/ItVz2ILXr8EaKACOM/XttyexVjZl8XP4us8yztBS//D+PHai6iyDoJk/nTx/2RSuxO9yAAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('1c947d2476365222ae038aebe1b202c0')
# 必須放上自己的You User ID (PUSH指令要收費)
#line_bot_api.push_message('U53b88e7039478edcee8eef5ae6c72142', TextSendMessage(text='您好!我已準備提供服務...'))



# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(JoinEvent) #經測試，加入新群會觸發
def handle_join(event):
    newcoming_text = "謝謝邀請「晴股偵測儀」來至此群組！！我會盡力為大家服務的～"
    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=newcoming_text)
        )
    #print("JoinEvent =", JoinEvent)

@handler.add(LeaveEvent)    #經測試，退群不會觸發
def handle_leave(event):
    leave_text = "好狠啊!!我被踢掉了QQ"
    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=leave_text)
        )
    #print("leave Event =", event)
    #print("我被踢掉了QQ 相關資訊", event.source)

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #decesion=TextSendMessage(event.message.text)
    #line_bot_api.reply_message(event.reply_token, decesion) #這寫法可以(不要錢)
    #messagetype=TextSendMessage(event.source.type) #若是使用者傳訊息，則傳回user；若是群組傳訊息，則傳回group
    #line_bot_api.reply_message(event.reply_token, messagetype) #這寫法可以(不要錢)

    '''
    if str(event.source.type)=='group':
        profile=line_bot_api.get_profile(event.source.user_id)
        uid=profile.user_id #使用者ID
        uname=profile.display_name
        #群組的ID與名稱試不出來
        groupprofile=line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
        #gid=groupprofile.group_id  #不能這樣使用
        gname=groupprofile.display_name #會顯示出和使用者一樣的名稱

        gid='111'
        #gname='222'
        texttemp=uname+'('+uid+')在群組'+gname+'('+gid+')說：'+event.message.text
        message = TextSendMessage(texttemp)  
        line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
    elif str(event.source.type)=='user':
        #取得說話者資料(針對個人)
        profile=line_bot_api.get_profile(event.source.user_id)
        uid=profile.user_id #使用者ID
        uname=profile.display_name
        texttemp=uname+'('+uid+')說：'+event.message.text
        message = TextSendMessage(texttemp)  
        line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)
    '''

    #測試用指令自動退出群組
    '''
    if str(event.message.text)=='bye':
        #離開
        if str(event.source.type)=='group':
            #回覆用戶
            #message=TextSendMessage('群組拜拜')
            #line_bot_api.reply_message(event.reply_token, message)
            line_bot_api.leave_group(event.source.group_id) #可以自動退出
        else:
            message=TextSendMessage('拜拜')
            line_bot_api.reply_message(event.reply_token, message)
          
    '''

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
        duration=240000
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

    #TemplateSendMessage - ImageCarouselTemplate
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
    line_bot_api.reply_message(event.reply_token, message) #這寫法可以(不要錢)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
