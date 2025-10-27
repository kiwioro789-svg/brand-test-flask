from flask import Flask, request, jsonify

app = Flask(__name__)

# 4題選項
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

# 用戶答案暫存 (demo用, 多用戶可改DB)
user_answers = {}

# 計算結果
def calculate_result(answers):
    try:
        score = sum([int(a) for a in answers])
    except:
        score = 0
    if score <= 5:
        return "🌱 初階品牌", "建議從品牌網站 + 形象照開始"
    elif score <= 10:
        return "🌿 成長品牌", "建議強化曝光與故事感"
    else:
        return "🌳 穩定品牌", "建議整合行銷與活動合作"

# 根路徑測試
@app.route("/")
def index():
    return "Flask app is running", 200

# LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    if not data:
        return "No data", 200

    events = data.get("events", [])
    replies = []

    for event in events:
        if event.get("type") == "message" and event["message"]["type"] == "text":
            user_id = event["source"]["userId"]
            user_msg = event["message"]["text"]

            # 啟動小遊戲
            if "品牌診斷小遊戲" in user_msg:
                user_answers[user_id] = {"step": 1, "answers": []}
                q = questions["Q1"]
                replies.append({
                    "type": "text",
                    "text": q["text"],
                    "quickReply": {
                        "items": [{"type":"action","action":{"type":"message","label":opt,"text":opt}} for opt in q["options"]]
                    }
                })
            # 處理答題
            elif user_id in user_answers:
                step = user_answers[user_id]["step"]
                # 將文字轉成數字 1~4
                try:
                    answer_index = questions[f"Q{step}"]["options"].index(user_msg) + 1
                except:
                    answer_index = 0
                user_answers[user_id]["answers"].append(answer_index)
                step += 1
                user_answers[user_id]["step"] = step

                if step <= 4:
                    q = questions[f"Q{step}"]
                    replies.append({
                        "type": "text",
                        "text": q["text"],
                        "quickReply": {
                            "items": [{"type":"action","action":{"type":"message","label":opt,"text":opt}} for opt in q["options"]]
                        }
                    })
                else:
                    # 全部答完，計算結果
                    answers = user_answers[user_id]["answers"]
                    result_type, recommendation = calculate_result(answers)
                    replies.append({
                        "type": "text",
                        "text": f"🎉 品牌診斷完成！\n\n結果: {result_type}\n建議: {recommendation}"
                    })
                    # 清除暫存
                    del user_answers[user_id]

    return jsonify({"replies": replies}), 200

# API route 給 Postman / LIFF 呼叫
@app.route("/brand-test", methods=["POST"])
def brand_test():
    data = request.get_json()
    answers = [
        data.get("Q1", "0"),
        data.get("Q2", "0"),
        data.get("Q3", "0"),
        data.get("Q4", "0")
    ]
    # 避免 KeyError
    try:
        result_type, recommendation = calculate_result(answers)
    except:
        result_type, recommendation = "未知", "請確認答案格式"
    return jsonify({
        "result_type": result_type,
        "score": sum([int(a) if str(a).isdigit() else 0 for a in answers]),
        "recommendation": recommendation
    }), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
