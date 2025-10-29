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

# 六題小遊戲題目
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

# 對應品牌類型
brand_types = [
    ("🌱 創造型品牌", "你充滿熱情與想法，品牌剛萌芽。建議聚焦於品牌定位與清晰視覺形象，讓世界看到你的創意！"),
    ("🌿 故事型品牌", "你重視情感與連結，品牌有故事與溫度。建議用影像與社群內容，建立品牌的真實感與人味。"),
    ("🌳 風格型品牌", "你擁有明確的設計感與一致的風格。接下來可以透過網站與形象影片，提升專業與辨識度。"),
    ("🌺 領導型品牌", "你的品牌成熟且有影響力。建議整合行銷策略，打造品牌聯名與高階市場價值。")
]

# 暫存使用者答案
user_answers = {}

# 分數計算（每題 1~4 分）
def calculate_result(answers):
    score = sum([int(a) for a in answers])  # 最大 24 分
    if score <= 6:
        return brand_types[0]
    elif score <= 12:
        return brand_types[1]
    elif score <= 18:
        return brand_types[2]
    else:
        return brand_types[3]

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
            user_msg = event["message"]["text"].strip()

            # 啟動遊戲
            if "品牌診斷小遊戲" in user_msg or user_msg == "再玩一次":
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
                    ans_index = 0  # 不在選項內
                user_answers[user_id]["answers"].append(ans_index)
                step += 1
                user_answers[user_id]["step"] = step

                if step <= 6:
                    q = questions[f"Q{step}"]
                    reply_line(reply_token, [{
                        "type":"text",
                        "text": q["text"],
                        "quickReply": {
                            "items":[{"type":"action","action":{"type":"message","label":opt,"text":opt}} for opt in q["options"]]
                        }
                    }])
                else:
                    result_title, result_text = calculate_result(user_answers[user_id]["answers"])
                    reply_line(reply_token, [
                        {
                            "type":"text",
                            "text": f"🎉 品牌診斷完成！\n\n結果: {result_title}\n建議: {result_text}"
                        },
                        {
                            "type":"text",
                            "text": "想要再玩一次嗎？",
                            "quickReply": {
                                "items":[{"type":"action","action":{"type":"message","label":"再玩一次","text":"再玩一次"}}]
                            }
                        }
                    ])
                    del user_answers[user_id]

    return "OK", 200

@app.route("/")
def index():
    return "Flask app is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
