from flask import Flask
import os
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache
from app.models import db, User

bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
cache = Cache()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey_for_evoting_system_change_in_production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evoting.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Caching Config (Simple in-memory cache)
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    # Mail Config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'areejelghrazzz@gmail.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'dczqfwodlpoubasp')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'areejelghrazzz@gmail.com')

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.voter import voter_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from datetime import datetime
    from app.models import Election, UserBehavior
    from flask import request, session
    from flask_login import current_user

    @app.before_request
    def monitor_system():
        # 1. Automatic Election Activation/Deactivation
        # Use local time since start_time and end_time are set using naive local datetimes via HTML input
        now = datetime.now()
        # Active elections that should be closed
        overdue = Election.query.filter(Election.status == 'active', Election.end_time < now).all()
        for e in overdue:
            e.status = 'closed'
        
        # Upcoming elections that should be active
        to_activate = Election.query.filter(Election.status == 'upcoming', Election.start_time <= now, Election.end_time > now).all()
        for e in to_activate:
            e.status = 'active'
        
        if overdue or to_activate:
            db.session.commit()

        # 2. Behavioral Tracking (IOB & Engagement)
        if current_user.is_authenticated and not request.path.startswith('/static'):
            last_path = session.get('last_path')
            last_time = session.get('last_time')
            
            if last_path and last_time:
                time_spent = (datetime.utcnow() - datetime.fromisoformat(last_time)).total_seconds()
                # If they stayed on the same page, it might be a refresh or just long read
                if last_path == request.path:
                    session['refreshes'] = session.get('refreshes', 0) + 1
                else:
                    # Save behavior record when moving to a new page
                    behavior = UserBehavior(
                        user_id=current_user.id,
                        page_url=last_path,
                        time_spent=time_spent,
                        refreshes=session.get('refreshes', 0)
                    )
                    db.session.add(behavior)
                    db.session.commit()
                    session['refreshes'] = 0
            
            session['last_path'] = request.path
            session['last_time'] = datetime.utcnow().isoformat()

    return app
