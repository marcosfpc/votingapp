# Online Voting System for Athletes Commission (ECA)
# Using Python (Flask framework)

from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import csv
import io
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

TEMPLATES_DIR = 'templates'
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# --- Database Setup ---

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS voters (
                        id_number TEXT PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        country TEXT,
                        gender TEXT,
                        has_voted BOOLEAN DEFAULT 0
                    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS candidates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        votes INTEGER DEFAULT 0
                    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS admin (
                        username TEXT PRIMARY KEY,
                        password_hash TEXT
                    )''')
    # Create default admin
    username = 'be_cool'
    password_hash = generate_password_hash('shadowman')
    conn.execute('INSERT OR IGNORE INTO admin (username, password_hash) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()

def load_voters_from_excel(file_path):
    conn = get_db_connection()
    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        conn.execute('INSERT OR IGNORE INTO voters (id_number, first_name, last_name, country, gender) VALUES (?, ?, ?, ?, ?)',
                     (str(row['ID Number']), row['First Name'], row['Last Name'], row['Country'], row['Gender']))
    conn.commit()
    conn.close()

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        id_number = request.form['id_number']
        conn = get_db_connection()
        voter = conn.execute('SELECT * FROM voters WHERE id_number = ?', (id_number,)).fetchone()
        conn.close()
        if voter:
            if voter['has_voted']:
                return 'You have already voted!'
            session['voter_id'] = id_number
            return redirect(url_for('vote'))
        else:
            return 'Invalid ID number.'
    return render_template('home.html')

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'voter_id' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    candidates = conn.execute('SELECT * FROM candidates').fetchall()
    if request.method == 'POST':
        candidate_id = request.form['candidate']
        # Update vote count
        conn.execute('UPDATE candidates SET votes = votes + 1 WHERE id = ?', (candidate_id,))
        # Mark voter as voted
        conn.execute('UPDATE voters SET has_voted = 1 WHERE id_number = ?', (session['voter_id'],))
        conn.commit()
        conn.close()
        session.pop('voter_id', None)
        return 'Thank you for voting!'
    conn.close()
    return render_template('vote.html', candidates=candidates)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admin WHERE username = ?', (username,)).fetchone()
        conn.close()
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return 'Invalid login.'
    return render_template('admin_login.html')

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filepath = os.path.join('/tmp', file.filename)
            file.save(filepath)
            load_voters_from_excel(filepath)
            flash('Voters uploaded successfully')
            return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    candidates = conn.execute('SELECT * FROM candidates').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', candidates=candidates)

@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    name = request.form['name']
    conn = get_db_connection()
    conn.execute('INSERT INTO candidates (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/download_results')
def download_results():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    candidates = conn.execute('SELECT * FROM candidates').fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Candidate Name', 'Votes'])
    for candidate in candidates:
        writer.writerow([candidate['name'], candidate['votes']])
    output.seek(0)
    conn.close()
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='results.csv')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
