from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from database.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client') # 'client', 'lawyer', 'admin'
    
    # Relationships
    lawyer_profile = db.relationship('LawyerProfile', backref='user', uselist=False)
    cases_as_client = db.relationship('Case', foreign_keys='Case.client_id', backref='client', lazy=True)
    cases_as_lawyer = db.relationship('Case', foreign_keys='Case.lawyer_id', backref='lawyer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LawyerProfile(db.Model):
    __tablename__ = 'lawyer_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0.0)
    bio = db.Column(db.Text)

class Case(db.Model):
    __tablename__ = 'cases'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50)) # Property, Criminal, Civil, etc.
    status = db.Column(db.String(20), default='Pending') # Pending, In Progress, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lawyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    messages = db.relationship('Message', backref='case', lazy=True)
    evidences = db.relationship('Evidence', backref='case', lazy=True)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_file = db.Column(db.Boolean, default=False)

class Evidence(db.Model):
    __tablename__ = 'evidences'
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    ocr_text = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    flags = db.Column(db.Text) # JSON string or comma-separated flags
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class PropertyRecord(db.Model):
    __tablename__ = 'property_records'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.String(50), unique=True, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Valid') # Valid, Disputed
