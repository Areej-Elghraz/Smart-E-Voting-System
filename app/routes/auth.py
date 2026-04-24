from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app.models import db, User, AuditLog
from app import bcrypt, mail, cache
from app.smart_features import calculate_session_risk
import random
import string
from datetime import datetime, timedelta
from threading import Thread

auth_bp = Blueprint('auth', __name__)

MAX_RESEND_ATTEMPTS = 3
LOCKOUT_MINUTES = 5

def log_audit(user_id, action, ip_address, details=""):
    log = AuditLog(user_id=user_id, action=action, ip_address=ip_address, details=details)
    db.session.add(log)
    db.session.commit()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"\n OTP sent successfully to email")
        except Exception as e:
            print(f"\n[EMAIL ERROR] Could not send email: {e}")

def send_otp_email(app, email, otp):
    msg = Message('Your Login OTP', sender='areejelghrazzz@gmail.com', recipients=[email])
    msg.body = f'Your OTP for login is: {otp}'
    
    # Send in background thread
    Thread(target=send_async_email, args=(app._get_current_object(), msg)).start()
    
    # Always print to console for development/backup
    print(f"\n[BACKUP] OTP for {email} is: {otp}\n")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        id_card = request.form.get('id_card')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter((User.username == username) | (User.email == email) | (User.id_card == id_card)).first():
            flash('Username, Email, or ID Card is already in use. Please choose different ones.', 'danger')
            return redirect(url_for('auth.register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, id_card=id_card, password_hash=hashed_password, role='voter')
        db.session.add(user)
        db.session.commit()
        
        log_audit(user.id, 'Register', request.remote_addr, f'Registered user {username}')
        cache.delete('admin_users')
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        login_id = request.form.get('username_or_email')
        password = request.form.get('password')
        
        user = User.query.filter((User.username == login_id) | (User.email == login_id)).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if user.role == 'admin' or user.has_verified_otp:
                login_user(user, remember=request.form.get('remember') == 'on')
                log_audit(user.id, 'Login Success', request.remote_addr)
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('voter.dashboard'))
                
            otp = generate_otp()
            session['otp'] = otp
            session['pending_user_id'] = user.id
            session['remember'] = request.form.get('remember') == 'on'
            session['resend_attempts'] = 0
            session['lockout_time'] = None
            
            from flask import current_app
            send_otp_email(current_app, user.email, otp)
                
            # Reset failed attempts on password success (but still need OTP)
            user.failed_login_count = 0
            user.last_login_ip = request.remote_addr
            db.session.commit()
            
            # Behavioral Security: Session Risk Score
            risk_score, factors = calculate_session_risk(user.id, request.remote_addr, session.get('_id', 'unknown'))
            if risk_score > 70:
                flash(f'Security Alert: Unusual login activity detected (Risk Score: {risk_score}). Additional verification required.', 'warning')
            
            flash('An OTP has been sent to your email.', 'info')
            return redirect(url_for('auth.verify_otp'))
        else:
            if user:
                user.failed_login_count += 1
                if user.failed_login_count >= 5:
                    user.is_locked = True
                    flash('Account locked due to too many failed attempts. Contact admin.', 'danger')
                db.session.commit()
                
            log_audit(None, 'Login Failed', request.remote_addr, f'Failed login attempt for: {login_id}')
            flash('Login Unsuccessful. Please check your credentials.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if 'pending_user_id' not in session:
        flash('Session expired or invalid. Please login again.', 'danger')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        expected_otp = session.get('otp')
        
        if entered_otp == expected_otp:
            user = User.query.get(session['pending_user_id'])
            if user:
                user.has_verified_otp = True
                db.session.commit()
                
                login_user(user, remember=session.get('remember', False))
                log_audit(user.id, 'Login Success', request.remote_addr)
                
                # Cleanup session
                session.pop('otp', None)
                session.pop('pending_user_id', None)
                session.pop('remember', None)
                session.pop('resend_attempts', None)
                session.pop('lockout_time', None)
                
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('voter.dashboard'))
            else:
                flash('User not found. Please login again.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            
    return render_template('auth/verify_otp.html')

@auth_bp.route('/resend_otp', methods=['POST'])
def resend_otp():
    if 'pending_user_id' not in session:
        flash('Session expired. Please login again.', 'danger')
        return redirect(url_for('auth.login'))
        
    # Check lockout
    if session.get('lockout_time'):
        lockout_time = datetime.fromisoformat(session['lockout_time'])
        if datetime.utcnow() < lockout_time:
            wait_time = int((lockout_time - datetime.utcnow()).total_seconds() / 60)
            flash(f'You have exceeded the maximum resend attempts. Please wait {wait_time} minutes before trying again.', 'danger')
            return redirect(url_for('auth.verify_otp'))
        else:
            # Lockout expired, reset attempts
            session['resend_attempts'] = 0
            session['lockout_time'] = None

    attempts = session.get('resend_attempts', 0)
    
    if attempts >= MAX_RESEND_ATTEMPTS:
        lockout_time = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
        session['lockout_time'] = lockout_time.isoformat()
        flash(f'Maximum resend attempts reached. Please wait {LOCKOUT_MINUTES} minutes.', 'danger')
        return redirect(url_for('auth.verify_otp'))
        
    user = User.query.get(session['pending_user_id'])
    if user:
        otp = generate_otp()
        session['otp'] = otp
        session['resend_attempts'] = attempts + 1
        
        from flask import current_app
        send_otp_email(current_app, user.email, otp)
        flash('A new OTP has been sent to your email.', 'success')
    else:
        flash('User error.', 'danger')
        
    return redirect(url_for('auth.verify_otp'))

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(current_user.id, 'Logout', request.remote_addr)
    # Clear user specific cache
    cache.delete(f'voter_dashboard_{current_user.id}')
    logout_user()
    return redirect(url_for('index'))
