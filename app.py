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

try:
    from meta import SQLALCHEMY_DATABASE_URI, SECRET_KEY, DEBUG, channel_access_token, channel_secret, api_key1, api_secret1

except:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = False
    channel_access_token = os.environ['CHANNEL_ACCESS']
    channel_secret = os.environ['CHANNEL_SECRET']
    api_key1 = os.environ['api_key1']
    api_secret1 = os.environ['api_secret1']


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


@app.route("/tv_callback/<string:tvdata>", methods=['POST', 'GET'])
def callback(tvdata):
    sideBS = "Buy"
    account = 1
    coin = 'BTC'
    top = 31723 # first entry
    bottom = 31344 #last entry
    stop = 31100
    profit = 35800

    leverage = 4
    print('TV_CALLBACK', tvdata)
    client = bybit.bybit(test=False, api_key=api_key1, api_secret=api_secret1)
    print(client)

    funds = client.Wallet.Wallet_getBalance(coin=coin).result()[0]['result'][coin]['available_balance']
    print(funds)

    line_bot_api.broadcast(TextSendMessage(text=client+fund))
    return tvdata


@handler.add(FollowEvent)
def handle_follow():
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

