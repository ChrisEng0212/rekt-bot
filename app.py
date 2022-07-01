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

def getInfo(get):

    position = session.my_position(symbol="BTCUSD")['result']['size']
    funds = session.get_wallet_balance()['result']['BTC']['equity']
    last_price = session.latest_information_for_symbol(symbol="BTCUSD")['result'][0]['last_price']
    price = int(last_price.split('.')[0])

    return get


def placeOrder(side, price, stop_loss, take_profit, type, qty):

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

    print(order)

    message = order['ret_msg']
    data = json.dumps(order['result'])

    try:
        line_bot_api.broadcast(TextSendMessage(text='ORDER PLACED ' + side + ' lp: ' + str(price) + ' stop: '  + str(stop_loss) + ' profit: ' + str(take_profit) + ' / '  + message + ' / ' + data))
    except:
        line_bot_api.broadcast(TextSendMessage(text='ORDER LINE FAILED' + data))
        print('ORDER LINE CANCEL')



def cancelOrder():
    print(session.cancel_all_active_orders(symbol="BTCUSD"))



position = {'id': 0,
           'position_idx': 0,
           'mode': 0,
           'user_id': 557296,
           'risk_id': 1,
           'symbol': 'BTCUSD',
           'side': 'None',
           'size': 0,
           'position_value': '0',
           'entry_price': '0',
           'is_isolated': True,
           'auto_add_margin': 0,
           'leverage': '3',
           'effective_leverage': '3',
           'position_margin': '0',
           'liq_price': '0',
           'bust_price': '0',
           'occ_closing_fee': '0',
           'occ_funding_fee': '0',
           'take_profit': '0',
           'stop_loss': '0',
           'trailing_stop': '0',
           'position_status': 'Normal',
           'deleverage_indicator': 0,
           'oc_calc_data': '{"blq":0,"slq":0,"bmp":0,"smp":0,"bv2c":0.33473334,"sv2c":0.33433334}',
           'order_margin': '0',
           'wallet_balance': '0.07579818',
           'realised_pnl': '-0.00118163',
           'unrealised_pnl': 0,
           'cum_realised_pnl': '-0.55798444',
           'cross_seq': 14093364496,
           'position_seq': 4438196956,
           'created_at': '2019-07-02T02:22:32Z',
           'updated_at': '2022-07-01T04:04:06.238822396Z',
           'tp_sl_mode': 'Full'
        }

funds = {'BTC': {'equity': 0.07579818,
                 'available_balance': 0.07579818,
                 'used_margin': 0,
                 'order_margin': 0,
                 'position_margin': 0,
                 'occ_closing_fee': 0,
                 'occ_funding_fee': 0,
                 'wallet_balance': 0.07579818,
                 'realised_pnl': -0.00118163,
                 'unrealised_pnl': 0,
                 'cum_realised_pnl': -0.55798444,
                 'given_cash': -3.0506730319093816e-31,
                 'service_cash': 0}
         }



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
    tx = event.message.text
    userID = event.source.user_id


    line_bot_api.broadcast(TextSendMessage(text='some one else tried to use strategy bot ' + str(userID)))


    ret = getInfo(tx)
    if ret == tx:
        line_bot_api.broadcast(TextSendMessage(text='No Action'))
    else:
        line_bot_api.broadcast(TextSendMessage(text=str(ret)))


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

