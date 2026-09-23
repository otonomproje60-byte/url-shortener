from flask import Flask, request, redirect, abort, send_file
import sqlite3
import string
import random
import os
import time
from functools import wraps

app = Flask(__name__)

DATABASE = '/app/data/urls.db'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

# Rate limiting storage
rate_limit_store = {}
RATE_LIMIT = 10  # requests per minute per IP
RATE_LIMIT_WINDOW = 60  # seconds

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

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            client_ip = request.remote_addr
            current_time = time.time()
            
            if client_ip not in rate_limit_store:
                rate_limit_store[client_ip] = []
            
            # Clean old entries
            rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if current_time - t < RATE_LIMIT_WINDOW]
            
            if len(rate_limit_store[client_ip]) >= RATE_LIMIT:
                return abort(429, 'Rate limit exceeded. Max 10 requests per minute.')
            
            rate_limit_store[client_ip].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def index():
    return '''<!DOCTYPE html>
<html>
<head>
    <title>URL Shortener</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .form-group { margin-bottom: 15px; }
        input[type="url"] { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 12px 24px; font-size: 16px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; display: none; }
        .result a { color: #007bff; word-break: break-all; }
        .error { color: #dc3545; margin-top: 10px; display: none; }
    </style>
</head>
<body>
    <h1>URL Shortener</h1>
    <div class="form-group">
        <input type="url" id="longUrl" placeholder="Enter URL to shorten" required>
    </div>
    <button onclick="shortenUrl()">Shorten</button>
    <div class="error" id="error"></div>
    <div class="result" id="result">
        <strong>Short URL:</strong><br>
        <a id="shortUrl" href="#" target="_blank"></a>
    </div>
    <script>
        async function shortenUrl() {
            const url = document.getElementById('longUrl').value;
            const errorDiv = document.getElementById('error');
            const resultDiv = document.getElementById('result');
            const shortUrlLink = document.getElementById('shortUrl');
            errorDiv.style.display = 'none';
            resultDiv.style.display = 'none';
            if (!url) {
                errorDiv.textContent = 'Please enter a URL';
                errorDiv.style.display = 'block';
                return;
            }
            try {
                const response = await fetch('/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await response.json();
                if (response.ok) {
                    shortUrlLink.href = data.short_url;
                    shortUrlLink.textContent = data.short_url;
                    resultDiv.style.display = 'block';
                } else {
                    errorDiv.textContent = data.detail || 'Error shortening URL';
                    errorDiv.style.display = 'block';
                }
            } catch (e) {
                errorDiv.textContent = 'Network error: ' + e.message;
                errorDiv.style.display = 'block';
            }
        }
        document.getElementById('longUrl').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') shortenUrl();
        });
    </script>
</body>
</html>'''

# Flag to track if database has been initialized
_initialized = False

@app.before_request
def initialize_database():
    global _initialized
    if not _initialized:
        init_db()
        _initialized = True

@app.route('/', methods=['POST'])
@rate_limit
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

@app.route('/compare')
def comparison():
    return send_file('comparison.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)