from app import create_app, bcrypt
from app.models import db, User
from flask import redirect, url_for, render_template
from flask_login import current_user

app = create_app()

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('voter.dashboard'))
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create a default admin user if none exists
        if not User.query.filter_by(username='admin').first():
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(username='admin', email='admin@evoting.com', id_card='ADMIN001', password_hash=hashed_pw, role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin / admin123")
    app.run(debug=True)
