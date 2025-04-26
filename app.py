import sqlite3
import bcrypt
import smtplib
from email.mime.text import MIMEText
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "mysecretkey123"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
SENDER_EMAIL = "sayedahemmad1@gmail.com"
SENDER_PASSWORD = "sanv zszk msmu aggt"

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            voter_id TEXT PRIMARY KEY,
            name TEXT,
            address TEXT,
            District TEXT,
            email TEXT,
            password TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            voter_id TEXT,
            candidate TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES users (voter_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id TEXT PRIMARY KEY,
            name TEXT,
            party TEXT,
            District TEXT,
            agenda TEXT,
            photo TEXT
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    init_db()
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    districts = get_unique_districts()
    print(f"Passing to template: {districts}")  # Debug line
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        name = request.form['name']
        address = request.form['address']
        District = request.form['District']
        email = request.form['email']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        conn = get_db_connection()
        if conn.execute('SELECT * FROM users WHERE voter_id = ?', (voter_id,)).fetchone():
            conn.close()
            return render_template('register.html', message="Voter ID already registered!")
        conn.execute('INSERT INTO users (voter_id, name, address, District, email, password) VALUES (?, ?, ?, ?, ?, ?)', 
                     (voter_id, name, address, District, email, password))
        conn.commit()
        conn.close()
        
        msg = MIMEText(f"Welcome to Odisha Voting, {name}! Your Voter ID is {voter_id}.")
        msg['Subject'] = "Welcome to Odisha Online Voting"
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

        return redirect(url_for('login'))
    return render_template('register.html', districts=districts)

@app.route('/candidate_register', methods=['GET', 'POST'])
def candidate_register():
    districts = get_unique_districts()
    if request.method == 'POST':
        candidate_id = request.form['candidate_id']
        name = request.form['name']
        party = request.form['party']
        District = request.form['District']
        agenda = request.form['agenda']
        conn = get_db_connection()
        existing_candidate = conn.execute('SELECT * FROM candidates WHERE candidate_id = ?', 
                                        (candidate_id,)).fetchone()
        if existing_candidate:
            conn.close()
            return render_template('candidate_register.html', message="Candidate ID already registered!")
        conn.execute('INSERT INTO candidates (candidate_id, name, party, District, agenda) VALUES (?, ?, ?, ?, ?)', 
                    (candidate_id, name, party, District, agenda))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('candidate_register.html', districts=districts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        password = request.form['password'].encode('utf-8')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE voter_id = ?', 
                            (voter_id,)).fetchone()
        conn.close()
        if user and bcrypt.checkpw(password, user['password']):
            session['voter_id'] = voter_id
            return redirect(url_for('vote'))
        return render_template('login.html', message="Invalid credentials.")
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'voter_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE voter_id = ?', (session['voter_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'voter_id' not in session:
        return redirect(url_for('login'))
    message = None
    conn = get_db_connection()
    voted = conn.execute('SELECT * FROM votes WHERE voter_id = ?', 
                         (session['voter_id'],)).fetchone()
    user = conn.execute('SELECT District, email, name FROM users WHERE voter_id = ?', 
                        (session['voter_id'],)).fetchone()
    District = user['District'] if user else None
    candidates = conn.execute("SELECT * FROM candidates WHERE District = ?", (District,)).fetchall()
    if request.method == 'POST' and not voted:
        candidate = request.form['candidate']
        conn.execute('INSERT INTO votes (voter_id, candidate) VALUES (?, ?)', 
                     (session['voter_id'], candidate))
        conn.commit()
        print(f"Vote saved: voter_id={session['voter_id']}, candidate={candidate}")
        message = f"You voted for {candidate}, Voter {session['voter_id']}!"
        
        msg = MIMEText(f"Dear {user['name']}, your vote for {candidate} has been recorded on {datetime.datetime.now()}.")
        msg['Subject'] = "Vote Confirmation - Odisha Voting"
        msg['From'] = SENDER_EMAIL
        msg['To'] = user['email']
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

    conn.close()
    return render_template('vote.html', message=message, voted=voted, candidates=candidates)

@app.route('/logout')
def logout():
    session.pop('voter_id', None)
    return redirect(url_for('login'))

@app.route('/results', methods=['GET'])
def results():
    conn = get_db_connection()
    search_query = request.args.get('search', '')
    if search_query:
        candidates = conn.execute("SELECT name, District FROM candidates WHERE name LIKE ? OR District LIKE ?", 
                                 (f'%{search_query}%', f'%{search_query}%')).fetchall()
        results = conn.execute("""
            SELECT c.District, c.name AS candidate, COUNT(v.candidate) AS vote_count
            FROM candidates c
            LEFT JOIN votes v ON c.name = v.candidate
            WHERE c.name LIKE ? OR c.District LIKE ?
            GROUP BY c.District, c.name
        """, (f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        candidates = conn.execute("SELECT name, District FROM candidates").fetchall()
        results = conn.execute("""
            SELECT c.District, c.name AS candidate, COUNT(v.candidate) AS vote_count
            FROM candidates c
            LEFT JOIN votes v ON c.name = v.candidate
            GROUP BY c.District, c.name
        """).fetchall()
    print(f"Results fetched: {results}")
    conn.close()
    if not results:
        print("No results found!")
        return render_template('results.html', results=[], candidates=candidates, message="No votes yet!", search_query=search_query)
    return render_template('results.html', results=results, candidates=candidates, search_query=search_query)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', message="Invalid admin credentials.")
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    search_query = request.args.get('search', '')
    if search_query:
        voters = conn.execute("SELECT * FROM users WHERE voter_id LIKE ? OR name LIKE ?", 
                             (f'%{search_query}%', f'%{search_query}%')).fetchall()
        candidates = conn.execute("SELECT * FROM candidates WHERE candidate_id LIKE ? OR name LIKE ?", 
                                 (f'%{search_query}%', f'%{search_query}%')).fetchall()
        votes = conn.execute("SELECT * FROM votes WHERE voter_id LIKE ? OR candidate LIKE ?", 
                            (f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        voters = conn.execute("SELECT * FROM users").fetchall()
        candidates = conn.execute("SELECT * FROM candidates").fetchall()
        votes = conn.execute("SELECT * FROM votes").fetchall()

    total_voters = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_votes = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    turnout = (total_votes / total_voters * 100) if total_voters > 0 else 0
    
    vote_stats = conn.execute("""
        SELECT c.District, c.name AS candidate, COUNT(v.candidate) AS vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.name = v.candidate
        GROUP BY c.District, c.name
        ORDER BY c.District, vote_count DESC
    """).fetchall()
    
    District_trends = conn.execute("""
        SELECT c.District, COUNT(v.candidate) AS vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.name = v.candidate
        GROUP BY c.District
    """).fetchall()

    conn.close()
    return render_template('admin.html', voters=voters, candidates=candidates, votes=votes, search_query=search_query, 
                          turnout=turnout, total_voters=total_voters, total_votes=total_votes,
                          vote_stats=vote_stats, District_trends=District_trends)

@app.route('/candidate_profile/<candidate_id>')
def candidate_profile(candidate_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE candidate_id = ?', (candidate_id,)).fetchone()
    conn.close()
    
    if candidate is None:
        flash('Candidate not found!')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('candidate_profile.html', candidate=candidate)

@app.route('/voter/candidate_profile/<candidate_id>')
def voter_candidate_profile(candidate_id):
    if 'voter_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE candidate_id = ?', (candidate_id,)).fetchone()
    conn.close()
    
    if candidate is None:
        flash('Candidate not found!')
        return redirect(url_for('home'))
    
    return render_template('voter_candidate_profile.html', candidate=candidate)

@app.route('/update_candidate/<candidate_id>', methods=['GET', 'POST'])
def update_candidate(candidate_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE candidate_id = ?', (candidate_id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        party = request.form['party']
        District = request.form['District']
        agenda = request.form['agenda']
        
        photo = request.files.get('photo')
        photo_path = candidate['photo']  # Keep old photo by default
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            try:
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_path = f'uploads/{filename}'
            except Exception as e:
                flash(f"Error uploading photo: {e}")
                conn.close()
                return render_template('update_candidate.html', candidate=candidate)
        elif 'remove_photo' in request.form:
            photo_path = None
        
        conn.execute('UPDATE candidates SET name = ?, party = ?, District = ?, agenda = ?, photo = ? WHERE candidate_id = ?',
                     (name, party, District, agenda, photo_path, candidate_id))
        conn.commit()
        conn.close()
        flash('Candidate profile updated successfully!')
        return redirect(url_for('candidate_profile', candidate_id=candidate_id))
    
    conn.close()
    return render_template('update_candidate.html', candidate=candidate)

@app.route('/admin/delete_voter/<voter_id>', methods=['POST'])
def delete_voter(voter_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM votes WHERE voter_id = ?", (voter_id,))
    conn.execute("DELETE FROM users WHERE voter_id = ?", (voter_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_candidate/<candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM votes WHERE candidate = (SELECT name FROM candidates WHERE candidate_id = ?)", (candidate_id,))
    conn.execute("DELETE FROM candidates WHERE candidate_id = ?", (candidate_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_vote/<voter_id>', methods=['POST'])
def delete_vote(voter_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM votes WHERE voter_id = ?", (voter_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_voter', methods=['GET', 'POST'])
def add_voter():
    districts = get_unique_districts()
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        voter_id = request.form['voter_id']
        name = request.form['name']
        address = request.form['address']
        District = request.form['District']
        email = request.form['email']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        conn = get_db_connection()
        if conn.execute('SELECT * FROM users WHERE voter_id = ?', (voter_id,)).fetchone():
            conn.close()
            return render_template('add_voter.html', message="Voter ID already exists!")
        conn.execute('INSERT INTO users (voter_id, name, address, District, email, password) VALUES (?, ?, ?, ?, ?, ?)', 
                     (voter_id, name, address, District, email, password))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_voter.html', districts=districts)

@app.route('/admin/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    districts = get_unique_districts()
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        candidate_id = request.form['candidate_id']
        name = request.form['name']
        party = request.form['party']
        District = request.form['District']
        agenda = request.form['agenda']
        conn = get_db_connection()
        if conn.execute('SELECT * FROM candidates WHERE candidate_id = ?', (candidate_id,)).fetchone():
            conn.close()
            return render_template('add_candidate.html', message="Candidate ID already exists!")
        conn.execute('INSERT INTO candidates (candidate_id, name, party, District, agenda) VALUES (?, ?, ?, ?, ?)', 
                     (candidate_id, name, party, District, agenda))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_candidate.html', districts=districts)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

def get_unique_districts():
    conn = sqlite3.connect('voting.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT District FROM candidates ORDER BY District')  # Changed to District
    districts = [row[0] for row in cursor.fetchall()]
    conn.close()
    print(f"Districts fetched: {districts}")  # Debug line
    return districts

@app.route('/admin_add_candidate', methods=['GET', 'POST'])
def admin_add_candidate():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        candidate_id = request.form['candidate_id']
        name = request.form['name']
        party = request.form['party']
        District = request.form['District']  # Fixed to match form field name
        agenda = request.form['agenda']
        conn = get_db_connection()
        if conn.execute('SELECT * FROM candidates WHERE candidate_id = ?', (candidate_id,)).fetchone():
            conn.close()
            return render_template('admin_add_candidate.html', message="Candidate ID already exists!")
        try:
            conn.execute('INSERT INTO candidates (candidate_id, name, party, District, agenda) VALUES (?, ?, ?, ?, ?)', 
                         (candidate_id, name, party, District, agenda))
            conn.commit()
            print(f"Inserted candidate: {candidate_id}, {name}, {party}, {District}, {agenda}")  # Debug
        except Exception as e:
            conn.close()
            return render_template('admin_add_candidate.html', message=f"Error: {str(e)}")
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_add_candidate.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))