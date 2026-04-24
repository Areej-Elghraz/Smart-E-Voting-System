from flask import Flask
import os
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_caching import Cache
from app.models import db, User

bcrypt = Bcrypt()
login_manager = LoginManager()
cache = Cache()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey_for_evoting_system_change_in_production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///evoting.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Caching Config (Simple in-memory cache)
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
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
        try:
            # 1. Automatic Election Activation/Deactivation
            now = datetime.now()
            overdue = Election.query.filter(Election.status == 'active', Election.end_time < now).all()
            for e in overdue:
                e.status = 'closed'
            
            to_activate = Election.query.filter(Election.status == 'upcoming', Election.start_time <= now, Election.end_time > now).all()
            for e in to_activate:
                e.status = 'active'
            
            if overdue or to_activate:
                db.session.commit()

            # 2. Behavioral Tracking (IOB & Engagement)
            if current_user.is_authenticated and not request.path.startswith('/static'):
                last_path = session.get('last_path')
                last_time_str = session.get('last_time')
                
                if last_path and last_time_str:
                    try:
                        last_time = datetime.fromisoformat(last_time_str)
                        time_spent = (datetime.utcnow() - last_time).total_seconds()
                        
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
                    except (ValueError, TypeError):
                        # Handle cases where last_time might be corrupted
                        pass
                
                session['last_path'] = request.path
                session['last_time'] = datetime.utcnow().isoformat()
        except Exception as e:
            # Prevent system monitor from crashing the whole app
            print(f"System monitor error: {e}")
            db.session.rollback()

    return app
