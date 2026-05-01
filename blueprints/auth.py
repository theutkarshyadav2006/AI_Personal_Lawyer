from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database.models import User
from database.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
            
        flash('Invalid email or password')
        
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'client') # default to client
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered')
            return redirect(url_for('auth.register'))
            
        new_user = User(name=name, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'lawyer':
            from database.models import LawyerProfile
            profile = LawyerProfile(
                user_id=new_user.id,
                specialization="General Practice",
                experience_years=0,
                rating=0.0,
                bio="New lawyer profile"
            )
            db.session.add(profile)
            db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('main.dashboard'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
