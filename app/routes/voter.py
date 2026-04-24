from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, Organization, Election, Candidate, Vote, VoterRecord, AuditLog
from app.blockchain import calculate_hash
from app.smart_features import analyze_voting_behavior, recommend_candidate, extract_election_topics
from datetime import datetime
from app import cache

voter_bp = Blueprint('voter', __name__)

def log_audit(user_id, action, ip_address, details=""):
    log = AuditLog(user_id=user_id, action=action, ip_address=ip_address, details=details)
    db.session.add(log)
    db.session.commit()

@voter_bp.route('/dashboard')
@login_required
def dashboard():
    cache_key = f'voter_dashboard_{current_user.id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
        
    # Show user only allowed organizations
    user_orgs = current_user.organizations
    
    # Get active elections for these orgs
    active_elections = []
    for org in user_orgs:
        elections = Election.query.filter_by(organization_id=org.id, status='active').all()
        active_elections.extend(elections)
        
    response = render_template('voter/dashboard.html', orgs=user_orgs, elections=active_elections)
    cache.set(cache_key, response, timeout=60)
    return response

@voter_bp.route('/join_org', methods=['POST'])
@login_required
def join_org():
    access_code = request.form.get('access_code')
    org = Organization.query.filter_by(access_code=access_code).first()
    
    if org:
        if org not in current_user.organizations:
            current_user.organizations.append(org)
            db.session.commit()
            cache.delete(f'voter_dashboard_{current_user.id}')
            log_audit(current_user.id, 'Joined Organization', request.remote_addr, f'Joined {org.name}')
            flash(f'Successfully joined {org.name}!', 'success')
        else:
            flash(f'You are already a member of {org.name}.', 'info')
    else:
        flash('Invalid access code.', 'danger')
        
    return redirect(url_for('voter.dashboard'))

@voter_bp.route('/election/<int:election_id>', methods=['GET', 'POST'])
@login_required
def view_election(election_id):
    election = Election.query.get_or_404(election_id)
    
    # Access Control: Ensure user belongs to the election's organization
    if election.organization not in current_user.organizations:
        flash('You do not have access to this election.', 'danger')
        return redirect(url_for('voter.dashboard'))
        
    # Check if already voted
    has_voted = VoterRecord.query.filter_by(user_id=current_user.id, election_id=election_id).first()
    
    recommended_candidates = []
    if request.method == 'POST':
        interests = request.form.get('interests', '')
        selected_topics = request.form.getlist('selected_topics')
        
        # If topics were selected, combine them into a single string
        if selected_topics:
            interests = " ".join(selected_topics) + (" " + interests if interests else "")
            
        if interests:
            recommended_candidates = recommend_candidate(interests, election.candidates)
            if recommended_candidates:
                flash('Based on your interests, we have highlighted matching candidates!', 'info')
            else:
                flash('No strong matches found for those interests.', 'warning')
            
    # Automatically generate topics from candidates if no manual topics are set or as additional options
    auto_topics = extract_election_topics(election.candidates)
    
    return render_template('voter/election.html', 
                           election=election, 
                           has_voted=has_voted, 
                           recommended_candidates=recommended_candidates,
                           auto_topics=auto_topics)

@voter_bp.route('/candidate/<int:candidate_id>')
@login_required
def view_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Access Control
    if candidate.election.organization not in current_user.organizations:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('voter.dashboard'))
        
    # Increment view count
    candidate.views_count += 1
    db.session.commit()
    
    return render_template('voter/candidate_profile.html', candidate=candidate)

@voter_bp.route('/election/<int:election_id>/vote', methods=['POST'])
@login_required
def submit_vote(election_id):
    election = Election.query.get_or_404(election_id)
    
    if election.organization not in current_user.organizations:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('voter.dashboard'))
        
    if election.status != 'active':
        flash('This election is not currently active.', 'danger')
        return redirect(url_for('voter.dashboard'))
        
    # Enforce One Vote
    if VoterRecord.query.filter_by(user_id=current_user.id, election_id=election_id).first():
        log_audit(current_user.id, 'Fraud Attempt', request.remote_addr, f'Tried to vote again in election {election_id}')
        flash('You have already voted in this election!', 'danger')
        return redirect(url_for('voter.view_election', election_id=election_id))
        
    candidate_id = request.form.get('candidate_id')
    if not candidate_id:
        flash('Please select a candidate.', 'warning')
        return redirect(url_for('voter.view_election', election_id=election_id))
        
    # --- Blockchain Simulation ---
    # Get previous block hash for this election
    last_vote = Vote.query.filter_by(election_id=election_id).order_by(Vote.id.desc()).first()
    previous_hash = last_vote.hash if last_vote else "0" * 64
    
    timestamp = datetime.utcnow()
    new_index = (last_vote.id + 1) if last_vote else 1
    
    new_hash = calculate_hash(new_index, candidate_id, election_id, timestamp, previous_hash)
    
    # 1. Record the anonymous vote
    vote = Vote(
        candidate_id=candidate_id, 
        election_id=election_id, 
        timestamp=timestamp,
        previous_hash=previous_hash,
        hash=new_hash
    )
    db.session.add(vote)
    
    # 2. Record that the user has voted
    voter_record = VoterRecord(user_id=current_user.id, election_id=election_id, timestamp=timestamp)
    db.session.add(voter_record)
    
    db.session.commit()
    
    # Clear caches
    cache.delete(f'voter_dashboard_{current_user.id}')
    cache.delete('admin_dashboard')
    
    # 3. Audit log (log that they voted, not who they voted for)
    log_audit(current_user.id, 'Vote Cast', request.remote_addr, f'Cast vote in election {election_id}')
    
    # 4. Trigger AI Anomaly Detection
    try:
        analyze_voting_behavior(election_id)
    except Exception as e:
        print(f"Anomaly detection error: {e}")
        
    flash('Your vote has been securely cast and added to the blockchain!', 'success')
    return redirect(url_for('voter.view_election', election_id=election_id))
