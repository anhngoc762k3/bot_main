import asyncio
import platform
import json
from flask import Flask, request, jsonify
from g4f.client import Client
import pdfplumber

# Chỉ import nếu chạy Windows
if platform.system() == "Windows":
    try:
        from asyncio import WindowsSelectorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    except ImportError:
        pass

client = Client()
app = Flask(__name__)

# Đọc PDF khi khởi động
pdf_file_path = 'MTvE.pdf'
def read_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

pdf_text = read_pdf(pdf_file_path)

# Đọc links từ file JSON
def load_links(json_path="data.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Lỗi đọc file JSON:", e)
        return {}

extra_links = load_links()

# Tìm link bài học liên quan
def find_related_links(question):
    links = []
    for keyword, link in extra_links.items():
        if keyword.lower() in question.lower():
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

        # Trích xuất link bài học liên quan
        link_html = find_related_links(question)

        # Chuẩn bị ngữ cảnh và prompt
        context = pdf_text[:6000] if len(pdf_text) > 6000 else pdf_text
        prompt = f"Đây là một đoạn văn từ tài liệu: {context}\n\nCâu hỏi: {question}\nTrả lời:"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        answer = response.choices[0].message.content
        final_answer = answer.replace("\n", "<br>") + link_html  # HTML định dạng và chèn link

        return jsonify({"answer": final_answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
