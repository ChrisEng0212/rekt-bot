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

# obj = {
#  "side": "Sell",
#  "time": "{{timenow}}",
#  "ticker":"{{ticker}}" ,
#  "strategy": "supertrend",
#  "exchange": "{{exchange}}",
#  "open":{{open}},
#  "high":{{high}},
#  "low":{{low}},
#  "close":{{close}},
#  "volume":{{volume}}
# }

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


@app.route("/divergenceAction", methods=['POST', 'GET'])
def divergenceAction():
    line_bot_api.broadcast(TextSendMessage(text='signal'))

    webhook_data = json.loads(request.data)

    code = webhook_data['code']
    closeP =  webhook_data['close']
    openP = webhook_data['open']
    ema = webhook_data['ema']
    strategy = webhook_data['strategy']
    side = webhook_data['side']

    if code != key_code:
        line_bot_api.broadcast(TextSendMessage(text='Invalid Code: ' + code))
        return 'Invalid'

    last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][4]['last_price'])  # 4 is BTCUSDT
    print('PRICE', last_price)

    line_bot_api.broadcast(TextSendMessage(text=str(closeP) + str(last_price)))

    ## calculate candle
    candle = 'red'
    if openP < closeP:
        candle = 'green'

    line_bot_api.broadcast(TextSendMessage(text=candle))

    ## calculate distance from ema
    distance = round((((closeP - ema)/closeP)*100), 2)

    line_bot_api.broadcast(TextSendMessage(text=str(distance)))

    ## calculate stop_loss
    stopLoss = closeP
    marker = 0
    if abs(distance) < 2:
        if side == 'Buy':
            stopLoss = closeP*0.99
        else:
            stopLoss = closeP*1.01
        marker = 1
    else:
        if side == 'Buy':
            stopLoss = closeP + (closeP - (distance/2)/100 )
        else:
            stopLoss = closeP - (closeP - (distance/2)/100 )
        marker = 2

    line_bot_api.broadcast(TextSendMessage(text=str(stopLoss) + 'Marker: ' + str(marker) ))

    ## cancel action
    if abs(distance) < 1:
        line_bot_api.broadcast(TextSendMessage( text='Abort: ' + strategy + ' ema distance: ' + str(distance) + str(stopLoss)  ))
        return False
    else:
        line_bot_api.broadcast(TextSendMessage( text='Continue: ' + strategy + ' ema distance: ' + str(distance) + str(stopLoss)  ))

    position_off = True

    position = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    for x in position:
        if x['size'] > 0:
            print('SIZE', x['size'])
            print('SIDE', x['side'])
            line_bot_api.broadcast(TextSendMessage(text='POSITION ON: ' + str(x['side']) + ' - ' + str(x['size']) ))
            position_off = False


    if position_off:
        line_bot_api.broadcast(TextSendMessage(text='position_off ' + str(closeP)))
        ## choose dollar amount
        units = 1000/last_price
        line_bot_api.broadcast(TextSendMessage(text=str(round(units, 2)) + ' ' + str(round(stopLoss)) + ' ' + str(round(ema))    ))
        result = client.LinearOrder.LinearOrder_new(side=side,symbol="BTCUSDT",order_type="Market",qty=round(units, 2),stop_loss=round(stopLoss),take_profit=round(ema),time_in_force="GoodTillCancel",reduce_only=False, close_on_trigger=False).result()
        print(result)
        line_bot_api.broadcast(TextSendMessage(text='result action'))
        line_bot_api.broadcast(TextSendMessage(text=json.dumps(result[0]['result'])))

    return 'divergence'


@app.route("/crossAction", methods=['POST', 'GET'])
def crossAction():

    # line_bot_api.broadcast(TextSendMessage(text='cross'))
    webhook_data = json.loads(request.data)

    last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][4]['last_price'])  # 4 is BTCUSDT
    print('PRICE', last_price)

    position_off = True

    position = client.LinearPositions.LinearPositions_myPosition(symbol="BTCUSDT").result()[0]['result']
    for x in position:
        if x['size'] > 0:
            print('SIZE', x['size'])
            print('SIDE', x['side'])
            line_bot_api.broadcast(TextSendMessage(text= webhook_data['strategy'] + ' POSITION ON: ' + str(x['side']) + ' - ' + str(x['size']) ))
            position_off = False
            ## short bitcoin and crossUnder
            if x['side'] == 'Sell':
                 print('SellMode')
                 sl = round(webhook_data['ema']) + 100
                 print('SL', sl)
                 line_bot_api.broadcast(TextSendMessage(text='Shorting / crossUnder signal - stop_loss adjusted to: ' + str(sl)))
                 print(client.LinearPositions.LinearPositions_tradingStop(symbol="BTCUSDT", side="Sell", stop_loss=sl).result())
            if x['side'] == 'Buy':
                 sl = round(webhook_data['ema']) - 100
                 line_bot_api.broadcast(TextSendMessage(text='Longing / crossOver signal - stop_loss adjusted to: ' + str(sl)))
                 print(client.LinearPositions.LinearPositions_tradingStop(symbol="BTCUSDT", side="Buy", stop_loss=sl).result())

    return 'ema cross'


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

@app.route("/test", methods=['POST', 'GET'])
def test():

    print('TEST')

    # result = client.LinearOrder.LinearOrder_new(side='Sell',symbol="BTCUSDT",order_type="Market",qty=0.01,stop_loss=50000,take_profit=40000,time_in_force="GoodTillCancel",reduce_only=False, close_on_trigger=False).result()
    # print(type(result[0]['result']))
    ema = 44950.55996856551

    print(client.LinearPositions.LinearPositions_tradingStop(symbol="BTCUSDT", side="Sell", stop_loss=round(ema)).result())

    #line_bot_api.broadcast(TextSendMessage(text=positionData))

    return 'Test'


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

