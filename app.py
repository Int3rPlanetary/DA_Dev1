"""Flask application main module."""
import os
import logging
import json
import random
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import stripe
from typing import Optional, Dict, List, Any, Union
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import time
from wtforms import StringField, PasswordField, BooleanField, IntegerField, FloatField, TextAreaField, SelectField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, URL, ValidationError
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib
import re
from slugify import slugify

# Load environment variables
load_dotenv()

# Unsplash API configuration
UNSPLASH_ACCESS_KEY = os.getenv('NEXT_PUBLIC_UNSPLASH_ACCESS_KEY', 'FxuNe95JEqmUHUmRb70GACHfzn9G5vmf7LA5GQEo4-4')

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Add context processor for datetime
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow(), 'timedelta': timedelta}

# Add custom filters
@app.template_filter('format_number')
def format_number(value):
    """Format a number with commas as thousands separators."""
    return "{:,}".format(value) if value is not None else "0"

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    logger.warning("SESSION_SECRET environment variable not set! Using development secret key.")
    app.secret_key = "dev-secret-key-for-testing"

# Use SQLite instead of PostgreSQL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///retronet_portal.db")
logger.info(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}

# CSRF Protection Configuration
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = app.secret_key
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['DEBUG'] = True

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

# Initialize extensions
from database import db, init_db
csrf = CSRFProtect()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

# Initialize extensions
logger.info("Initializing Flask extensions...")
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
mail.init_app(app)

# Initialize database
logger.info("Initializing database...")
init_db(app)

# Initialize Flask-Migrate after database
migrate.init_app(app, db)

# Import models and forms after extensions are initialized
with app.app_context():
    from models import User, SystemSettings, PasswordReset, Listing, Message, DAG, Product, Campaign, Project, Channel, Post, Comment, Reaction, PollOption, PollVote
    from forms import SystemSettingsForm, DAGForm, PointsAllocationForm, RegistrationForm, ChannelForm, PostForm, CommentForm

    # Initialize migration
    logger.info("Initializing database migrations...")
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}", exc_info=True)
        raise

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# User Management
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    try:
        user = User.query.get(int(user_id))
        logger.debug(f"Loading user {user_id}: {'Found' if user else 'Not found'}")
        return user
    except Exception as e:
        logger.error(f"Error loading user: {str(e)}")
        return None

def send_verification_code(email: str, code: str) -> bool:
    """Send verification code via email."""
    try:
        msg = Message('Your Login Code',
                     sender=app.config['MAIL_DEFAULT_SENDER'],
                     recipients=[email])
        msg.body = f'''Your login code is: {code}

This code will expire in 30 minutes.
'''
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending verification code: {str(e)}")
        return False

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle both password and passwordless login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = FlaskForm()
    
    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('Invalid form submission')
            return render_template('login.html', form=form)

        email = request.form.get('email')
        password = request.form.get('password')
        login_type = request.form.get('login_type', 'password')

        if not email:
            flash('Email is required')
            return render_template('login.html', form=form)

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with this email address')
            return render_template('login.html', form=form)

        if login_type == 'password':
            if not password:
                flash('Password is required')
                return render_template('login.html', form=form)

            if not user.password_hash:
                flash('Please use passwordless login or reset your password')
                return render_template('login.html', form=form)

            if not check_password_hash(user.password_hash, password):
                flash('Invalid password')
                return render_template('login.html', form=form)

            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            # Passwordless login
            code = ''.join(secrets.choice('0123456789') for _ in range(6))
            reset = PasswordReset(email=email, code=code)
            
            try:
                db.session.add(reset)
                db.session.commit()
                
                if send_verification_code(email, code):
                    flash('A verification code has been sent to your email')
                    session['login_email'] = email
                    return redirect(url_for('verify_login'))
                else:
                    flash('Error sending verification code')
                    return render_template('login.html', form=form)
            except Exception as e:
                logger.error(f"Error in passwordless login: {str(e)}")
                db.session.rollback()
                flash('Error processing login')
                return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/verify_login', methods=['GET', 'POST'])
def verify_login():
    """Handle login code verification."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = FlaskForm()
    email = session.get('login_email')
    
    if not email:
        flash('Please start the login process again')
        return redirect(url_for('login'))

    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('Invalid form submission')
            return render_template('verify_login.html', form=form)

        code = request.form.get('code')
        if not code:
            flash('Verification code is required')
            return render_template('verify_login.html', form=form)

        try:
            reset = PasswordReset.query.filter_by(
                email=email,
                code=code,
                used=False
            ).order_by(PasswordReset.created_at.desc()).first()

            if not reset or datetime.utcnow() - reset.created_at > timedelta(minutes=30):
                flash('Invalid or expired verification code')
                return render_template('verify_login.html', form=form)

            reset.used = True
            user = User.query.filter_by(email=email).first()
            
            if user:
                login_user(user)
                db.session.commit()
                session.pop('login_email', None)
                return redirect(url_for('dashboard'))
            else:
                flash('User not found')
                return redirect(url_for('login'))

        except Exception as e:
            logger.error(f"Error in verification: {str(e)}")
            db.session.rollback()
            flash('Error processing verification')
            return render_template('verify_login.html', form=form)

    return render_template('verify_login.html', form=form)

@app.route('/logout')
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/registration_statement')
def registration_statement():
    """Show registration statement before proceeding to registration"""
    try:
        logger.info("Accessing registration statement page")
        return render_template('registration_statement.html')
    except Exception as e:
        logger.error(f"Error showing registration statement: {str(e)}", exc_info=True)
        return render_template('error.html', error="Error loading registration statement"), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = FlaskForm()
    
    if request.method == 'POST':
        if not form.validate_on_submit():
            flash('Invalid form submission')
            return render_template('register.html', form=form)

        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        if not all([email, username, password]):
            flash('All fields are required')
            return render_template('register.html', form=form)

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html', form=form)

        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return render_template('register.html', form=form)

        try:
            user = User(
                email=email,
                username=username,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Error in registration: {str(e)}")
            db.session.rollback()
            flash('Error creating account')
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)

# Core Routes
@app.route('/')
def index():
    """Index route."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route"""
    try:
        logger.debug(f"Loading user {current_user.id}: Found")
        
        # Get projects data
        projects = {
            'active_projects': [
                {
                    'id': 1,
                    'title': 'Mobile App Development',
                    'description': 'Creating native mobile applications for RetroNet Portal',
                    'current_funding': 35000,
                    'funding_goal': 45000
                },
                {
                    'id': 2,
                    'title': 'Community Education Platform',
                    'description': 'Development of educational resources and learning paths',
                    'current_funding': 25000,
                    'funding_goal': 50000
                },
                {
                    'id': 3,
                    'title': 'Marketplace Enhancement',
                    'description': 'Adding advanced features to the bazaar system',
                    'current_funding': 15000,
                    'funding_goal': 30000
                }
            ],
            'backlog_projects': [
                {
                    'id': 4,
                    'title': 'Analytics Dashboard',
                    'description': 'Advanced analytics for community engagement',
                    'votes': 120,
                    'current_funding': 10000,
                    'funding_goal': 40000
                },
                {
                    'id': 5,
                    'title': 'Decentralized Identity',
                    'description': 'Implementing decentralized identity solutions',
                    'votes': 95,
                    'current_funding': 5000,
                    'funding_goal': 25000
                }
            ]
        }
        
        # Get treasury data
        treasury_data = {
            'total_daps': 1000000,
            'fiat_balance': 50000.00,
            'member_count': 150,
            'bazaar_revenue': 25000.00,
            'active_fundraising': 5,
            'assistance_queue': 3,
            'pending_loans': 2,
            'loan_capacity': 10,
            'waitlist_length': 8,
            'avg_wait_time': 3,
            'active_dags': 12,
            'total_projects': 45,
            'member_engagement_rate': 78.5,
            'growth_rate': 12.3,
            'backlog_projects': [
                {
                    'id': 1,
                    'title': 'Community Education Platform',
                    'description': 'Development of educational resources and learning paths',
                    'votes': 156,
                    'current_funding': 25000,
                    'funding_goal': 50000
                },
                {
                    'id': 2,
                    'title': 'Marketplace Enhancement',
                    'description': 'Adding advanced features to the bazaar system',
                    'votes': 142,
                    'current_funding': 15000,
                    'funding_goal': 30000
                }
            ],
            'wip_projects': [
                {
                    'id': 3,
                    'title': 'Mobile App Development',
                    'description': 'Creating native mobile applications',
                    'current_funding': 35000,
                    'funding_goal': 45000
                }
            ]
        }
        
        return render_template('dashboard.html',
                             projects=projects,
                             treasury_data=treasury_data,
                             user=current_user)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        db.session.rollback()
        return render_template('error.html'), 500

# Health Check & System Routes
@app.route('/status')
def status():
    """Health check endpoint"""
    return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}

@app.route('/test')
def test():
    """Basic test endpoint"""
    return "Hello, World! The server is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)