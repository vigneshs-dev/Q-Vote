from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Create a database connection
def get_db_connection():
    conn = sqlite3.connect('votes.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate INTEGER NOT NULL)''')
    conn.commit()
    conn.close()

create_tables()

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already taken. Please try a different one."
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('vote'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

# Voting page
@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        candidate = request.form['candidate']  # Get the selected candidate from the form

        # Insert the vote into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO votes (candidate) VALUES (?)', (candidate,))
        conn.commit()
        conn.close()

        # After vote submission, redirect to results page
        return redirect(url_for('results'))

    return render_template('vote.html')

# Results page to show current vote counts and winner
@app.route('/results')
def results():
    conn = get_db_connection()

    # Get the total votes for each candidate
    vote_counts = conn.execute('SELECT candidate, COUNT(*) as count FROM votes GROUP BY candidate').fetchall()

    conn.close()

    # Find the candidate(s) with the highest vote count
    if vote_counts:
        max_votes = max([row['count'] for row in vote_counts])
        winners = [row['candidate'] for row in vote_counts if row['count'] == max_votes]
    else:
        max_votes = 0
        winners = []

    return render_template('results.html', vote_counts=vote_counts, winners=winners, max_votes=max_votes)

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
