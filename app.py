import asyncio
import sys
from g4f.client import Client
import pdfplumber

# Dữ liệu liên kết
lecture_links = {
    "Máy tính và em": {
        "Máy tính là gì?": {
            "link bài giảng": "https://example.com2/bai-giang-may-tinh",
            "link bài tập": "https://example.com4/bai-tap-may-tinh"
        }
    },
    "Tạo nội dung bằng máy tính": {
        "Phần mềm tô màu": {
            "link bài giảng": "https://example.com/toan-10",
            "link bài tập": "https://example.com/bai-tap-toan-10"
        }
    }
}

# Chỉ thiết lập WindowsSelectorEventLoopPolicy nếu đang chạy trên Windows
if sys.platform.startswith("win"):
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

# Khởi tạo client
client = Client()

# Đọc PDF
def read_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

# Tạo câu trả lời
def generate_response(question, pdf_text):
    try:
        context = pdf_text[:6000] if len(pdf_text) > 6000 else pdf_text
        prompt = (
            f"Đây là một đoạn văn từ tài liệu học thuật:\n\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            f"Trả lời chi tiết và nếu có thể, hãy đề xuất bài học liên quan.\n"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Đã xảy ra lỗi: {str(e)}"

# Gợi ý liên kết theo câu hỏi/tiêu đề
def suggest_lecture_links(question_or_answer):
    suggestions = []
    for topic, lessons in lecture_links.items():
        if topic.lower() in question_or_answer.lower():
            for title, links in lessons.items():
                suggestion = f"📘 **{title}**\n"
                for label, url in links.items():
                    suggestion += f"- {label}: {url}\n"
                suggestions.append(suggestion)
        else:
            for title, links in lessons.items():
                if title.lower() in question_or_answer.lower():
                    suggestion = f"📘 **{title}**\n"
                    for label, url in links.items():
                        suggestion += f"- {label}: {url}\n"
                    suggestions.append(suggestion)
    return suggestions

# Đọc PDF
pdf_file_path = 't2.pdf'
pdf_text = read_pdf(pdf_file_path)

# Giao diện dòng lệnh
if __name__ == "__main__":
    while True:
        question = input("Bạn: ")
        if question.lower() in ["exit", "quit"]:
            break
        answer = generate_response(question, pdf_text)
        print("\nChatbot:", answer)

        # Gợi ý liên kết
        suggested_links = suggest_lecture_links(question + " " + answer)
        if suggested_links:
            print("\n🔗 Các liên kết liên quan:")
            for s in suggested_links:
                print(s)
