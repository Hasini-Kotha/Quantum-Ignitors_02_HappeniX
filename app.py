from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, send
import sqlite3
import smtplib
from email.mime.text import MIMEText
import re
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")  # Path to your Firebase service account key
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://event-management-904df-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure secret key
socketio = SocketIO(app)

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participants
                 (id INTEGER PRIMARY KEY, name TEXT, email TEXT, workshop_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS workshops
                 (id INTEGER PRIMARY KEY, title TEXT, description TEXT, date TEXT, type TEXT, conductor_id INTEGER, timing TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY, workshop_id INTEGER, participant_email TEXT, rating INTEGER, comments TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS conductors
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    
    # Insert sample conductors (if they don't already exist)
    c.execute("SELECT COUNT(*) FROM conductors")
    if c.fetchone()[0] == 0:
        conductors = [
            ("conductor1", generate_password_hash("password1")),
            ("conductor2", generate_password_hash("password2"))
        ]
        c.executemany("INSERT INTO conductors (username, password) VALUES (?, ?)", conductors)
    
    # Insert sample workshops (if they don't already exist)
    c.execute("SELECT COUNT(*) FROM workshops")
    if c.fetchone()[0] == 0:
        # Get tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Education workshops
        education_workshops = [
            ("Python Programming", "Learn Python from scratch", tomorrow, "education", 1, "10:00 AM - 12:00 PM"),
            ("Web Development", "Build modern websites", tomorrow, "education", 1, "2:00 PM - 4:00 PM"),
            ("Data Science", "Introduction to Data Science", tomorrow, "education", 1, "11:00 AM - 1:00 PM"),
            ("Machine Learning", "Basics of Machine Learning", tomorrow, "education", 1, "3:00 PM - 5:00 PM"),
            ("AI Fundamentals", "Introduction to Artificial Intelligence", tomorrow, "education", 1, "9:00 AM - 11:00 AM")
        ]
        
        # Office workshops
        office_workshops = [
            ("Office Productivity", "Master Microsoft Office", tomorrow, "office", 2, "3:00 PM - 5:00 PM"),
            ("Excel Advanced", "Advanced Excel techniques", tomorrow, "office", 2, "10:00 AM - 12:00 PM"),
            ("PowerPoint Mastery", "Create stunning presentations", tomorrow, "office", 2, "1:00 PM - 3:00 PM"),
            ("Time Management", "Boost productivity with time management", tomorrow, "office", 2, "4:00 PM - 6:00 PM"),
            ("Communication Skills", "Effective communication in the workplace", tomorrow, "office", 2, "9:00 AM - 11:00 AM")
        ]
        
        c.executemany("INSERT INTO workshops (title, description, date, type, conductor_id, timing) VALUES (?, ?, ?, ?, ?, ?)", education_workshops + office_workshops)
    
    conn.commit()
    conn.close()

init_db()

# Email validation
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    return re.match(regex, email)

# Email setup
def send_email(to_email, subject, body):
    sender_email = "your_email@gmail.com"  # Replace with your Gmail
    sender_password = "your_email_password"  # Replace with your Gmail password (Less Secure Apps must be enabled)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, sender_password)  # Log in to Gmail
            server.sendmail(sender_email, to_email, msg.as_string())  # Send the email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
        raise

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/education')
def education():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM workshops WHERE type = 'education'")
    workshops = c.fetchall()
    conn.close()
    return render_template('education.html', workshops=workshops)

@app.route('/office')
def office():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM workshops WHERE type = 'office'")
    workshops = c.fetchall()
    conn.close()
    return render_template('office.html', workshops=workshops)

@app.route('/register/<int:workshop_id>', methods=['GET', 'POST'])
def register(workshop_id):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Validate email
        if not is_valid_email(email):
            flash("Please enter a valid Gmail address.")
            return redirect(url_for('register', workshop_id=workshop_id))

        # Check for duplicate registration
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM participants WHERE email = ? AND workshop_id = ?", (email, workshop_id))
        if c.fetchone():
            flash("This email is already registered for the workshop.")
            conn.close()
            return redirect(url_for('register', workshop_id=workshop_id))

        # Register the participant
        c.execute("INSERT INTO participants (name, email, workshop_id) VALUES (?, ?, ?)",
                  (name, email, workshop_id))
        conn.commit()
        conn.close()

        # Store registration details in Firebase
        ref = db.reference(f'workshops/{workshop_id}/participants')
        ref.push({
            'name': name,
            'email': email
        })

        # Send confirmation email
        try:
            send_email(email, "Workshop Registration Confirmation",
                       f"Hi {name}, you have successfully registered for the workshop!")
            flash("Registration successful! Check your email for confirmation.")
        except Exception as e:
            flash("Registration successful, but the confirmation email could not be sent. Please contact support.")

        return redirect(url_for('index'))

    return render_template('register.html', workshop_id=workshop_id)

@app.route('/workshop/<int:workshop_id>')
def workshop(workshop_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM workshops WHERE id = ?", (workshop_id,))
    workshop = c.fetchone()
    conn.close()

    if not workshop:
        flash("Workshop not found.")
        return redirect(url_for('index'))

    return render_template('workshop.html', workshop=workshop)

@app.route('/feedback/<int:workshop_id>', methods=['GET', 'POST'])
def feedback(workshop_id):
    if request.method == 'POST':
        email = request.form['email']
        rating = request.form['rating']
        comments = request.form['comments']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO feedback (workshop_id, participant_email, rating, comments) VALUES (?, ?, ?, ?)",
                  (workshop_id, email, rating, comments))
        conn.commit()
        conn.close()

        flash("Thank you for your feedback!")
        return redirect(url_for('index'))

    return render_template('feedback.html', workshop_id=workshop_id)

# Conductor Login
@app.route('/conductor/login', methods=['GET', 'POST'])
def conductor_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM conductors WHERE username = ?", (username,))
        conductor = c.fetchone()
        conn.close()

        if conductor and check_password_hash(conductor[2], password):
            session['conductor_id'] = conductor[0]  # Store conductor ID in session
            session['conductor_username'] = conductor[1]  # Store conductor username in session
            flash("Login successful!")
            return redirect(url_for('conductor_dashboard'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('conductor_login'))

    return render_template('conductor_login.html')

@app.route('/conductor/dashboard')
def conductor_dashboard():
    if 'conductor_id' not in session:
        flash("Please log in to access the dashboard.")
        return redirect(url_for('conductor_login'))

    conductor_id = session['conductor_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Fetch workshops conducted by the logged-in conductor
    c.execute("SELECT * FROM workshops WHERE conductor_id = ?", (conductor_id,))
    workshops = c.fetchall()

    # Fetch participants for each workshop from Firebase
    workshop_participants = {}
    for workshop in workshops:
        ref = db.reference(f'workshops/{workshop[0]}/participants')
        participants = ref.get()
        if participants:
            workshop_participants[workshop[0]] = [participant for participant in participants.values()]
        else:
            workshop_participants[workshop[0]] = []

    conn.close()
    return render_template('conductor_dashboard.html', workshops=workshops, workshop_participants=workshop_participants)

@app.route('/conductor/logout')
def conductor_logout():
    session.pop('conductor_id', None)
    session.pop('conductor_username', None)
    flash("You have been logged out.")
    return redirect(url_for('index'))

# Real-time Q&A and Polls
@socketio.on('message')
def handle_message(msg):
    send(msg, broadcast=True)

@socketio.on('poll_vote')
def handle_poll_vote(data):
    send(data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
