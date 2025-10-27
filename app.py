from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# 讀取 .env
load_dotenv()

app = Flask(__name__)

# LINE 設定
LINE_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
LINE_API = "https://api.line.me/v2/bot/message/reply"

# 小遊戲題目與 QuickReply 選項
questions = {
    "Q1": {
        "text": "🎯 Q1. 你的品牌目前階段是？",
        "options": ["剛起步／還在準備中", "已經營運中，但缺乏曝光", "品牌穩定，想升級形象", "其他"]
    },
    "Q2": {
        "text": "🎯 Q2. 目前你的主要推廣方式是？",
        "options": ["口碑、熟人介紹", "社群平台（IG／FB）", "網站、廣告投放", "其他"]
    },
    "Q3": {
        "text": "🎯 Q3. 你希望客戶第一次看到品牌時感受到什麼？",
        "options": ["專業、有信任感", "溫暖、有故事性", "時尚、有創意", "其他"]
    },
    "Q4": {
        "text": "🎯 Q4. 如果現在要你選最需要的服務？",
        "options": ["網站形象建立", "品牌影像拍攝", "行銷與曝光策略", "全部都需要"]
    }
}

# 用戶暫存答案
user_answers = {}

# 計算結果
def calculate_result(answers):
    score = sum([int(a) for a in answers])
    if score <= 5:
        return "🌱 初階品牌", "建議從品牌網站 + 形象照開始"
    elif score <= 10:
        return "🌿 成長品牌", "建議強化曝光與故事感"
    else:
        return "🌳 穩定品牌", "建議整合行銷與活動合作"

# 回覆 LINE
def reply_line(reply_token, messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {"replyToken": reply_token, "messages": messages}
    requests.post(LINE_API, headers=headers, json=data)

# Webhook
@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    events = data.get("events", [])

    for event in events:
        if event.get("type") == "message" and event["message"]["type"] == "text":
            user_id = event["source"]["userId"]
            reply_token = event["replyToken"]
            user_msg = event["message"]["text"]

            # 啟動小遊戲
            if "品牌診斷小遊戲" in user_msg:
                user_answers[user_id] = {"step": 1, "answers": []}
                q = questions["Q1"]
                reply_line(reply_token, [{
                    "type":"text",
                    "text": q["text"],
                    "quickReply": {
                        "items":[{"type":"action","action":{"type":"message","label":opt,"text":opt}} for opt in q["options"]]
                    }
                }])
                continue

            # 處理答題
            if user_id in user_answers:
                step = user_answers[user_id]["step"]
                try:
                    ans_index = questions[f"Q{step}"]["options"].index(user_msg) + 1
                except ValueError:
                    ans_index = 0
                user_answers[user_id]["answers"].append(ans_index)
                step += 1
                user_answers[user_id]["step"] = step

                if step <= 4:
                    q = questions[f"Q{step}"]
                    reply_line(reply_token, [{
                        "type":"text",
                        "text": q["text"],
                        "quickReply": {
                            "items":[{"type":"action","action":{"type":"message","label":opt,"text":opt}} for opt in q["options"]]
                        }
                    }])
                else:
                    # 全部答完，計算結果
                    answers = user_answers[user_id]["answers"]
                    result_type, recommendation = calculate_result(answers)
                    reply_line(reply_token, [{
                        "type":"text",
                        "text": f"🎉 品牌診斷完成！\n\n結果: {result_type}\n建議: {recommendation}"
                    }])
                    # 清除暫存
                    del user_answers[user_id]

    return "OK", 200

# 測試根目錄
@app.route("/")
def index():
    return "Flask app is running", 200

if __name__ == "__main__":
    app.run(debug=True)
