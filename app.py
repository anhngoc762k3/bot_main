import json
from flask import Flask, request, jsonify
from g4f.client import Client
import pdfplumber
import re

client = Client()
app = Flask(__name__)

# Đọc PDF khi khởi động
def read_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print("Lỗi đọc file PDF:", e)
        return ""

pdf_text = read_pdf("t2.pdf")

# Đọc links từ file JSON (theo cấu trúc mới có "bai_hoc": [{"keyword": ..., "link": ...}])
def load_links(json_path="data.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item["keyword"]: item["link"] for item in data.get("bai_hoc", [])}
    except Exception as e:
        print("Lỗi đọc file JSON:", e)
        return {}

extra_links = load_links()

# Tìm link bài học liên quan
def find_related_links(question):
    question = question.lower()
    links = []
    for keyword, link in extra_links.items():
        # So khớp chính xác từ khóa trong câu hỏi (tránh bị dính từ gần giống)
        if re.search(rf'\b{re.escape(keyword.lower())}\b', question):
            links.append(f'<a href="{link}" target="_blank">{keyword.title()}</a>')
    if links:
        return "<br><br><strong>🔗 Link bài học liên quan:</strong><br>" + "<br>".join(links)
    return ""

@app.route("/", methods=["GET"])
def home():
    return "✅ API đang chạy. Gửi POST đến /ask với câu hỏi."

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "Thiếu câu hỏi"}), 400

        # Gợi ý thêm link bài học
        link_html = find_related_links(question)

        # Chuẩn bị ngữ cảnh và prompt
        context = pdf_text[:6000]  # Giới hạn ký tự
        prompt = f"Đây là một đoạn văn từ tài liệu:\n{context}\n\nCâu hỏi: {question}\nTrả lời:"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        answer = response.choices[0].message.content
        final_answer = answer.replace("\n", "<br>") + link_html

        return jsonify({"answer": final_answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
