from flask import Flask, request, abort, render_template, url_for, flash, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime, timedelta
import json
import os
import ast
import time
import bybit

try:
    from meta import SQLALCHEMY_DATABASE_URI, SECRET_KEY, DEBUG, channel_access_token, channel_secret, api_key1, api_secret1, key_code

except:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = False
    channel_access_token = os.environ['CHANNEL_ACCESS']
    channel_secret = os.environ['CHANNEL_SECRET']
    api_key1 = os.environ['api_key1']
    api_secret1 = os.environ['api_secret1']
    key_code = os.environ['key_code']


from linebot import (
    LineBotApi, WebhookHandler, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Channel Access Token
line_bot_api = LineBotApi(channel_access_token)
# Channel Secret
handler = WebhookHandler(channel_secret)

parser = WebhookParser(channel_secret)

client = bybit.bybit(test=False, api_key=api_key1, api_secret=api_secret1)
print('CLIENT', client)

# class Trades(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     username =  db.Column(db.String(20), unique=True, nullable=False)


# admin = Admin(app)
# admin.add_view(MyModelView(User, db.session))
# admin.add_view(MyModelView(Recruits, db.session))


''' UI pages '''

@app.route('/')
def home():
    return 'Hello, World!'


@app.route("/bs_callback/<string:code>/<string:tvdata>", methods=['POST', 'GET'])
def buySell(code, tvdata):
    if code != key_code:
        return 'Invalid'

    sideBS = tvdata
    account = 1
    coin = 'BTC'
    pair = 'BTCUSDT'

    print('BS_CALLBACK', tvdata)

    last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][4]['last_price'])  # 4 is BTCUSDT
    print('PRICE', last_price)

    ##funds = client.Wallet.Wallet_getBalance(coin=coin).result()[0]['result']['USDT']['available_balance']
    ##print(funds)

    if sideBS == 'Sell':
        stop = last_price + (last_price * 0.01)
        profit = last_price - (last_price * 0.1)
    else:
        stop = last_price - (last_price * 0.015)
        profit = last_price + (last_price * 0.04)


    limit = last_price - (last_price * 0.04)

    five_thou = 5000/last_price

    position_off = True

    position = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    for x in position:
        if x['size'] > 0:
            print('SIZE', x['size'])
            line_bot_api.broadcast(TextSendMessage(text=sideBS + ' fail - postion already on: ' + str(x['size']) + 'BTC'))
            position_off = False

    if position_off:
        print(client.LinearOrder.LinearOrder_new(side=sideBS,symbol="BTCUSDT",order_type="Market",qty=0.15,stop_loss=stop,take_profit=profit,time_in_force="GoodTillCancel",reduce_only=False, close_on_trigger=False).result())
        line_bot_api.broadcast(TextSendMessage(text=sideBS+str(last_price)))
        line_bot_api.broadcast(TextSendMessage(text='suggested limit: ' + str(limit)))

    return tvdata


@app.route("/gr_callback/<string:code>/<string:tvdata>", methods=['POST', 'GET'])
def greenRedChange(code, tvdata):
    if code != key_code:
        return 'Invalid'

    print('CHANGE_CALLBACK', tvdata)

    last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][4]['last_price'])  # 4 is BTCUSDT
    print('PRICE', last_price)

    position_off = True

    position = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    for x in position:
        if x['size'] > 0:
            print('SIZE', x['size'])
            print('SIDE', x['side'])
            position_off = False
            if x['side'] == 'Sell':
                sl = last_price + 100
                line_bot_api.broadcast(TextSendMessage(text='MOMENTUM CHANGE, stop_loss adjusted to: ' + str(sl)))
                print(client.LinearPositions.LinearPositions_tradingStop(symbol="BTCUSDT", side="Sell", stop_loss=sl).result())

    if position_off:
        line_bot_api.broadcast(TextSendMessage(text='MOMENTUM CHANGE, no position, BTC: ' + str(last_price)))

    return 'stop_loss adjustment'


@app.route("/test_callback/<string:code>/<string:tvdata>", methods=['POST', 'GET'])
def testMode(code, tvdata):
    if code != key_code:
        return 'Invalid'

    print('TEST_CALLBACK:', tvdata)

    # line_bot_api.broadcast(TextSendMessage(text=tvdata))

    position = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    for x in position:
        if x['size'] > 0:
            print(x)
            print(x['size'])
    print(len(position))

    print(client.LinearPositions.LinearPositions_tradingStop(symbol="BTCUSDT", side="Sell", stop_loss=31900).result())


    # line_bot_api.broadcast(TextSendMessage(text=positionData))

    return tvdata


@handler.add(FollowEvent)
def handle_follow():
    line_bot_api.broadcast(TextSendMessage(text='some joined'))
    print('someone joined')


@handler.add(UnfollowEvent)
def handle_unfollow():
    print('someone has left')

#If there is no handler for an event, this default handler method is called.
@handler.default()
def default(event):
    print('DEFAULT', event)
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    with open('/', 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)




if __name__ == '__main__':
    app.run(debug=True)

