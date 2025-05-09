import asyncio
from asyncio import WindowsSelectorEventLoopPolicy
from flask import Flask, request, jsonify
from g4f.client import Client
import pdfplumber

# Cho Windows (bỏ qua nếu không dùng local Windows)
try:
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
except:
    pass

client = Client()
app = Flask(__name__)

# Đọc nội dung PDF ngay khi server khởi động
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

# API trả lời câu hỏi từ PDF
@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "Thiếu câu hỏi"}), 400

        context = pdf_text[:6000] if len(pdf_text) > 6000 else pdf_text
        prompt = f"Đây là một đoạn văn từ tài liệu: {context}\n\nCâu hỏi: {question}\nTrả lời:"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        answer = response.choices[0].message.content
        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
