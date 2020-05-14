# -*- coding: utf-8 -*-
''''
Created on Sat Aug 18 01:00:17 2018

@author: linzino
'''
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *
import mongodb
import re

app = Flask(__name__)

# 必須放上自己的Channel Access Token
line_bot_api = LineBotApi('fkZZVXaAF/e48XU6uQ5m/Ma1UdPVo2Cz7s+risWsSmh4NyMUGj0OqzxPWfoq02jah1VQa+9uZTUWDWP/ItVz2ILXr8EaKACOM/XttyexVjZl8XP4us8yztBS//D+PHai6iyDoJk/nTx/2RSuxO9yAAdB04t89/1O/w1cDnyilFU=')
# 必須放上自己的Channel Secret
handler = WebhookHandler('1c947d2476365222ae038aebe1b202c0')
# 必須放上自己的You User ID
line_bot_api.push_message('U53b88e7039478edcee8eef5ae6c72142', TextSendMessage(text='你可以開始了'))

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

#訊息傳遞區塊
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    ### 抓到顧客的資料 ###
    profile = line_bot_api.get_profile(event.source.user_id)
    uid = profile.user_id #使用者ID
    usespeak=str(event.message.text) #使用者講的話
    if re.match('[0-9]{4}[<>][0-9]',usespeak): # 先判斷是否是使用者要用來存股票的
        mongodb.write_user_stock_fountion(stock=usespeak[0:4], bs=usespeak[4:5], price=usespeak[5:])
        #line_bot_api.push_message(uid, TextSendMessage(usespeak[0:4]+'已經儲存成功'))
        line_bot_api.push_message('U53b88e7039478edcee8eef5ae6c72142', TextSendMessage(usespeak[0:4]+'已經儲存成功'+uid))
        return 0    
    elif re.match('刪除[0-9]{4}',usespeak): # 刪除存在資料庫裡面的股票
        mongodb.delete_user_stock_fountion(stock=usespeak[2:])
        #line_bot_api.push_message(uid, TextSendMessage(usespeak+'已經刪除成功'))
        line_bot_api.push_message('U53b88e7039478edcee8eef5ae6c72142', TextSendMessage(usespeak[0:4]+'已經刪除成功'+uid))
        return 0

if __name__ == '__main__':
    app.run(debug=True)