from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import bcrypt
import bleach
import os
from generate_key import generate_secret_key  # Assuming this is a custom module

# Initialize Flask app with templates folder
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "../html/templates"))
app.secret_key = generate_secret_key()  # Secure secret key (consider persisting it securely)
csrf = CSRFProtect(app)

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')  # Test connection
    db = client.notes_app
except PyMongoError as e:
    print(f"⚠️ Error connecting to MongoDB: {e}")
    db = None

# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Use HTTPS in production
    SESSION_COOKIE_HTTPONLY=True,  # Prevent JS access to cookies
    SESSION_COOKIE_SAMESITE='Lax',  # Mitigate CSRF
    PERMANENT_SESSION_LIFETIME=3600  # Session expires after 1 hour
)

def is_logged_in():
    return 'username' in session

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password', '').encode('utf-8')
        
        try:
            user = db.users.find_one({'username': username})
            if user and bcrypt.checkpw(password, user['password']):
                session['username'] = username
                session.permanent = True  # Make session persistent
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            flash('Invalid username or password', 'error')
        except PyMongoError as e:
            app.logger.error(f"❌ Login error: {e}")
            flash('Database error occurred', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password', '').encode('utf-8')
        
        try:
            if db.users.find_one({'username': username}):
                flash('Username already exists', 'error')
            else:
                hashed = bcrypt.hashpw(password, bcrypt.gensalt())
                db.users.insert_one({'username': username, 'password': hashed, 'role': 'user'})
                flash('Registration successful! Please login', 'success')
                return redirect(url_for('login'))
        except PyMongoError as e:
            app.logger.error(f"❌ Registration error: {e}")
            flash('Database error occurred', 'error')
    
    return render_template('register.html')

@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    try:
        admin_data = db.users.find_one({'role': 'admin'})
        notes = list(db.notes.find({'user': session['username']}))  # Show only user's notes
        return render_template('index.html', admin=admin_data, notes=notes)
    except PyMongoError as e:
        app.logger.error(f"❌ Home error: {e}")
        flash('Error loading data', 'error')
        return redirect(url_for('login'))

@app.route('/add_note', methods=['POST'])
def add_note():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    note_content = bleach.clean(request.form.get('note', ''))
    if note_content:
        try:
            db.notes.insert_one({"content": note_content, "user": session['username']})
            flash('Note added successfully', 'success')
        except PyMongoError as e:
            app.logger.error(f"❌ Add note error: {e}")
            flash('Error saving note', 'error')
    
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Debug mode should be False in production
    app.run(debug=os.getenv('FLASK_DEBUG', 'False') == 'True', host='0.0.0.0', port=5000)