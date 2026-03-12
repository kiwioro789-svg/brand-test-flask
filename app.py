import os
import json
import requests
from flask import Flask, request, abort, render_template, jsonify

# 【修正點 1：使用正確的 v3 物件名稱 TextMessage, FlexMessage, QuickReplyItem】
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest, 
    TextMessage, ReplyMessageRequest, QuickReply, QuickReplyItem, 
    MessageAction, FlexMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ==========================================
# 1. 環境變數設定 
# ==========================================
access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
channel_secret = os.getenv('CHANNEL_SECRET')
liff_id = os.getenv('LIFF_ID')
notion_token = os.getenv('NOTION_TOKEN')
notion_db_id = os.getenv('NOTION_DATABASE_ID')

configuration = Configuration(access_token=access_token)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
handler = WebhookHandler(channel_secret)


# ==========================================
# 2. 品牌診斷小遊戲：題庫與變數
# ==========================================
questions = {
    "Q1": {"text": "💭 Q1. 如果你的品牌是一個人，他會是：", "options": ["剛畢業的新鮮人，充滿熱血", "熱愛社交的創意人", "冷靜理性的專業人士", "成熟穩重、有魅力的領導者"]},
    "Q2": {"text": "🎨 Q2. 你的品牌色系更接近哪一種？", "options": ["柔和白灰，乾淨簡約", "暖橘粉，溫暖有故事", "高飽和色，創意滿滿", "黑金配色，質感高端"]},
    "Q3": {"text": "🚀 Q3. 當你在經營品牌時，最享受的瞬間是？", "options": ["客人第一次認識品牌", "設計或拍攝時的創作過程", "收到正面回饋", "看見品牌越來越有影響力"]},
    "Q4": {"text": "💬 Q4. 若品牌有一句 slogan，你會選哪種語氣？", "options": ["一步一腳印，從零開始", "用故事溫暖市場", "做自己風格的主角", "讓專業說話"]},
    "Q5": {"text": "✨ Q5. 你的品牌最需要的超能力是？", "options": ["讓人一眼記住的視覺感", "感動人心的內容力", "自動吸引客戶的行銷力", "穩定發展的策略力"]},
    "Q6": {"text": "🗺️ Q6. 如果品牌是一場旅程，現在你覺得自己在哪？", "options": ["剛整理行李，準備出發", "走在途中，開始有風景", "已達到第一個目的地", "正在規劃下一趟旅程"]}
}

brand_types = [
    ("🌱 創造型品牌", "你充滿熱情與想法，品牌剛萌芽。建議聚焦於品牌定位與清晰視覺形象，讓世界看到你的創意！"),
    ("🌿 故事型品牌", "你重視情感與連結，品牌有故事與溫度。建議用影像與社群內容，建立品牌的真實感與人味。"),
    ("🌳 風格型品牌", "你擁有明確的設計感與一致的風格。接下來可以透過網站與形象影片，提升專業與辨識度。"),
    ("🌺 領導型品牌", "你的品牌成熟且有影響力。建議整合行銷策略，打造品牌聯名與高階市場價值。")
]

user_answers = {}

def calculate_result(answers):
    score = sum([int(a) for a in answers])
    if score <= 6: return brand_types[0]
    elif score <= 12: return brand_types[1]
    elif score <= 18: return brand_types[2]
    else: return brand_types[3]


# ==========================================
# 3. 核心功能：傳送資料到 Notion API
# ==========================================
def send_to_notion(name, phone, user_id, project):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": {"database_id": notion_db_id},
        "properties": {
            "姓名": {
                "title": [{"text": {"content": name}}]
            },
            "電話": {
                "rich_text": [{"text": {"content": phone}}]
            },
            "LINE ID": {
                "rich_text": [{"text": {"content": user_id}}]
            },
            "項目": {
                "rich_text": [{"text": {"content": project}}]
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Notion API 錯誤: {response.text}")
        return False
    return True


# ==========================================
# 4. 前端 LIFF 報名系統 API
# ==========================================
@app.route('/liff/form')
def liff_form():
    return render_template('liff_form.html', liff_id=liff_id)

@app.route('/api/submit_form', methods=['POST'])
def submit_form():
    data = request.get_json()
    user_id = data.get('userId', '未知ID')
    name = data.get('name', '未填寫')
    phone = data.get('phone', '未填寫')
    project = data.get('project', '未選擇')

    success = send_to_notion(name, phone, user_id, project)

    if success:
        try:
            # 【修正點 2：使用 TextMessage】
            success_msg = TextMessage(
                text=f"🎉 報名成功！\n\n已收到您的需求：\n姓名：{name}\n電話：{phone}\n項目：{project}\n\n我們將盡快與您聯繫！"
            )
            messaging_api.push_message(PushMessageRequest(to=user_id, messages=[success_msg]))
        except Exception as e:
            print(f"推播失敗: {e}")
        return jsonify({"status": "success", "message": "報名已記錄到 Notion！"})
    else:
        return jsonify({"status": "error", "message": "寫入 Notion 失敗"}), 500


# ==========================================
# 5. LINE Webhook 處理聊天訊息
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

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    msg = event.message.text.strip()
    reply_token = event.reply_token
    user_id = event.source.user_id

    # ----------------------------------------
    # 邏輯 1：使用者正在進行「品牌診斷小遊戲」
    # ----------------------------------------
    if user_id in user_answers and msg not in ["選單", "功能", "我要報名", "價目表"]:
        step = user_answers[user_id]["step"]
        
        try:
            ans_index = questions[f"Q{step}"]["options"].index(msg) + 1
        except ValueError:
            ans_index = 0  

        user_answers[user_id]["answers"].append(ans_index)
        step += 1
        user_answers[user_id]["step"] = step

        if step <= 6:
            q = questions[f"Q{step}"]
            # 【修正點 3：使用 QuickReplyItem】
            buttons = [QuickReplyItem(action=MessageAction(label=opt[:20], text=opt)) for opt in q["options"]]
            qr = QuickReply(items=buttons)
            
            messaging_api.reply_message(
                ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=q["text"], quick_reply=qr)])
            )
        else:
            result_title, result_text = calculate_result(user_answers[user_id]["answers"])
            del user_answers[user_id] 
            
            replay_qr = QuickReply(items=[QuickReplyItem(action=MessageAction(label="再玩一次", text="再玩一次"))])
            
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[
                        TextMessage(text=f"🎉 品牌診斷完成！\n\n結果: {result_title}\n建議: {result_text}"),
                        TextMessage(text="想要再玩一次嗎？", quick_reply=replay_qr)
                    ]
                )
            )
        return

    # ----------------------------------------
    # 邏輯 2：觸發啟動小遊戲
    # ----------------------------------------
    if "品牌診斷" in msg or msg == "再玩一次":
        user_answers[user_id] = {"step": 1, "answers": []}
        q = questions["Q1"]
        buttons = [QuickReplyItem(action=MessageAction(label=opt[:20], text=opt)) for opt in q["options"]]
        qr = QuickReply(items=buttons)
        
        messaging_api.reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=q["text"], quick_reply=qr)])
        )
        return

    # ----------------------------------------
    # 邏輯 3：呼叫 Quick Reply 總選單
    # ----------------------------------------
    if "選單" in msg or "功能" in msg or "測試" in msg:
        quick_reply_buttons = [
            QuickReplyItem(action=MessageAction(label="📝 我要報名", text="我要報名")),
            QuickReplyItem(action=MessageAction(label="🎮 品牌診斷", text="品牌診斷小遊戲")),
            QuickReplyItem(action=MessageAction(label="💰 價目表", text="價目表"))
        ]
        qr = QuickReply(items=quick_reply_buttons)
        messaging_api.reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text="請選擇您需要的服務：", quick_reply=qr)])
        )
        return

    # ----------------------------------------
    # 邏輯 4：讀取 Flex Message (價目表)
    # ----------------------------------------
    if msg == "價目表":
        try:
            with open('flex_templates/price.json', 'r', encoding='utf-8') as f:
                flex_data = json.load(f)
            # 【修正點 4：使用 FlexMessage】
            messaging_api.reply_message(
                ReplyMessageRequest(reply_token=reply_token, messages=[FlexMessage(alt_text="這是價目表", contents=flex_data)])
            )
        except Exception as e:
            print(f"Flex讀取錯誤: {e}")
            messaging_api.reply_message(
                ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text="目前無法讀取卡片喔！請確認檔案是否存在。")])
            )
        return

    # ----------------------------------------
    # 邏輯 5：預設回覆
    # ----------------------------------------
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text=f"收到您的訊息：「{msg}」\n您可以輸入「選單」來查看所有功能！")]
        )
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)