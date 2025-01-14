from flask import Flask, render_template, request, jsonify
import sqlite3
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch

app = Flask(__name__)

# اتصال به دیتابیس
DB_PATH = "C:/Users/Lenovo/Desktop/toska_full_menu_database.sql"

# مدل ALBERT برای پاسخ‌دهی
MODEL_NAME = "albert-base-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForQuestionAnswering.from_pretrained(MODEL_NAME)

# دیتای نمونه برای پردازش توسط مدل (می‌توانید تغییر دهید)
CONTEXT = "رستوران ما بهترین غذاهای ایرانی و بین‌المللی را ارائه می‌دهد. منوی ما شامل پیتزا، سالاد، سوپ و انواع دسرها می‌باشد."

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# مقداردهی اولیه دیتابیس
init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["userInput"]
        response = handle_user_input(user_input)
        return render_template("index.html", response=response)
    return render_template("index.html", response="لطفاً سوالات خود را درباره غذاهای رستوران بپرسید.")

@app.route("/api/menu", methods=["GET"])
def api_get_menu():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description FROM menu_items")
    menu_items = cursor.fetchall()
    conn.close()

    menu_list = [
        {"name": item[0], "price": item[1], "description": item[2]} for item in menu_items
    ]
    return jsonify(menu_list)

@app.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get("query", "")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, description FROM menu_items WHERE name LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()

    search_results = [
        {"name": item[0], "price": item[1], "description": item[2]} for item in results
    ]
    return jsonify(search_results)

def handle_user_input(user_input):
    if "منو" in user_input or "غذا" in user_input:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, description FROM menu_items")
        menu_items = cursor.fetchall()
        conn.close()

        menu_list = "".join([f"<li>{item[0]}: {item[1]} تومان - {item[2]}</li>" for item in menu_items])
        return f"<h2>منوی رستوران:</h2><ul>{menu_list}</ul>"

    # استفاده از مدل ALBERT برای پاسخ‌دهی به سوالات
    inputs = tokenizer.encode_plus(user_input, CONTEXT, return_tensors="pt")
    outputs = model(**inputs)
    start_scores = outputs.start_logits
    end_scores = outputs.end_logits

    start_index = torch.argmax(start_scores)
    end_index = torch.argmax(end_scores) + 1

    answer = tokenizer.decode(inputs['input_ids'][0][start_index:end_index])
    return f"<p>{answer}</p>"

if __name__ == "__main__":
    app.run(debug=True)

# HTML Template (index.html)
# Save this as a separate file in a "templates" folder
"""
<!DOCTYPE html>
<html lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>رستوران هوشمند</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="chat-container">
        <div class="chat-box">
            <div class="chat-header">
                <h2>چت با رستوران هوشمند</h2>
            </div>
            <div class="chat-messages">
                {{ response|safe }}
            </div>
            <div class="chat-input-container">
                <form method="POST" action="/">
                    <input type="text" name="userInput" placeholder="پرسش خود را وارد کنید...">
                    <button type="submit">ارسال</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

# CSS Template (style.css)
# Save this as a separate file in a "static" folder
"""
@font-face {
    font-family:'iransans';
    src: url('iransans.ttf');
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'iransans', sans-serif;
}

body {
    font-family: 'iransans', sans-serif;
    background-color: #f0f2f5;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 90vh;
}

.chat-container {
    width: 90%;
    min-width: 300px;
    max-width: 480px;
    height: 80vh;
    background-color: #fff;
    border-radius: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.chat-box {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.chat-header {
    background-color: #4f4ffa;
    color: white;
    padding: 15px;
    text-align: center;
}

.chat-messages {
    padding: 10px;
    flex-grow: 1;
    overflow-y: auto;
    background-color: #f9f9f9;
    border-bottom: 1px solid #ddd;
    direction: rtl;
}

.message {
    max-width: 75%;
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 10px;
    font-size: 14px;
}

.user-message {
    background-color: #4f4ffa;
    color: white;
    margin-left: auto;
    border-bottom-right-radius: 0;
}

.bot-message {
    background-color: #e0e0e0;
    color: #333;
    margin-right: auto;
    border-bottom-left-radius: 0;
}

.chat-input-container {
    direction: rtl;
    display: flex;
    padding: 10px;
    background-color: #fff;
    border-top: 1px solid #ddd;
}

.chat-input-container input {
    flex-grow: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 25px;
    font-size: 14px;
    outline: none;
}

.chat-input-container input:focus {
    border-color: #4f4ffa;
}

.chat-input-container button {
    background-color: #4f4ffa;
    color: white;
    padding: 10px 15px;
    margin-right: 10px;
    border: none;
    border-radius: 15px;
    cursor: pointer;
}

.chat-input-container button:hover {
    background-color: #45a049;
}
"""
