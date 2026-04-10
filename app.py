import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    FlexSendMessage, PostbackEvent,
    QuickReply, QuickReplyButton, MessageAction, URIAction
)
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# IG 的 LIFF 連結或網址 (請填入與 setup_menu.py 相同的那一個)
IG_URL = "https://liff.line.me/2008759042-aJUUZRGH"

# ==========================================
# 核心 Webhook 入口
# ==========================================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ==========================================
# 事件處理：Postback (按鈕回傳)
# ==========================================
@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    
    # 處理滿意度調查的「不滿意」按鈕
    if data == 'action=survey_bad':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="感謝您的意見！我們會持續改進，期待下次能為您提供更好的服務。")
        )
    
    # 注意：因為使用了 Alias，選單切換 (switch_to_a/b) 由 LINE 手機端直接處理，
    # 這裡不需要寫程式碼，後端不會收到切換的 Postback 事件。

# ==========================================
# 事件處理：文字訊息
# ==========================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    
    # 1. 觸發滿意度調查
    if msg == "調查":
        send_survey_flex(event.reply_token)
        
    # 2. 其他文字回應 (自動附加 Quick Reply)
    else:
        # 建立共用的 Quick Reply 選單
        quick_reply_menu = make_quick_replies()
        
        reply_text = f"收到：{msg}"
        
        # 根據關鍵字做簡單回應 (模擬客服)
        if msg.lower() == "video":
            reply_text = "這是我們的最新影片：https://youtu.be/example"
        elif msg.lower() == "contact":
            reply_text = "聯絡我們：\n電話：09-xxx-xxx\n地址：台北市信義區..."
        elif msg.lower() == "price list":
            reply_text = "【價目表】\n1. 攝影$2000/1hr\n2. line@ $10000"
        elif msg.lower() == "work":
            reply_text = "這是我們的作品集..."
        elif msg.lower() == "q&a":
            reply_text = "常見問題：\nQ: 商家公司W？\n A: 獨立作業"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text, quick_reply=quick_reply_menu)
        )

# ==========================================
# 輔助函式：發送 Flex Message
# ==========================================
def send_survey_flex(reply_token):
    try:
        # 讀取你的 flex_templates/card.json
        with open('flex_templates/card.json', 'r', encoding='utf-8') as f:
            flex_template = json.load(f)
        
        flex_message = FlexSendMessage(
            alt_text='邀請您填寫滿意度調查',
            contents=flex_template
        )
        line_bot_api.reply_message(reply_token, flex_message)
    except Exception as e:
        print(f"Error loading flex json: {e}")
        line_bot_api.reply_message(reply_token, TextSendMessage(text="抱歉，目前無法載入調查表。"))

# ==========================================
# 輔助函式：製作 Quick Reply (對應圖文選單選項)
# ==========================================
def make_quick_replies():
    """
    建立包含圖文選單所有選項的快速回覆按鈕
    """
    return QuickReply(items=[
        # 1. Instagram (連結)
        QuickReplyButton(
            action=URIAction(label="Instagram", uri=IG_URL)
        ),
        # 2. Video
        QuickReplyButton(
            action=MessageAction(label="Video", text="video")
        ),
        # 3. Contact
        QuickReplyButton(
            action=MessageAction(label="Contact", text="contact")
        ),
        # 4. Price List
        QuickReplyButton(
            action=MessageAction(label="Price List", text="price list")
        ),
        # 5. Work
        QuickReplyButton(
            action=MessageAction(label="Work", text="work")
        ),
        # 6. Q&A
        QuickReplyButton(
            action=MessageAction(label="Q&A", text="Q&A")
        ),
        # 7. 加一個「調查」按鈕，方便測試
        QuickReplyButton(
            action=MessageAction(label="滿意度調查", text="調查")
        ),
    ])

if __name__ == "__main__":
    app.run(port=5000, debug=True)