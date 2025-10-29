from flask import Flask, request
import requests
import os
import json
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

app = Flask(__name__)

# LINE 設定
LINE_TOKEN = os.getenv("LINE_TOKEN")
LINE_API = "https://api.line.me/v2/bot/message/reply"

# 小遊戲題目與 QuickReply 選項
questions = {
    "Q1": {
        "text": "💭 Q1. 如果你的品牌是一個人，他會是：",
        "options": [
            "剛畢業的新鮮人，充滿熱血",
            "熱愛社交的創意人",
            "冷靜理性的專業人士",
            "成熟穩重、有魅力的領導者"
        ]
    },
    "Q2": {
        "text": "🎨 Q2. 你的品牌色系更接近哪一種？",
        "options": [
            "柔和白灰，乾淨簡約",
            "暖橘粉，溫暖有故事",
            "高飽和色，創意滿滿",
            "黑金配色，質感高端"
        ]
    },
    "Q3": {
        "text": "🚀 Q3. 當你在經營品牌時，最享受的瞬間是？",
        "options": [
            "客人第一次認識品牌",
            "設計或拍攝時的創作過程",
            "收到正面回饋",
            "看見品牌越來越有影響力"
        ]
    },
    "Q4": {
        "text": "💬 Q4. 若品牌有一句 slogan，你會選哪種語氣？",
        "options": [
            "一步一腳印，從零開始",
            "用故事溫暖市場",
            "做自己風格的主角",
            "讓專業說話"
        ]
    },
    "Q5": {
        "text": "✨ Q5. 你的品牌最需要的超能力是？",
        "options": [
            "讓人一眼記住的視覺感",
            "感動人心的內容力",
            "自動吸引客戶的行銷力",
            "穩定發展的策略力"
        ]
    },
    "Q6": {
        "text": "🗺️ Q6. 如果品牌是一場旅程，現在你覺得自己在哪？",
        "options": [
            "剛整理行李，準備出發",
            "走在途中，開始有風景",
            "已達到第一個目的地",
            "正在規劃下一趟旅程"
        ]
    }
}


# 暫存使用者答案
user_answers = {}

def calculate_result(answers):
    score = sum(answers)
    if score <= 6:
        return "🌱 創造型品牌", "你充滿熱情與想法，建議先集中火力打造清楚的品牌故事與視覺風格！"
    elif score <= 10:
        return "🌿 故事型品牌", "你重視情感與連結，可以用影像與內容行銷，強化品牌溫度。"
    elif score <= 15:
        return "🌳 風格型品牌", "你的品牌有明確個性，建議投入網站與行銷，打造一致性形象。"
    else:
        return "🌺 領導型品牌", "你已是成熟品牌，下一步可以朝品牌合作與跨界策略前進！"


def reply_line(reply_token, messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {"replyToken": reply_token, "messages": messages}
    res = requests.post(LINE_API, headers=headers, json=data)
    print("Reply status:", res.status_code, res.text)

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    print("=== LINE Webhook Triggered ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    events = data.get("events", [])
    for event in events:
        if event.get("type") == "message" and event["message"]["type"] == "text":
            user_id = event["source"]["userId"]
            reply_token = event["replyToken"]
            user_msg = event["message"]["text"]

            # 啟動遊戲
            if "品牌診斷小遊戲" in user_msg.strip():
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

            # 回答處理
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
                    result_type, recommendation = calculate_result(user_answers[user_id]["answers"])
                    reply_line(reply_token, [{
                        "type":"text",
                        "text": f"🎉 品牌診斷完成！\n\n結果: {result_type}\n建議: {recommendation}"
                    }])
                    del user_answers[user_id]

    return "OK", 200

@app.route("/")
def index():
    return "Flask app is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
