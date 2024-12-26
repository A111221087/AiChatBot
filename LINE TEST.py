from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, URITemplateAction, MessageTemplateAction)
import logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Flask app initialization
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:123456@127.0.0.1:5432/milk5'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# LINE Bot API and WebhookHandler initialization
line_bot_api = LineBotApi('AbjmoLU+M+c53f5Q+ScyauW3Mp//wl7AgwvxWu6VLjAj1SVQL1Ax79sT34uUT8pRXW23cNiSS9WiLAbTqOo2VXBd2gktSo3Q33rcJZ5FKOBW4oPSCoBg772gUYEtvestPTHVF/PRu5RFGflAv+alkgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('95abc1bed0d3fe3a8a32e859e6dfd3ca')

logging.basicConfig(level=logging.ERROR)

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
        abort(400)
    return 'OK'

# Handle text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    mtext = event.message.text

    if mtext.startswith("線上預訂"):
        handle_reservation(event, mtext)
    elif mtext == '@店家資訊':
        sendButton(event)
    elif mtext == '@排行榜':
        sendConfirm(event)
    elif mtext == '@線上預訂':
        sendPhoneNumber(event)
    elif mtext == '@活動通知':
        sendEventNotification(event)
    elif mtext == '@分享活動':
        sendShareMessage(event)

# Handle reservation
def handle_reservation(event, mtext):
    try:
        # 解析輸入資料
        parts = mtext.replace("線上預訂", "").strip().split(',')
        if len(parts) != 6:
            raise ValueError("格式錯誤！請輸入：線上預訂 姓名,電話,日期(YYYY-MM-DD),時間(HH:MM),人數,飲料")

        name = parts[0].strip()
        phone = parts[1].strip()
        date = datetime.strptime(parts[2].strip(), '%Y-%m-%d').date()
        time = datetime.strptime(parts[3].strip(), '%H:%M').time()
        people = int(parts[4].strip())
        drink = parts[5].strip()

        # 檢查飲料名稱是否合法
        if not drink or len(drink) > 255:
            raise ValueError("飲料名稱無效或過長！請重新輸入。")

        logging.error(f"Parsed Data - Name: {name}, Phone: {phone}, Date: {date}, Time: {time}, People: {people}, Drink: {drink}")

        # 新增預訂資料
        new_reservation = Reservation(name=name, phone=phone, date=date, time=time, people=people, drink=drink)
        db.session.add(new_reservation)
        db.session.commit()

        # 回應使用者
        reply = (f"預訂成功！\n姓名: {name}\n電話: {phone}\n日期: {date}\n時間: {time}\n人數: {people}\n飲料: {drink}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    except ValueError as ve:
        logging.error(f"ValueError: {ve}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(ve)))
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"發生錯誤：{e}"))



# Store information button template
def sendButton(event):  # 按鈕樣板 for 店家資訊
    try:
        message = TemplateSendMessage(
            alt_text='店家資訊',
            template=ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/W16O7ps.png',  # 顯示的圖片
                title='五十藍',  # 店家名稱
                text='地址: 新北市三峽區光明路100-3號\n營業時間: 7:30 - 21:00',  # 店家地址和營業時間
                actions=[
                    MessageTemplateAction(  # 顯示文字訊息
                        label='電話聯絡',
                        text='@線上預訂'
                    ),
                    URITemplateAction(  # 開啟地圖位置
                        label='查看地圖',
                        uri='https://www.google.com/maps?q=237%E6%96%B0%E5%8C%97%E5%B8%82%E4%B8%89%E5%B3%BD%E5%8D%80%E5%85%89%E6%98%8E%E8%B7%AF100-3%E8%99%9F50%E5%B5%90+%E4%B8%89%E5%B3%BD%E5%85%89%E6%98%8E%E5%BA%97&ftid=0x34681b3771d20a67:0x31b5c6f517c04f56&entry=gps&lucs=,94224825,94227247,94227248,94231188,47071704,47069508,94218641,94203019,47084304,94208458,94208447&g_ep=CAISDTYuMTM5LjAuOTA4MzAYACCIJypjLDk0MjI0ODI1LDk0MjI3MjQ3LDk0MjI3MjQ4LDk0MjMxMTg4LDQ3MDcxNzA0LDQ3MDY5NTA4LDk0MjE4NjQxLDk0MjAzMDE5LDQ3MDg0MzA0LDk0MjA4NDU4LDk0MjA4NDQ3QgJUVw%3D%3D&g_st=il'  # Replace with actual location coordinates
                    ),
                    URITemplateAction(  # 開啟網頁
                        label='查看網站',
                        uri='http://50lan.com/web/news.asp'  # Replace with actual website URL
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='發生錯誤！'))


# Phone number and online reservation
def sendPhoneNumber(event):
    try:
        phone_number = '0987-654-321'
        website_url = 'https://order.nidin.shop/menu/12738'
        message = TextSendMessage(text=f'客服專線是：{phone_number}\n請訪問我們的網站：{website_url}')
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        logging.error(f"Error sending phone number: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# Activity notification
def sendEventNotification(event):
    try:
        message = TemplateSendMessage(
            alt_text='活動通知',
            template=ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/dOneP9g.jpeg',
                title='🎉 最新活動通知',
                text='元旦活動優惠！凡購買飲品滿 $200，即贈限量周邊一份。\n活動期間：2024/01/01 - 2024/01/07',
                actions=[
                    URITemplateAction(
                        label='了解詳情',
                        uri='https://www.easycard.com.tw/offer?cls=1506473503,1508721809,1506473490,&id=1702024188'
                    ),
                    MessageTemplateAction(
                        label='分享給朋友',
                        text='@分享活動'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        logging.error(f"Error sending event notification: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# Share activity message
def sendShareMessage(event):
    try:
        message = TextSendMessage(
            text='🎉 快來參加元旦優惠活動！凡購買飲品滿 $200，即贈限量周邊一份。\n活動詳情：https://www.easycard.com.tw/offer?cls=1506473503,1508721809,1506473490,&id=1702024188'
        )
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        logging.error(f"Error sending share message: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# Carousel template for rankings
def sendConfirm(event):
    try:
        message = TemplateSendMessage(
            alt_text='排行榜',
            template=ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/70dj7l7.png',
                title='Top1 布丁奶茶',
                text='香濃滑順，甜而不膩，口感豐富。',
                actions=[
                    URITemplateAction(
                        label='查看詳情',
                        uri='http://50lan.com/web/morenews.asp?id=334'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
    except Exception as e:
        logging.error(f"Error sending ranking: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all defined tables
    app.run()
