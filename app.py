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

class BBWPV(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    ticker =  db.Column(db.String, unique=False, nullable=False)
    interval =  db.Column(db.String, unique=False, nullable=True)
    value =  db.Column(db.String, unique=False, nullable=True)
    info =  db.Column(db.String, unique=False, nullable=True)
    extra =  db.Column(db.String, unique=False, nullable=True)

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    ticker =  db.Column(db.String, unique=False, nullable=False)
    interval =  db.Column(db.String, unique=False, nullable=True)
    message =  db.Column(db.String, unique=False, nullable=True)
    data =  db.Column(db.String, unique=False, nullable=True)
    info =  db.Column(db.String, unique=False, nullable=True)


class MyModelView(ModelView):
    def is_accessible(self):
        return DEBUG


admin = Admin(app)

admin.add_view(MyModelView(BBWPV, db.session))


coinList = {
    "0": "BTCUSD",
    "1": "ETHUSD",
    "2": "EOSUSD",
    "3": "XRPUSD",
    "4": "DOTUSD",
    "5": "BITUSD",
    "6": "BTCUSDT",
    "7": "ETHUSDT",
    "8": "EOSUSDT",
    "9": "XRPUSDT",
    "10": "BCHUSDT",
    "11": "LTCUSDT",
    "12": "XTZUSDT",
    "13": "LINKUSDT",
    "14": "ADAUSDT",
    "15": "DOTUSDT",
    "16": "UNIUSDT",
    "17": "XEMUSDT",
    "18": "SUSHIUSDT",
    "19": "AAVEUSDT",
    "20": "DOGEUSDT",
    "21": "MATICUSDT",
    "22": "ETCUSDT",
    "23": "BNBUSDT",
    "24": "FILUSDT",
    "25": "SOLUSDT",
    "26": "XLMUSDT",
    "27": "TRXUSDT",
    "28": "VETUSDT",
    "29": "THETAUSDT",
    "30": "COMPUSDT",
    "31": "AXSUSDT",
    "32": "LUNAUSDT",
    "33": "SANDUSDT",
    "34": "MANAUSDT",
    "35": "KSMUSDT",
    "36": "ATOMUSDT",
    "37": "AVAXUSDT",
    "38": "CHZUSDT",
    "39": "CRVUSDT",
    "40": "ENJUSDT",
    "41": "GRTUSDT",
    "42": "SHIB1000USDT",
    "43": "YFIUSDT",
    "44": "BSVUSDT",
    "45": "ICPUSDT",
    "46": "FTMUSDT",
    "47": "ALGOUSDT",
    "48": "DYDXUSDT",
    "49": "NEARUSDT",
    "50": "SRMUSDT",
    "51": "OMGUSDT",
    "52": "IOSTUSDT",
    "53": "DASHUSDT",
    "54": "FTTUSDT",
    "55": "BITUSDT",
    "56": "GALAUSDT",
    "57": "CELRUSDT",
    "58": "HBARUSDT",
    "59": "ONEUSDT",
    "60": "C98USDT",
    "61": "MKRUSDT",
    "62": "COTIUSDT",
    "63": "ALICEUSDT",
    "64": "EGLDUSDT",
    "65": "RENUSDT",
    "66": "TLMUSDT",
    "67": "RUNEUSDT",
    "68": "ILVUSDT",
    "69": "FLOWUSDT",
    "70": "WOOUSDT",
    "71": "LRCUSDT",
    "72": "ENSUSDT",
    "73": "IOTXUSDT",
    "74": "CHRUSDT",
    "75": "BATUSDT",
    "76": "STORJUSDT",
    "77": "SNXUSDT",
    "78": "SLPUSDT",
    "79": "ANKRUSDT",
    "80": "LPTUSDT",
    "81": "QTUMUSDT",
    "82": "CROUSDT",
    "83": "SXPUSDT",
    "84": "YGGUSDT",
    "85": "ZECUSDT",
    "86": "IMXUSDT",
    "87": "SFPUSDT",
    "88": "AUDIOUSDT",
    "89": "ZENUSDT",
    "90": "GTCUSDT",
    "91": "LITUSDT",
    "92": "CVCUSDT",
    "93": "RNDRUSDT",
    "94": "SCUSDT",
    "95": "RSRUSDT",
    "96": "STXUSDT",
    "97": "MASKUSDT",
    "98": "CTKUSDT",
    "99": "BICOUSDT",
    "100": "REQUSDT",
    "101": "1INCHUSDT",
    "102": "KLAYUSDT",
    "103": "SPELLUSDT",
    "104": "ANTUSDT",
    "105": "DUSKUSDT",
    "106": "ARUSDT",
    "107": "REEFUSDT",
    "108": "XMRUSDT",
    "109": "PEOPLEUSDT",
    "110": "IOTAUSDT",
    "111": "CELOUSDT",
    "112": "WAVESUSDT",
    "113": "RVNUSDT",
    "114": "KNCUSDT",
    "115": "KAVAUSDT",
    "116": "ROSEUSDT",
    "117": "DENTUSDT",
    "118": "CREAMUSDT",
    "119": "LOOKSUSDT",
    "120": "JASMYUSDT",
    "121": "10000NFTUSDT",
    "122": "HNTUSDT",
    "123": "ZILUSDT",
    "124": "NEOUSDT",
    "125": "RAYUSDT",
    "126": "CKBUSDT",
    "127": "SUNUSDT",
    "128": "JSTUSDT",
    "129": "BANDUSDT",
    "130": "RSS3USDT",
    "131": "OCEANUSDT",
    "132": "1000BTTUSDT",
    "133": "API3USDT",
    "134": "BTCUSDH22",
    "135": "BTCUSDM22",
    "136": "ETHUSDH22",
    "137": "ETHUSDM22"
}

'''

https://rekt-lbot.herokuapp.com/


{
 "time": "{{timenow}}",
 "interval": "{{interval}}",
 "ticker":"{{ticker}}" ,
 "strategy": "bbwp",
 "exchange": "{{exchange}}",
 "action" :"action",
 "code": "code",
 "open":"{{open}}"
}

{
 "time": "{{timenow}}",
 "interval": "{{interval}}",
 "ticker":"{{ticker}}" ,
 "action" :"Buy",
 "code": "code",
 "open":"{{open}}"
}

'''

''' UI pages '''

@app.route('/')
def home():
    return 'Rekt Bot, ready for action'


@app.route("/bbwp", methods=['POST', 'GET'])
def bbwp():
    #line_bot_api.broadcast(TextSendMessage(text='signal'))

    #actions  emaUp emaDown  valUp valD

    webhook_data = json.loads(request.data)

    ticker = webhook_data['ticker']
    interval = webhook_data['interval']
    code = webhook_data['code']
    action = webhook_data['action']


    if code != key_code:
        line_bot_api.broadcast(TextSendMessage(text='Invalid Code: ' + code))
        return 'Invalid'


    entry = BBWPV.query.filter_by(ticker=ticker, interval=interval).first()

    if not entry:
        newEntry = BBWPV(ticker=ticker, interval=interval, value='na')
        db.session.add(newEntry)
        db.session.commit()
        entry = BBWPV.query.filter_by(ticker=ticker, interval=interval).first()

    if action == 'valueUp':
        entry.value = 'valueUp'
        db.session.commit()

    if action == 'valueDown':
        entry.value = 'valueDown'
        db.session.commit()

    return 'bbwp'


def placeOrder(side, ticker, stop_loss, take_profit, last_price, units, interval):

    print('PLACEORDER', side, ticker, stop_loss, take_profit, last_price, units, interval)

    result = client.LinearOrder.LinearOrder_new(
        side=side,
        symbol=ticker,
        order_type="Limit",
        stop_loss=stop_loss,
        take_profit=take_profit,
        qty=units,
        price=last_price,
        time_in_force="GoodTillCancel",
        reduce_only=False,
        close_on_trigger=False

    ).result()

    print(result)

    message = result[0]['ret_msg']
    data = json.dumps(result[0]['result'])

    entry = Orders(ticker=ticker, interval=interval, message=message, data=data)
    db.session.add(entry)
    db.session.commit()

    try:
        line_bot_api.broadcast(TextSendMessage(text='ORDER PLACED' + ticker + interval + ': ' + last_price))
    except:
        print('ORDER LINE CANCEL', ticker, interval)


@app.route("/momoAction", methods=['POST', 'GET'])
def momoAction():
    #line_bot_api.broadcast(TextSendMessage(text='signal'))

    webhook_data = json.loads(request.data)

    ticker = webhook_data['ticker']
    time = webhook_data['time']
    interval = webhook_data['interval']
    code = webhook_data['code']
    action = webhook_data['action']
    open = webhook_data['open']

    if code != key_code:
        line_bot_api.broadcast(TextSendMessage(text='Invalid Code: ' + code))
        return 'Invalid'

    coin_number = list(coinList.keys())[list(coinList.values()).index(ticker)]
    print('COIN NUM', coin_number)
    last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][int(coin_number)]['last_price'])

    bbwp = BBWPV.query.filter_by(ticker=ticker, interval=interval).first()

    if bbwp.value == 'valueDown':
        print('BBWP CANCEL')
        try:
            line_bot_api.broadcast(TextSendMessage(text='BBWP CANCEL ' + ticker + interval + ' ' + time + ' ' + open))
        except:
            print('BBWP LINE CANCEL', ticker, interval)

        return 'CANCELLED ACTION'


    ''' GET STOPS '''

    roundStops = {
        "BTCUSDT": 1,
        "MATICUSDT" : 2
    }

    stop_loss = round(last_price*0.996, roundStops[ticker])
    take_profit = round(last_price*1.004, roundStops[ticker])

    print("STOP/PROFIT:", stop_loss, take_profit)


    ''' GET UNITS'''

    roundUnits = {
        "BTCUSDT": 3,
        "MATICUSDT" : 1
    }

    dollars = int(bbwp.info)
    units = round(dollars/last_price, roundUnits[ticker])

    print('UNITS', units)

    placeOrder(action, ticker, stop_loss, take_profit, last_price, units, interval)


    return 'momoAction'

@app.route("/info", methods=['POST', 'GET'])
def info():
    #line_bot_api.broadcast(TextSendMessage(text='signal'))

    # coinList= {}
    # count = 0


    # check = client.Market.Market_symbolInfo().result()[0]['result']
    # for y in check:
    #     coinList[count] = y['symbol']
    #     count += 1
    #     print('TUPLE', json.dumps(y))

    # position = client.LinearPositions.LinearPositions_myPosition(symbol="MATICUSDT").result()[0]['result']
    # for x in position:
    #     print('DUMP', json.dumps(x))

    last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][21]['last_price'])

    ticker = 'MATICUSDT'


    stop_loss = round(last_price*0.996, 3)
    take_profit = round(last_price*1.004, 3)
    print(stop_loss, take_profit)

    #coin_number = list(coinList.keys())[list(coinList.values()).index(ticker)]

    # result = client.LinearOrder.LinearOrder_new(
    #     side='Buy',
    #     symbol=ticker,
    #     order_type="Limit",
    #     stop_loss=stop_loss,
    #     take_profit=take_profit,
    #     qty=100,
    #     price=last_price,
    #     time_in_force="GoodTillCancel",
    #     reduce_only=False,
    #     close_on_trigger=False
    # ).result()

    print(result)
    return 'test'

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

