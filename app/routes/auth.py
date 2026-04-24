from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, AuditLog
from app import bcrypt, cache
from app.smart_features import calculate_session_risk
from datetime import datetime
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def log_audit(user_id, action, ip_address, details=""):
    log = AuditLog(user_id=user_id, action=action, ip_address=ip_address, details=details)
    db.session.add(log)
    db.session.commit()

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
        
        # Log in the user automatically after registration
        login_user(user)
        flash('Account created and logged in successfully!', 'success')
        
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('voter.dashboard'))
        
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
            login_user(user, remember=request.form.get('remember') == 'on')
            log_audit(user.id, 'Login Success', request.remote_addr)
            
            # Reset security metrics
            user.failed_login_count = 0
            user.last_login_ip = request.remote_addr
            db.session.commit()
            
            # Behavioral Security: Session Risk Score (Still monitored)
            risk_score, factors = calculate_session_risk(user.id, request.remote_addr, session.get('_id', 'unknown'))
            if risk_score > 70:
                flash(f'Security Alert: Unusual login activity detected (Risk Score: {risk_score}).', 'warning')
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('voter.dashboard'))
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

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit(current_user.id, 'Logout', request.remote_addr)
    # Clear user specific cache
    cache.delete(f'voter_dashboard_{current_user.id}')
    logout_user()
    return redirect(url_for('index'))
