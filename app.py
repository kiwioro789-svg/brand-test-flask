from flask import Flask, request, jsonify

app = Flask(__name__)

# 權重矩陣
weights = {
    "Q1": {"A":[3,1,0,0], "B":[1,3,1,0], "C":[0,1,3,1], "D":[0,1,1,3]},
    "Q2": {"A":[2,1,1,0], "B":[1,3,1,0], "C":[1,1,3,1], "D":[3,1,0,1]},
    "Q3": {"A":[2,1,2,0], "B":[1,3,1,0], "C":[0,1,3,1], "D":[0,1,1,3]},
    "Q4": {"A":[3,1,0,0], "B":[0,3,1,1], "C":[0,1,3,1], "D":[1,2,2,3]}
}

results = ["🌱 初階品牌", "🌿 成長品牌", "🌳 穩定品牌", "🌼 全面品牌"]

@app.route("/brand-test", methods=["POST"])
def brand_test():
    data = request.json
    # data = {"Q1":"A","Q2":"B","Q3":"B","Q4":"D"}
    
    scores = [0,0,0,0]
    for q, ans in data.items():
        w = weights.get(q, {}).get(ans)
        if w:
            scores = [s + w_i for s, w_i in zip(scores, w)]
    
    max_score = max(scores)
    top_indices = [i for i, s in enumerate(scores) if s == max_score]
    
    # 若多個平手，選最後一題的選項權重優先
    if len(top_indices) > 1:
        last_q = "Q4"
        last_ans = data[last_q]
        w_last = weights[last_q][last_ans]
        top_indices = [i for i in top_indices if w_last[i]==max(w_last[i] for i in top_indices)]
    
    result_index = top_indices[0]
    
    return jsonify({
        "result_type": results[result_index],
        "scores": scores,
        "recommendation": f"建議服務對應 {results[result_index]}"
    })

if __name__ == "__main__":
    app.run(debug=True)
