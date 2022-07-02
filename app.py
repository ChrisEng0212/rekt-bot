from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy

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

    if type == 'Market':
        price = None

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
        line_bot_api.broadcast(TextSendMessage(text='ORDER PLACED ' + side + ' lp: ' + str(price) + ' stop: '  + str(stop_loss) + ' profit: ' + str(take_profit) + ' / '  + message + ' / ' + data))
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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    tx = event.message.text
    userID = event.source.user_id

    if userID != BaseConfig.userID:
        line_bot_api.broadcast(TextSendMessage(text='some one else tried to use strategy bot ' + str(userID)))
        return False

    info = {'position' :session.my_position(symbol="BTCUSD")['result']['size'],
            'funds' : session.get_wallet_balance()['result']['BTC']['equity'],
            'price' : int(session.latest_information_for_symbol(symbol="BTCUSD")['result'][0]['last_price'].split('.')[0]),
            'high' : int(session.latest_information_for_symbol(symbol="BTCUSD")['result'][0]['high_price_24h'].split('.')[0]),
            'low' : int(session.latest_information_for_symbol(symbol="BTCUSD")['result'][0]['low_price_24h'].split('.')[0]),
            'order' : 'b-m-p-sl-tp-q',
            'cancel' : session.cancel_all_active_orders(symbol="BTCUSD")['ret_msg']
            }

    deets = tx.split(' ')
    print('DEETS', deets)
    print('POSITION', int(info['position']))

    if int(info['position']) != 0 and len(deets) >= 6:
        line_bot_api.broadcast(TextSendMessage(text='Position On ' + str(info['position']) ))
    elif tx in info:
        line_bot_api.broadcast(TextSendMessage(text=info[tx]))
    elif len(deets) >= 6:


        s = {'b': 'Buy',
             's': 'Sell'
             }

        p = {'b': -1,
             's': 1
             }

        t = {'m': 'Market',
             'l': 'Limit'
             }

        side = s[deets[0]]
        type = t[deets[1]]
        price = info['price'] + int(deets[2])*p[deets[0]]
        stop_loss = info['price'] + int(deets[3])*p[deets[0]]
        take_profit = info['price'] - int(deets[4])*p[deets[0]]
        qty = int(deets[5])

        placeOrder(side, type, price, stop_loss, take_profit, qty)
        #placeOrder(side, type, price, stop_loss, take_profit,  qty)
    else:
        line_bot_api.broadcast(TextSendMessage(text='No Action'))




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

