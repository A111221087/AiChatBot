from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, URITemplateAction, MessageTemplateAction)
import logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Flask app initialization
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://linetestcloud:UtEvi79s9kQjP87KR1Su2QolkbUCvSBo@dpg-ctn391btq21c73fddf1g-a.singapore-postgres.render.com/linetestcloud?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize LineBotApi
line_bot_api = LineBotApi(os.environ.get('Channel_Access_Token'))
handler = WebhookHandler(os.environ.get('Channel_Secret'))

logging.basicConfig(level=logging.DEBUG)

# Database models
class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    people = db.Column(db.Integer, nullable=False)
    drink = db.Column(db.String(255), nullable=False)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.Text)
    detail_url = db.Column(db.Text)

# Webhook callback route
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("Invalid Signature Error")
        abort(400)
    return 'OK'

# Handle text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    mtext = event.message.text

    if mtext.startswith("線上預訂"):
        handle_reservation(event, mtext)
    else:
        reply = "指令無效，請輸入正確的指令。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# Handle reservation
def handle_reservation(event, mtext):
    try:
        parts = mtext.replace("線上預訂", "").strip().split(',')
        if len(parts) != 6:
            raise ValueError("格式錯誤！請輸入：線上預訂 姓名,電話,日期(YYYY-MM-DD),時間(HH:MM),人數,飲料")
        name = parts[0].strip()
        phone = parts[1].strip()
        date = datetime.strptime(parts[2].strip(), '%Y-%m-%d').date()
        time = datetime.strptime(parts[3].strip(), '%H:%M').time()
        people = int(parts[4].strip())
        drink = parts[5].strip()
        new_reservation = Reservation(name=name, phone=phone, date=date, time=time, people=people, drink=drink)
        db.session.add(new_reservation)
        db.session.commit()
        reply = f"預訂成功！\n姓名: {name}\n電話: {phone}\n日期: {date}\n時間: {time}\n人數: {people}\n飲料: {drink}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(ve)))
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="發生錯誤，請稍後再試。"))

# Initialize database
@app.route('/init-db', methods=['GET'])
def init_db():
    try:
        db.create_all()
        return "Database initialized successfully!", 200
    except Exception as e:
        return f"Error initializing database: {e}", 500

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
