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

class BBWP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    ticker =  db.Column(db.String, unique=False, nullable=False)
    timeframe =  db.Column(db.String, unique=False, nullable=False)
    ema =  db.Column(db.String, unique=False, nullable=False)
    value =  db.Column(db.String, unique=False, nullable=False)
    info =  db.Column(db.String, unique=False, nullable=False)
    extra =  db.Column(db.String, unique=False, nullable=False)


class MyModelView(ModelView):
    def is_accessible(self):
        return DEBUG


admin = Admin(app)

admin.add_view(MyModelView(BBWP, db.session))

'''
{
 "time": "{{timenow}}",
 "timeframe": "{{interval}}",
 "ticker":"{{ticker}}" ,
 "strategy": "bbwp",
 "exchange": "{{exchange}}",
 "open":"{{open}}"
}

'''

''' UI pages '''

@app.route('/')
def home():
    return 'Hello, World!'


@app.route("/bbwp", methods=['POST', 'GET'])
def bbwp():
    #line_bot_api.broadcast(TextSendMessage(text='signal'))

    webhook_data = json.loads(request.data)

    ticker = webhook_data['ticker']
    timeframe = webhook_data['interval']
    code = webhook_data['code']

    if code != key_code:
        line_bot_api.broadcast(TextSendMessage(text='Invalid Code: ' + code))
        return 'Invalid'


    entry = BBWP.query.filter_by(ticker=ticker, timeframe=timeframe).first()

    if not entry:
        newEntry = BBWP(ticker=ticker, timeframe=timeframe, ema='n', value='n', info='n', extra='n')
        db.session.add(newEntry)
        db.session.commit()
        entry = BBWP.query.filter_by(ticker=ticker, timeframe=timeframe).first()


    return 'bbwp'

@app.route("/momoAction", methods=['POST', 'GET'])
def momoAction():
    #line_bot_api.broadcast(TextSendMessage(text='signal'))

    webhook_data = json.loads(request.data)

    asset = webhook_data['asset']
    code = webhook_data['code']
    closeP =  webhook_data['close']
    openP = webhook_data['open']
    ema = webhook_data['ema']
    strategy = webhook_data['strategy']
    side = webhook_data['side']

    if code != key_code:
        line_bot_api.broadcast(TextSendMessage(text='Invalid Code: ' + code))
        return 'Invalid'

    last_price = 0.0

    if asset == "BTCUSDT":
        last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][4]['last_price'])  # 4 is BTCUSDT
        # line_bot_api.broadcast(   TextSendMessage(text='BTCUSDT ' + str(closeP) + ' ' + str(last_price)    )   )
    if asset == "ETHUSDT":
        last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][5]['last_price'])  # 4 is BTCUSDT
        # line_bot_api.broadcast(TextSendMessage(text='ETHUSDT ' + str(closeP) + ' ' + str(last_price)))

    #print('PRICE', last_price)

    ## calculate candle
    candle = 'red'
    if openP < closeP:
        candle = 'green'

    ## calculate distance from ema
    distance = round((((closeP - ema)/closeP)*100), 2)

    #line_bot_api.broadcast(TextSendMessage(text=str(distance) + ' ' + candle))

    ## calculate stop_loss
    stopLoss = round(closeP)
    marker = 0
    if abs(distance) < 2:
        if side == 'Buy':
            stopLoss = closeP*0.99
        else:
            stopLoss = closeP*1.01
        marker = 1
    else:
        factor = (abs(distance)/2)/100
        if side == 'Buy':
            stopLoss = closeP * (1-factor)
        else:
            stopLoss = closeP * (1+factor)
        marker = 2

    # line_bot_api.broadcast(TextSendMessage(text=str(stopLoss) + ' Marker: ' + str(marker) ))

    ## cancel action
    if abs(distance) < 1:
        line_bot_api.broadcast(TextSendMessage( text=asset + ' Abort: ' + strategy + ' last: ' + str(last_price) + ' ema distance: ' + str(distance) + ' stop: ' + str(stopLoss)  ))
        return False
    else:
        line_bot_api.broadcast(TextSendMessage( text=asset + ' Continue: ' + strategy + ' last: ' + str(last_price) +  ' ema distance: ' + str(distance) + ' stop: ' + str(stopLoss)  ))

    position_off = True

    position = client.LinearPositions.LinearPositions_myPosition(symbol=asset).result()[0]['result']
    for x in position:
        if x['size'] > 0:
            print('SIZE', x['size'])
            print('SIDE', x['side'])
            line_bot_api.broadcast(TextSendMessage(text='POSITION ON: ' + str(x['side']) + ' Amount: ' + str(x['size']) ))
            position_off = False


    if position_off:
        #line_bot_api.broadcast(TextSendMessage(text='position_off ' + str(closeP)))
        ## choose dollar amount
        units = 1000/last_price
        line_bot_api.broadcast(TextSendMessage(text=str(round(units, 2)) + ' ' + str(round(stopLoss)) + ' ' + str(round(ema))    ))
        result = client.LinearOrder.LinearOrder_new(side=side,symbol=asset,order_type="Market",qty=round(units, 2),stop_loss=round(stopLoss),take_profit=round(ema),time_in_force="GoodTillCancel",reduce_only=False, close_on_trigger=False).result()
        print(result)
        #line_bot_api.broadcast(TextSendMessage(text='result action'))
        line_bot_api.broadcast(TextSendMessage(text='ACTION: ' + json.dumps(result[0]['result'])))

    return 'divergence'


@app.route("/testAction/<string:code>", methods=['POST', 'GET'])
def testAction(code):
    print('TEST_CALLBACK:', code)

    line_bot_api.broadcast(TextSendMessage(text='test'))
    webhook_data = json.loads(request.data)

    asset = webhook_data['asset']
    code = webhook_data['code']
    openP =  webhook_data['openP']
    open = webhook_data['open']
    strategy = webhook_data['strategy']
    side = webhook_data['side']
    Cross = webhook_data['Cross']
    CrossP = webhook_data['CrossP']
    bbwp = webhook_data['bbwp']
    bbwpMA1 = webhook_data['bbwpMA1']
    cutOff = webhook_data['cutOff']


    line_bot_api.broadcast(TextSendMessage(text= webhook_data['strategy'] + '/' + webhook_data['Cross'] + '/' + webhook_data['bbwp'] ))

    return 'test cross'


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

    #print(client.LinearPositions.LinearPositions_tradingStop(symbol="BTCUSDT", side="Sell", stop_loss=round(ema)).result())

    line_bot_api.broadcast(TextSendMessage(text='positionData'))

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

