from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

# Association table for User-Organization many-to-many relationship
user_organization = db.Table('user_organization',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('organization_id', db.Integer, db.ForeignKey('organization.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    id_card = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='user') # 'admin' or 'user'
    last_login_ip = db.Column(db.String(50))
    failed_login_count = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organizations = db.relationship('Organization', secondary=user_organization, backref=db.backref('users', lazy='dynamic'))

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    access_code = db.Column(db.String(50), unique=True, nullable=True)
    
    # Relationships
    elections = db.relationship('Election', backref='organization', lazy=True)

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='upcoming') # 'upcoming', 'active', 'closed'
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    topics = db.Column(db.String(255)) # comma-separated topics
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    # Relationships
    candidates = db.relationship('Candidate', backref='election', lazy=True, cascade="all, delete-orphan")
    votes = db.relationship('Vote', backref='election', lazy=True, cascade="all, delete-orphan")
    voter_records = db.relationship('VoterRecord', backref='election', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('Alert', backref='election', lazy=True, cascade="all, delete-orphan")

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    platform_keywords = db.Column(db.String(255)) # comma-separated keywords for recommendations
    views_count = db.Column(db.Integer, default=0)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    
    # Relationships
    votes = db.relationship('Vote', backref='candidate', lazy=True, cascade="all, delete-orphan")

class VoterRecord(db.Model):
    """Tracks if a user has voted in an election to enforce one-vote, without linking to the specific vote"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Vote(db.Model):
    """The actual anonymous vote, implemented as a simple blockchain"""
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Blockchain fields
    previous_hash = db.Column(db.String(64), nullable=False)
    hash = db.Column(db.String(64), nullable=False)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Null for anonymous/failed login attempts
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50))
    session_id = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

class UserBehavior(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    page_url = db.Column(db.String(255))
    time_spent = db.Column(db.Float) # in seconds
    refreshes = db.Column(db.Integer, default=0)
    multiple_submissions = db.Column(db.Boolean, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('behaviors', lazy=True))

class SessionRisk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    risk_score = db.Column(db.Float, default=0.0) # 0 to 100
    risk_factors = db.Column(db.Text) # JSON string of factors
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('risks', lazy=True))

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(50), default='warning')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
