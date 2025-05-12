from flask import Flask, request, jsonify
from g4f.client import Client
import pdfplumber
import json
import os

app = Flask(__name__)
client = Client()

# Đọc file JSON bài học
def load_lessons():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

lessons_data = load_lessons()

# Đọc nội dung PDF
def read_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

pdf_text = read_pdf("t2.pdf")

# Tìm link từ JSON nếu có liên quan
def search_lesson_link(question):
    for lesson in lessons_data:
        if lesson["tieu_de"].lower() in question.lower():
            return {
                "title": lesson["tieu_de"],
                "bai_giang": lesson["link_bai_giang"],
                "bai_tap": lesson["link_bai_tap"]
            }
    return None

# Chatbot trả lời
def generate_response(question, pdf_text):
    try:
        context = pdf_text[:6000] if len(pdf_text) > 6000 else pdf_text
        prompt = f"Đây là một đoạn văn từ tài liệu: {context}\n\nCâu hỏi: {question}\nTrả lời:"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Đã xảy ra lỗi: {str(e)}"

# API endpoint
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "Không có câu hỏi."}), 400

    # Kiểm tra nếu câu hỏi có liên quan tới bài học
    matched = search_lesson_link(question)
    if matched:
        return jsonify({
            "answer": f"Đây là bài học về *{matched['title']}*. Bạn có thể xem tại:\n"
                      f"- 📘 [Bài giảng]({matched['bai_giang']})\n"
                      f"- ✏️ [Bài tập]({matched['bai_tap']})"
        })

    # Nếu không liên quan, dùng AI để trả lời
    answer = generate_response(question, pdf_text)
    return jsonify({"answer": answer})

# Chạy server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
