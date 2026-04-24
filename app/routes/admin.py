from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime
from flask_login import login_required, current_user
from app.models import db, Organization, Election, Candidate, User, AuditLog, Alert, Vote, SessionRisk, UserBehavior
from app.smart_features import predict_participation, analyze_engagement
from app import cache

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
@cache.cached(timeout=60, key_prefix='admin_dashboard')
def dashboard():
    orgs_count = Organization.query.count()
    elections_count = Election.query.count()
    users_count = User.query.count()
    votes_count = Vote.query.count()
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(5).all()
    
    # Data for charts
    elections = Election.query.all()
    status_counts = {'upcoming': 0, 'active': 0, 'closed': 0}
    for e in elections:
        status_counts[e.status] = status_counts.get(e.status, 0) + 1
        
    return render_template('admin/dashboard.html', 
                           orgs_count=orgs_count, 
                           elections_count=elections_count,
                           users_count=users_count,
                           votes_count=votes_count,
                           alerts=alerts,
                           status_labels=list(status_counts.keys()),
                           status_data=list(status_counts.values()))

@admin_bp.route('/users', methods=['GET'])
@admin_required
@cache.cached(timeout=60, key_prefix='admin_users')
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/update_role', methods=['POST'])
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot change your own role here.", "danger")
    else:
        user.role = request.form.get('role')
        db.session.commit()
        cache.delete('admin_users')
        flash(f"User {user.username} role updated.", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete yourself.", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        cache.delete('admin_users')
        flash(f"User {user.username} deleted.", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/organizations', methods=['GET', 'POST'])
@admin_required
def manage_orgs():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        access_code = request.form.get('access_code')
        org = Organization(name=name, description=description, access_code=access_code)
        db.session.add(org)
        db.session.commit()
        cache.delete('admin_orgs')
        flash('Organization created.', 'success')
        return redirect(url_for('admin.manage_orgs'))
        
    return get_cached_orgs()

@cache.cached(timeout=60, key_prefix='admin_orgs')
def get_cached_orgs():
    orgs = Organization.query.all()
    users = User.query.filter_by(role='voter').all()
    return render_template('admin/organizations.html', orgs=orgs, users=users)

@admin_bp.route('/organizations/<int:org_id>/update', methods=['POST'])
@admin_required
def update_org(org_id):
    org = Organization.query.get_or_404(org_id)
    org.name = request.form.get('name')
    org.description = request.form.get('description')
    org.access_code = request.form.get('access_code')
    db.session.commit()
    cache.delete('admin_orgs')
    flash(f'Organization {org.name} updated.', 'success')
    return redirect(url_for('admin.manage_orgs'))

@admin_bp.route('/organizations/<int:org_id>/delete', methods=['POST'])
@admin_required
def delete_org(org_id):
    org = Organization.query.get_or_404(org_id)
    db.session.delete(org)
    db.session.commit()
    cache.delete('admin_orgs')
    flash(f'Organization deleted.', 'success')
    return redirect(url_for('admin.manage_orgs'))

@admin_bp.route('/organizations/<int:org_id>/add_user', methods=['POST'])
@admin_required
def add_user_to_org(org_id):
    org = Organization.query.get_or_404(org_id)
    user_id = request.form.get('user_id')
    user = User.query.get(user_id)
    
    if user and user not in org.users:
        org.users.append(user)
        db.session.commit()
        cache.delete('admin_orgs')
        flash(f'User {user.username} added to {org.name}.', 'success')
    else:
        flash('User already in organization or not found.', 'warning')
        
    return redirect(url_for('admin.manage_orgs'))

@admin_bp.route('/organizations/<int:org_id>/remove_user/<int:user_id>', methods=['POST'])
@admin_required
def remove_user_from_org(org_id, user_id):
    org = Organization.query.get_or_404(org_id)
    user = User.query.get_or_404(user_id)
    
    if user in org.users:
        org.users.remove(user)
        db.session.commit()
        cache.delete('admin_orgs')
        flash(f'User {user.username} removed from {org.name}.', 'success')
        
    return redirect(url_for('admin.manage_orgs'))

@admin_bp.route('/elections', methods=['GET', 'POST'])
@admin_required
def manage_elections():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        org_id = request.form.get('organization_id')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        topics = request.form.get('topics')
        
        # Convert string to datetime
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        election = Election(
            title=title, 
            description=description, 
            organization_id=org_id,
            start_time=start_dt,
            end_time=end_dt,
            topics=topics
        )
        db.session.add(election)
        db.session.commit()
        cache.delete('admin_elections')
        flash('Election created and scheduled.', 'success')
        return redirect(url_for('admin.manage_elections'))
        
    return get_cached_elections()

@cache.cached(timeout=60, key_prefix='admin_elections')
def get_cached_elections():
    elections = Election.query.all()
    orgs = Organization.query.all()
    return render_template('admin/elections.html', elections=elections, orgs=orgs)

@admin_bp.route('/elections/<int:election_id>/update', methods=['POST'])
@admin_required
def update_election(election_id):
    election = Election.query.get_or_404(election_id)
    election.title = request.form.get('title')
    election.description = request.form.get('description')
    
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    election.topics = request.form.get('interests') or request.form.get('topics') # Handle both if needed
    
    if start_time:
        election.start_time = datetime.fromisoformat(start_time)
    if end_time:
        election.end_time = datetime.fromisoformat(end_time)
        
    db.session.commit()
    cache.delete('admin_elections')
    flash(f'Election updated.', 'success')
    return redirect(url_for('admin.manage_elections'))

@admin_bp.route('/elections/<int:election_id>/delete', methods=['POST'])
@admin_required
def delete_election(election_id):
    election = Election.query.get_or_404(election_id)
    db.session.delete(election)
    db.session.commit()
    cache.delete('admin_elections')
    flash(f'Election deleted.', 'success')
    return redirect(url_for('admin.manage_elections'))

@admin_bp.route('/elections/<int:election_id>/status', methods=['POST'])
@admin_required
def update_election_status(election_id):
    election = Election.query.get_or_404(election_id)
    status = request.form.get('status')
    if status in ['upcoming', 'active', 'closed']:
        election.status = status
        db.session.commit()
        cache.delete('admin_elections')
        flash(f'Election status updated to {status}.', 'success')
    return redirect(url_for('admin.manage_elections'))

@admin_bp.route('/elections/<int:election_id>/candidates', methods=['POST'])
@admin_required
def add_candidate(election_id):
    name = request.form.get('name')
    description = request.form.get('description')
    platform_keywords = request.form.get('platform_keywords')
    
    candidate = Candidate(name=name, description=description, platform_keywords=platform_keywords, election_id=election_id)
    db.session.add(candidate)
    db.session.commit()
    cache.delete('admin_elections')
    flash('Candidate added.', 'success')
    return redirect(url_for('admin.manage_elections'))

@admin_bp.route('/candidates/<int:candidate_id>/update', methods=['POST'])
@admin_required
def update_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    candidate.name = request.form.get('name')
    candidate.description = request.form.get('description')
    candidate.platform_keywords = request.form.get('platform_keywords')
    db.session.commit()
    cache.delete('admin_elections')
    flash(f'Candidate {candidate.name} updated.', 'success')
    return redirect(url_for('admin.manage_elections'))

@admin_bp.route('/candidates/<int:candidate_id>/delete', methods=['POST'])
@admin_required
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    db.session.delete(candidate)
    db.session.commit()
    cache.delete('admin_elections')
    flash('Candidate deleted.', 'success')
    return redirect(url_for('admin.manage_elections'))

@admin_bp.route('/audit')
@admin_required
@cache.cached(timeout=60, key_prefix='admin_audit')
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('admin/audit.html', logs=logs)

@admin_bp.route('/elections/<int:election_id>/results')
@admin_required
@cache.cached(timeout=60)
def election_results(election_id):
    election = Election.query.get_or_404(election_id)
    
    # Calculate results
    results = []
    labels = []
    data = []
    
    for candidate in election.candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
        results.append({'name': candidate.name, 'votes': vote_count})
        labels.append(candidate.name)
        data.append(vote_count)
        
    return render_template('admin/results.html', election=election, results=results, labels=labels, data=data)

@admin_bp.route('/analytics')
@admin_required
@cache.cached(timeout=60, key_prefix='admin_analytics')
def analytics():
    # Behavioral Security: High Risk Sessions
    risky_sessions = SessionRisk.query.filter(SessionRisk.risk_score > 50).order_by(SessionRisk.risk_score.desc()).limit(10).all()
    
    # Participation Prediction for active elections
    active_elections = Election.query.filter_by(status='active').all()
    predictions = {}
    for e in active_elections:
        predictions[e.title] = predict_participation(e.id)
        
    # IOB: Engagement Monitoring
    engagement = analyze_engagement()
    
    # Behavioral Analytics Summary
    total_locked = User.query.filter_by(is_locked=True).count()
    
    # Candidate Engagement
    top_candidates = Candidate.query.order_by(Candidate.views_count.desc()).limit(5).all()
    total_candidate_views = db.session.query(db.func.sum(Candidate.views_count)).scalar() or 0
    
    return render_template('admin/analytics.html', 
                           risky_sessions=risky_sessions, 
                           predictions=predictions,
                           engagement=engagement,
                           total_locked=total_locked,
                           top_candidates=top_candidates,
                           total_candidate_views=total_candidate_views)
