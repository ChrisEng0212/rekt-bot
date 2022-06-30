from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy

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


@app.route('/')
def home():

    return json.dumps('Hello RektBot!')

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
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_id = event.message.id
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text + str(message_id)))


def placeOrder(side, ticker, stop_loss, take_profit, last_price, units, limit):

    # placeOrder(side, ticker, stop_loss, take_profit, last_price, deets[0], deets[3])

    print('PLACEORDER', side, ticker, stop_loss, take_profit, last_price, units, limit)

    price = last_price - limit
    if side[0] == 'S':
        price = last_price + limit

    result = client.LinearOrder.LinearOrder_new(
        side=side,
        symbol=ticker,
        order_type="Limit",
        stop_loss=stop_loss,
        take_profit=take_profit,
        qty=units,
        price=price,
        time_in_force="GoodTillCancel",
        reduce_only=False,
        close_on_trigger=False

    ).result()

    print('RESULT', result)

    message = result[0]['ret_msg']
    data = json.dumps(result[0]['result'])

    try:
        line_bot_api.broadcast(TextSendMessage(text='ORDER PLACED ' + ticker + side + ' lp: ' + str(last_price) + ' stop: '  + str(stop_loss) + ' profit: ' + str(take_profit) + ' / '  + message + ' / ' + data))
    except:
        line_bot_api.broadcast(TextSendMessage(text='ORDER LINE FAILED' + data))
        print('ORDER LINE CANCEL', ticker)



@app.route("/order/<string:code>/<string:side>/<string:details>/", methods=['POST', 'GET'])
def orderBot(code, side, details):
    #line_bot_api.broadcast(TextSendMessage(text='signal'))

    #details = '2000-200-100-20'

    deets = details.split('-')

    print('UNITS', deets)

    if code != key_code:
        line_bot_api.broadcast(TextSendMessage(text='Invalid Code: ' + code))
        return 'Invalid'

    coin_number = 0
    ticker = 'BTCUSD'
    print('COIN NUM', coin_number)
    last_price = float(client.Market.Market_symbolInfo().result()[0]['result'][int(coin_number)]['last_price'])

    position = client.LinearPositions.OrderPositions_myPosition(symbol=ticker).result()[0]['result']
    for x in position:
        print('POSITION', position)
        if x['size'] > 0:
            line_bot_api.broadcast(TextSendMessage(text='POSITION CANCEL'))
            print('POSITION CANCEL')
            return 'POSITION CANCEL'

    # entryDict = {
    #     "dollars" : 100,
    #     "margin" : 5,
    #     "drawDown" : 0.996,
    #     "drawUp" : 1.004,
    #     "buyProfit" : 1.009,
    #     "sellProfit" : 0.991,
    #     "roundStops" : 4,
    #     "roundUnits" : 1

    #  maxStop == 0.8
    # drawUp = 1=0.008  (maxStop/100)
    # }



    ''' GET SLTP '''
    stop_loss = last_price - deets[1]
    take_profit = last_price + deets[2]

    if side[0] == 'S':
        stop_loss = last_price + deets[1]
        take_profit = last_price - deets[2]


    print("STOP/PROFIT:", side, stop_loss, take_profit)


    placeOrder(side, ticker, stop_loss, take_profit, last_price, deets[0], deets[3])


    return 'orderAction'




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

    position = client.LinearPositions.LinearPositions_myPosition(symbol=ticker).result()[0]['result']
    for x in position:
        print('POSITION', position)
        if x['size'] > 0:
            line_bot_api.broadcast(TextSendMessage(text='POSITION CANCEL'))
            print('POSITION CANCEL')
            return 'POSITION CANCEL'

    # entryDict = {
    #     "dollars" : 100,
    #     "margin" : 5,
    #     "drawDown" : 0.996,
    #     "drawUp" : 1.004,
    #     "buyProfit" : 1.009,
    #     "sellProfit" : 0.991,
    #     "roundStops" : 4,
    #     "roundUnits" : 1

    #  maxStop == 0.8
    # drawUp = 1=0.008  (maxStop/100)
    # }

    bbwp = BBWPV.query.filter_by(ticker=ticker, interval=interval).first()
    entryDict = json.loads(bbwp.info)
    print('ENTRY DICT', entryDict)

    ''' GET SLTP '''
    stop_loss = 'SL_NONE'
    take_profit = 'TP_NONE'


    if action == 'Buy':
        drawDown = 1 - entryDict['maxStop']/100
        stop_loss = round(float(open)*drawDown, entryDict['roundStops'])

        buyP = 1 + entryDict['profit']/100
        take_profit = round(float(open)*buyP, entryDict['roundStops'])

    elif action == 'Sell':
        drawDown = 1 + entryDict['maxStop']/100
        stop_loss = round(float(open)*drawDown, entryDict['roundStops'])

        sellP = 1 - entryDict['profit']/100
        take_profit = round(float(open)*sellP, entryDict['roundStops'])


    print("STOP/PROFIT:", action, stop_loss, take_profit)


    ''' GET UNITS'''
    dollars = entryDict['dollars']
    margin = entryDict['margin']
    units = round(dollars/last_price, entryDict['roundUnits'])*margin

    print('UNITS', units)

    placeOrder(action, ticker, stop_loss, take_profit, last_price, units, interval, open)


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


    ticker = 'MATICUSDT'
    interval = '15'
    action = 'Buy'
    open = float(client.Market.Market_symbolInfo().result()[0]['result'][21]['last_price'])


    # stop_loss = round(last_price*0.996, 3)
    # take_profit = round(last_price*1.004, 3)
    # print(stop_loss, take_profit)

    #coin_number = list(coinList.keys())[list(coinList.values()).index(ticker)]

    bbwp = BBWPV.query.filter_by(ticker=ticker, interval=interval).first()
    entryDict = json.loads(bbwp.info)
    print('ENTRY DICT', entryDict)

    ''' GET SLTP '''
    stop_loss = 'SL_NONE'
    take_profit = 'TP_NONE'





    if action == 'Buy':
        drawDown = 1 - entryDict['maxStop']/100
        stop_loss = round(float(open)*drawDown, entryDict['roundStops'])

        buyP = 1 + entryDict['profit']/100
        take_profit = round(float(open)*buyP, entryDict['roundStops'])

    elif action == 'Sell':
        drawDown = 1 + entryDict['maxStop']/100
        stop_loss = round(float(open)*drawDown, entryDict['roundStops'])

        sellP = 1 - entryDict['profit']/100
        take_profit = round(float(open)*sellP, entryDict['roundStops'])


    print("STOP/PROFIT:", action, open, stop_loss, take_profit)
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

