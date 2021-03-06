from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import pprint

from tokens import BaseConfig

from pybit import inverse_perpetual


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = BaseConfig.SQLALCHEMY_DATABASE_URI
app.config['SECRET_KEY'] = BaseConfig.SECRET_KEY
app.config['DEBUG'] = BaseConfig.DEBUG
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


from linebot import (
    LineBotApi, WebhookHandler, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

# Channel Access Token
line_bot_api = LineBotApi(BaseConfig.channel_access_token)
# Channel Secret
handler = WebhookHandler(BaseConfig.channel_secret)

parser = WebhookParser(BaseConfig.channel_secret)

session = inverse_perpetual.HTTP(
    endpoint='https://api.bybit.com',
    api_key=BaseConfig.api_key1,
    api_secret=BaseConfig.api_secret1
)
ws = inverse_perpetual.WebSocket(
    test=False,
    api_key=BaseConfig.api_key1,
    api_secret=BaseConfig.api_secret1
)

print('SESSION', session)


## Sesson Actions


def placeOrder(side, type, price, stop_loss, take_profit, qty):

    #line_bot_api.broadcast(TextSendMessage(text='Order Placement'))
    print('tp', take_profit, price)

    if type == 'Market':
        price = None

    spread = False
    if type == 'Spread':
        spread = True
        type = 'Limit'

    order = session.place_active_order(
    symbol="BTCUSD",
    side=side,
    order_type=type,
    price=price,
    stop_loss = stop_loss,
    take_profit = take_profit,
    qty=qty,
    time_in_force="GoodTillCancel"
    )

    print('ORDER', order)

    message = order['ret_msg']
    data = json.dumps(order['result'])

    try:
        string = 'ORDER PLACED ' + side + ' lp: ' + str(price) + ' stop: '  + str(stop_loss) + ' profit: ' + str(take_profit) + ' / '  + message
        if not spread:
            line_bot_api.broadcast(TextSendMessage(text=string + ' / ' + data))
        else:
            print(string)
    except:
        line_bot_api.broadcast(TextSendMessage(text='ORDER LINE FAILED' + data))
        print('ORDER LINE CANCEL')


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


def getHiLow(data):

    print('GET HI LOW ', data)

    hi1 = int(data[0]['high'].split('.')[0])
    hi2 = int(data[1]['high'].split('.')[0])
    low1 = int(data[0]['low'].split('.')[0])
    low2 = int(data[1]['low'].split('.')[0])

    mHi = max(hi1, hi2)
    mLow = min(low1, low2)

    return { 'low' : mLow, 'high' : mHi }




@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):


    #tx = event['message']

    tx = event.message.text
    userID = event.source.user_id

    if userID != BaseConfig.userID:
        line_bot_api.broadcast(TextSendMessage(text='some one else tried to use strategy bot ' + str(userID)))
        return False

    now = datetime.now()
    timestamp = int(datetime.timestamp(now)) - 7200
    print("timestamp =", timestamp)

    info = {'position' :session.my_position(symbol="BTCUSD")['result']['size'],
            'funds' : session.get_wallet_balance()['result']['BTC']['equity'],
            'pnl' : session.get_wallet_balance()['result']['BTC']['realised_pnl'],
            'price' : int(session.latest_information_for_symbol(symbol="BTCUSD")['result'][0]['last_price'].split('.')[0]),
            'hl' : session.query_kline(symbol="BTCUSD", interval="60", from_time=str(timestamp))['result'],
            'cancel' : session.cancel_all_active_orders(symbol="BTCUSD")['ret_msg'],
            'order' : 'side(bs)-type(mls)-limit(diff$)-sl/tp-qnt(shp)'
            }

    deets = tx.split(' ')
    print('DEETS', deets)

    line_bot_api.broadcast(TextSendMessage('Command Received'))

    position = info['position']
    print('POSITION', position)


    if position != 0 and len(deets) >= 5:
        line_bot_api.broadcast(TextSendMessage(text='Position On ' + str(position) ))
    elif tx in info:
        if tx == 'hl':

            hl = getHiLow(info['hl'])

            line_bot_api.broadcast(TextSendMessage(text=json.dumps(hl)))

        elif tx == 'pnl':
            line_bot_api.broadcast(TextSendMessage(text=tx + ': ' + str(info[tx])))
        else:
            line_bot_api.broadcast(TextSendMessage(text=tx + ': ' + str(info[tx])))
    elif len(deets) >= 5:

        s = {'b': 'Buy',
             's': 'Sell'
             }

        p = {'Buy': -1,
             'Sell': 1
             }

        t = {'m': 'Market',
             'l': 'Limit',
             's': 'Spread'
             }

        side = s[deets[0]]
        type = t[deets[1]]
        limit = int(deets[2])
        sltp = deets[3] # stop loss / take profit
        quant = deets[4]


        data = info['hl']

        close = int(data[1]['close'].split('.')[0])

        price = close + limit*p[side]

        ''' get stop losses and take profit based on deets'''

        if sltp == 'hl':
            # get high low of last 2 hours and set as stops
            lh = getHiLow(data)
            print('lh', lh)

            low = lh['low']
            high = lh['high']

            if side == 'Buy':
                stop_loss = low
                take_profit = high
            else:
                stop_loss = high
                take_profit = low

            if stop_loss > close or take_profit < close:
                string = 'HighLow targets out of bounds ' + str(close) + ' ' + str(low) + ' ' + str(high)
                line_bot_api.broadcast(TextSendMessage(text=string))

        else:
            # set stops as +/- the limit value set or figure two seperate values and set that
            targets = sltp.split('/')
            if len(targets) > 1:
                stop_loss = price + int(targets[0])*p[side]
                take_profit = price - int(targets[1])*p[side]
            else:
                stop_loss = price + int(targets[0])*p[side]
                take_profit = price - int(targets[0])*p[side]


        '''# get quantity of trade'''

        q = {'s': 2000,
             'h': 1000,
             'p': 3000
             }

        if quant in q:
            qty = q[quant]
        else:
            qty = int(quant)

        if type == 'Spread':
            for i in range(limit):
                spreadLimit = close + i*p[side]
                placeOrder(side, type, spreadLimit, stop_loss, take_profit, qty/limit)
        else:
            placeOrder(side, type, price, stop_loss, take_profit, qty)

        #placeOrder(side, type, price, stop_loss, take_profit,  qty)
    else:
        string = 'No Action - Available Functions: '
        for x in info:
            string += x + ' - '

        string += info['order']

        line_bot_api.broadcast(TextSendMessage(text=string))

# event = {'message' : 'b s 10 hl 10',
#          'userID' : None
# }

# handle_message(event)

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
    app.run()

