import sqlite3
import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# --- 설정 구간 ---
# 여기에 본인의 OpenAI API 키를 입력하세요.
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")
DB_PATH = 'ma_database.db'
# ----------------

def init_db():
    """데이터베이스 및 테이블 초기화"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ma_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def summarize_with_gpt(article_text):
    """GPT를 사용하여 기사 전문을 한 줄로 요약"""
    prompt = f"""
    아래 뉴스 기사 내용을 바탕으로 M&A 정보를 한 줄로 요약해줘.
    결과값은 반드시 아래의 형식을 정확히 지켜줘:
    "YYYY년 MM월 DD일", "인수자", "피인수자 또는 분야"에 대한 "상태(인수 관심/검토/완료 등)", 출처 "신문사이름"

    기사 내용:
    {article_text}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"GPT Error: {e}")
        return None

@app.route('/')
def index():
    """메인 페이지: 저장된 리스트 노출"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT summary FROM ma_records ORDER BY id DESC')
        records = [row[0] for row in cursor.fetchall()]
    return render_template('index.html', records=records)

@app.route('/summarize', methods=['POST'])
def summarize():
    """기사 접수 및 요약 저장 API"""
    data = request.json
    raw_text = data.get('text')
    
    summary = summarize_with_gpt(raw_text)
    
    if summary:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO ma_records (summary) VALUES (?)', (summary,))
            conn.commit()
        return jsonify({"summary": summary})
    else:
        return jsonify({"error": "요약 실패"}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)