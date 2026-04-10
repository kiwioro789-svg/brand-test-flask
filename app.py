import os
import requests
from flask import Flask, request, abort, render_template, jsonify
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest, 
    TextMessage, ReplyMessageRequest, QuickReply, QuickReplyItem, 
    MessageAction
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ==========================================
# 1. 配置環境變數
# ==========================================
line_token = os.getenv('LINE_TOKEN') 
channel_secret = os.getenv('CHANNEL_SECRET')
liff_id = os.getenv('LIFF_ID')
notion_token = os.getenv('NOTION_TOKEN')
notion_db_id = os.getenv('NOTION_DATABASE_ID')

configuration = Configuration(access_token=line_token) 
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
handler = WebhookHandler(channel_secret)

# ==========================================
# 2. 品牌診斷小遊戲設定
# ==========================================
questions = {
    "Q1": {"text": "💭 Q1. 如果你的品牌是一個人，他會是：", "options": ["熱血新鮮人", "創意人", "專業人士", "領導者"]},
    "Q2": {"text": "🎨 Q2. 你的品牌色系更接近哪一種？", "options": ["簡約白灰", "溫暖橘粉", "創意飽和色", "高端黑金"]},
    "Q3": {"text": "🚀 Q3. 最享受的瞬間是？", "options": ["客戶認識我", "創作過程", "收到回饋", "品牌影響力"]},
    "Q4": {"text": "💬 Q4. Slogan 語氣？", "options": ["踏實從零開始", "溫暖故事", "做主角", "專業說話"]},
    "Q5": {"text": "✨ Q5. 最需要的超能力？", "options": ["一眼記住", "內容力", "行銷力", "策略力"]},
    "Q6": {"text": "🗺️ Q6. 目前在哪個階段？", "options": ["準備出發", "開始有風景", "第一個目的地", "下一趟旅程"]}
}
brand_types = [("🌱 創造型", "建議聚焦視覺形象"), ("🌿 故事型", "建議強化內容連結"), ("🌳 風格型", "建議提升專業辨識"), ("🌺 領導型", "建議整合行銷策略")]
user_answers = {} 

def calculate_result(answers):
    score = sum([int(a) for a in answers])
    if score <= 6: return brand_types[0]
    elif score <= 12: return brand_types[1]
    elif score <= 18: return brand_types[2]
    else: return brand_types[3]

# ==========================================
# 3. Notion 寫入功能
# ==========================================
def send_to_notion(name, phone, user_id, project, remarks):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": notion_db_id},
        "properties": {
            "姓名": {"title": [{"text": {"content": name}}]},
            "電話": {"rich_text": [{"text": {"content": phone}}]},
            "LINE ID": {"rich_text": [{"text": {"content": user_id}}]},
            "項目": {"rich_text": [{"text": {"content": project}}]},
            "備註": {"rich_text": [{"text": {"content": remarks}}]}
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200

# ==========================================
# 4. 路由 API
# ==========================================
@app.route('/liff/form')
def liff_form():
    return render_template('liff_form.html', liff_id=liff_id)

@app.route('/api/submit_form', methods=['POST'])
def submit_form():
    data = request.get_json()
    if send_to_notion(
        data.get('name'), data.get('phone'), data.get('userId'),
        data.get('project'), data.get('remarks')
    ):
        try:
            msg = TextMessage(text=f"🎉 預約成功！\n姓名：{data.get('name')}\n項目：{data.get('project')}\n\n我們已經收到您的需求，將儘速與您聯繫！")
            messaging_api.push_message(PushMessageRequest(to=data.get('userId'), messages=[msg]))
        except: pass
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 500

# ==========================================
# 5. LINE 訊息處理
# ==========================================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    msg = event.message.text.strip()
    user_id = event.source.user_id
    reply_token = event.reply_token

    # 核心 Quick Reply 選單
    default_qr = QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="📝 我要預約", text="我要報名")),
        QuickReplyItem(action=MessageAction(label="🎮 品牌診斷", text="品牌診斷"))
    ])

    # 邏輯 A：觸發報名表單
    if "報名" in msg or "預約" in msg:
        if user_id in user_answers: del user_answers[user_id]
        return messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token, 
            messages=[TextMessage(text=f"請點擊下方網址開啟預約表單：\nhttps://liff.line.me/{liff_id}")]
        ))

    # 邏輯 B：啟動小遊戲
    if "診斷" in msg or "再玩" in msg:
        user_answers[user_id] = {"step": 1, "answers": []}
        q = questions["Q1"]
        qr = QuickReply(items=[QuickReplyItem(action=MessageAction(label=o[:20], text=o)) for o in q["options"]])
        return messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token, messages=[TextMessage(text=q["text"], quick_reply=qr)]
        ))

    # 邏輯 C：遊戲進行中
    if user_id in user_answers:
        step = user_answers[user_id]["step"]
        try:
            ans_index = questions[f"Q{step}"]["options"].index(msg) + 1
            user_answers[user_id]["answers"].append(ans_index)
            user_answers[user_id]["step"] += 1
            step = user_answers[user_id]["step"]
            if step <= 6:
                q = questions[f"Q{step}"]
                qr = QuickReply(items=[QuickReplyItem(action=MessageAction(label=o[:20], text=o)) for o in q["options"]])
                return messaging_api.reply_message(ReplyMessageRequest(
                    reply_token=reply_token, messages=[TextMessage(text=q["text"], quick_reply=qr)]
                ))
            else:
                res, advice = calculate_result(user_answers[user_id]["answers"])
                del user_answers[user_id]
                return messaging_api.reply_message(ReplyMessageRequest(
                    reply_token=reply_token, 
                    messages=[
                        TextMessage(text=f"結果：{res}\n{advice}"), 
                        TextMessage(text="接下來想做什麼呢？", quick_reply=default_qr)
                    ]
                ))
        except: 
            del user_answers[user_id]

    # 💡 邏輯 D：圖文選單觸發 Quick Reply
    menu_keywords = ["關於我們", "服務內容", "合作專案", "常見問題", "優惠與活動"]
    if msg in menu_keywords:
        return messaging_api.reply_message(ReplyMessageRequest(
            reply_token=reply_token, 
            messages=[TextMessage(text=f"{msg}", quick_reply=default_qr)]
        ))

    # 💡 邏輯 E：已讀不回
    # 只要不符合上述邏輯，程式會直接結束，不會傳送任何訊息，也不會報錯
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))