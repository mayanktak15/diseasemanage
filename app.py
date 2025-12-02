import os
import csv
import requests
import ipaddress
import warnings
import logging

# Suppress NumPy warnings on Windows
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*MINGW-W64.*')
os.environ['PYTHONWARNINGS'] = 'ignore::RuntimeWarning'

# Ensure SQLite driver availability on runtimes lacking stdlib sqlite3
try:
    import sqlite3 as _sqlite3  # noqa: F401
except Exception:
    try:
        import pysqlite3 as sqlite3  # type: ignore
        import sys as _sys
        _sys.modules["sqlite3"] = sqlite3
    except Exception:
        pass

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

try:
    from evaluate_different_modules import process_query5,process_query2,process_query4,process_query,process_query3
    ADVANCED_MODULES_AVAILABLE = True
except ImportError as e:
    ADVANCED_MODULES_AVAILABLE = False
except Exception as e:
    ADVANCED_MODULES_AVAILABLE = False

# Import the simple FAQ responses as fallback (from existing helper module)
try:
    from evaluate_different_modules import get_simple_faq_response
    FAQ_AVAILABLE = True
except ImportError:
    print("Warning: Simple FAQ responses not available from evaluate_different_modules")
    FAQ_AVAILABLE = False

# Define safe stubs to satisfy linters and ensure symbols exist
if not ADVANCED_MODULES_AVAILABLE:
    def process_query5(query, symptoms=None):
        return None
    def process_query2(query, symptoms=None):
        return None
    def process_query4(query, symptoms=None):
        return None
    def process_query(query, symptoms=None):
        return None
    def process_query3(query, symptoms=None):
        return None

if not FAQ_AVAILABLE:
    def get_simple_faq_response(query):
        return None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-fallback-secret-key')

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Keep SQLite database under a writable path.
# On Vercel, only `/tmp` is writable and is ephemeral.
try:
    os.makedirs(app.instance_path, exist_ok=True)
except Exception:
    pass

is_vercel = os.getenv('VERCEL') == '1' or bool(os.getenv('VERCEL_ENV'))
sqlite_path_env = os.getenv('SQLITE_PATH')
db_uri_env = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL')

if is_vercel:
    # Force SQLite on Vercel; use /tmp by default for write access
    sqlite_path = sqlite_path_env or '/tmp/docify.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
else:
    if db_uri_env:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri_env
    else:
        sqlite_path = sqlite_path_env or os.path.join(app.instance_path, 'docify.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Configure allowed IP addresses/CIDR ranges and optional bypass
ALLOWED_IPS = os.getenv('ALLOWED_IPS', '127.0.0.1/32').split(',')
DISABLE_IP_FILTER = os.getenv('DISABLE_IP_FILTER', 'false').lower() in {'1','true','yes'}

def is_ip_allowed(ip_address):
    """Check if the IP address is in the allowed list"""
    try:
        client_ip = ipaddress.ip_address(ip_address)
        for allowed_range in ALLOWED_IPS:
            if client_ip in ipaddress.ip_network(allowed_range, strict=False):
                return True
        return False
    except ValueError:
        return False

@app.before_request
def limit_remote_addr():
    """Middleware to check IP address before processing requests"""
    if DISABLE_IP_FILTER:
        return
    # Get client IP (handle proxy headers if behind load balancer)
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if client_ip:
        # If behind proxy, get the first IP
        client_ip = client_ip.split(',')[0].strip()
    
    # Skip IP check for health/static endpoints (optional)
    if request.endpoint in ['health', 'status', 'static']:
        return
    
    if not is_ip_allowed(client_ip):
        abort(403)  # Forbidden


@app.route('/health', methods=['GET'])
def health():
    """Simple health check endpoint"""
    return jsonify(status="ok"), 200


# -------------------- Helpers & Decorators --------------------
from functools import wraps

def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

def login_required_page(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper

def login_required_json(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "Please log in"}), 401
        return view_func(*args, **kwargs)
    return wrapper

def safe_commit(success_message: str | None = None, error_message: str | None = None) -> bool:
    try:
        db.session.commit()
        if success_message:
            flash(success_message, 'success')
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception(f"DB commit failed: {e}")
        if error_message:
            flash(error_message, 'error')
        return False

def safe_commit_json() -> tuple[bool, str | None]:
    try:
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        logger.exception(f"DB commit failed: {e}")
        return False, str(e)


@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'no-referrer')
    return response


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, completed
    doctor_notes = db.Column(db.Text, nullable=True)  # Doctor's response/advice
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('consultations', lazy=True))


# Initialize Database
with app.app_context():
    db.create_all()


# Export User Details to CSV
def export_users_to_csv():
    users = User.query.all()
    with open('users.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'name', 'phone', 'email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for user in users:
            writer.writerow({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'email': user.email

            })


# Routes
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        new_user = User(name=name, phone=phone, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        export_users_to_csv()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required_page
def dashboard():
    user = get_current_user()
    
    # Check if user exists
    if not user:
        session.pop('user_id', None)
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        symptoms = request.form['symptoms']
        consultation = Consultation(user_id=user.id, symptoms=symptoms)
        db.session.add(consultation)
        if safe_commit('Consultation form submitted successfully!'):
            return redirect(url_for('dashboard'))
        return redirect(url_for('dashboard'))

    consultations = (Consultation.query
                     .filter_by(user_id=user.id)
                     .order_by(Consultation.created_at.desc())
                     .all())
    return render_template('dash.html', user=user, consultations=consultations)


@app.route('/update_consultation/<int:id>', methods=['GET', 'POST'])
@login_required_page
def update_consultation(id):
    consultation = Consultation.query.get_or_404(id)
    if consultation.user_id != session['user_id']:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        consultation.symptoms = request.form['symptoms']
        consultation.updated_at = datetime.utcnow()
        if safe_commit('Consultation updated successfully!'):
            return redirect(url_for('dashboard'))
        return redirect(url_for('dashboard'))

    return render_template('update_consultation.html', consultation=consultation)


@app.route('/faq')
def faq():
    return render_template('faq.html')


# Delete Consultation Route
@app.route('/delete_consultation/<int:id>', methods=['POST'])
@login_required_json
def delete_consultation(id):
    consultation = Consultation.query.get_or_404(id)
    if consultation.user_id != session['user_id']:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    db.session.delete(consultation)
    ok, err = safe_commit_json()
    if ok:
        return jsonify({"success": True, "message": "Consultation deleted successfully"})
    return jsonify({"success": False, "message": f"Delete failed: {err}"}), 500


# User Profile Route
@app.route('/profile', methods=['GET', 'POST'])
@login_required_page
def profile():
    user = get_current_user()
    if not user:
        session.clear()
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user.name = request.form.get('name', user.name)
        user.phone = request.form.get('phone', user.phone)
        user.age = request.form.get('age', type=int)
        user.gender = request.form.get('gender')
        user.blood_group = request.form.get('blood_group')
        user.medical_history = request.form.get('medical_history')
        user.allergies = request.form.get('allergies')
        
        if safe_commit('Profile updated successfully!'):
            return redirect(url_for('profile'))
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)


# Update Consultation Status (for admin/doctor use)
@app.route('/update_status/<int:id>', methods=['POST'])
@login_required_json
def update_status(id):
    consultation = Consultation.query.get_or_404(id)
    
    data = request.json
    new_status = data.get('status')
    doctor_notes = data.get('doctor_notes')
    
    if new_status:
        consultation.status = new_status
    if doctor_notes:
        consultation.doctor_notes = doctor_notes
    
    consultation.updated_at = datetime.utcnow()
    ok, err = safe_commit_json()
    if ok:
        return jsonify({"success": True, "message": "Status updated successfully"})
    return jsonify({"success": False, "message": f"Update failed: {err}"}), 500


# Updated Chatbot Route
@app.route('/chatbot', methods=['POST'])
def chatbot():

    data = request.json
    query = data.get('message')
    logger.info("chatbot query received")
    if not query:
        return jsonify({"reply": "Please provide a message."}), 400
    try:
        # Append user message for analysis (UTF-8)
        with open("query_dataset.csv", "a", encoding='utf-8', newline='') as file:
            # Replace newlines to keep one line per entry
            safe_query = (query or "").replace('\r', ' ').replace('\n', ' ').strip()
            file.write(safe_query + "\n")
    except Exception as e:
        logger.warning(f"Could not append to query_dataset.csv: {e}")
    # Get latest symptoms from user's consultations
    if 'user_id' in session:
        latest_consultation = Consultation.query.filter_by(user_id=session['user_id']).order_by(
            Consultation.created_at.desc()).first()
        symptoms = latest_consultation.symptoms if latest_consultation else None
    else:
        symptoms = None


    try:
        # Try advanced chatbot function first
        if ADVANCED_MODULES_AVAILABLE:
            response = process_query5(query, symptoms)
            logger.info("chatbot response generated")
            
            # Check if response is valid
            if response and response.strip():
                return jsonify({"reply": response})
        
        # Fall back to simple FAQ responses
        if FAQ_AVAILABLE:
            response = get_simple_faq_response(query)
            return jsonify({"reply": response})
        else:
            # Last resort fallback
            return jsonify({"reply": "I'm sorry, I couldn't generate a response. Please try asking about Docify Online services."})
            
    except Exception as e:
        logger.exception(f"Error in chatbot endpoint: {e}")
        
        # Try FAQ fallback
        if FAQ_AVAILABLE:
            try:
                response = get_simple_faq_response(query)
                return jsonify({"reply": response})
            except Exception as e2:
                print(f"Error in FAQ fallback: {e2}")
        
        # Final fallback response
        fallback_response = """
        Welcome to Docify Online! I'm here to help you with:
        - Information about our medical consultation services
        - How to submit consultation forms
        - FAQ about our platform
        - General health information guidance
        
        What would you like to know about Docify Online?
        """
        return jsonify({"reply": fallback_response.strip()})


# Friendly error handlers (register globally so they work under Gunicorn too)
@app.errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template('error_403.html'), 403
    return jsonify(error='Forbidden'), 403

@app.errorhandler(404)
def not_found(e):
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template('error_404.html'), 404
    return jsonify(error='Not Found'), 404

@app.errorhandler(500)
def server_error(e):
    if request.accept_mimetypes.accept_html and not request.is_json:
        return render_template('error_500.html'), 500
    return jsonify(error='Internal Server Error'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5000)
