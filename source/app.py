from flask import Flask, request, redirect, abort
import sqlite3
import string
import random
import os

app = Flask(__name__)

DATABASE = '/app/data/urls.db'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT 1 FROM urls WHERE short_code = ?', (code,))
        if not c.fetchone():
            conn.close()
            return code
        conn.close()

# Flag to track if database has been initialized
_initialized = False

@app.before_request
def initialize_database():
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True

@app.route('/', methods=['POST'])
def shorten():
    long_url = request.form.get('url') or request.json.get('url')
    if not long_url:
        return abort(400, 'URL is required')
    # Ensure URL has scheme
    if not long_url.startswith(('http://', 'https://')):
        long_url = 'http://' + long_url
    short_code = generate_short_code()
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO urls (long_url, short_code) VALUES (?, ?)', (long_url, short_code))
    conn.commit()
    conn.close()
    short_url = f'{BASE_URL}/{short_code}'
    return {'short_url': short_url, 'long_url': long_url, 'short_code': short_code}

@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT long_url FROM urls WHERE short_code = ?', (short_code,))
    row = c.fetchone()
    conn.close()
    if row:
        return redirect(row[0])
    else:
        abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)