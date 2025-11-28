# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize SQLAlchemy instance (to be init_app()'d by your app)
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Simple user model for local dev auth. Stores username, display name and password hash.
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    """
    Optional message persistence model. If you use it, you can persist messages per-user
    and per-session. For minimal risk this is not automatically wired in; add writes where
    you want to persist.
    """
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)      # 0 for guest
    role = db.Column(db.String(20), nullable=False)      # 'user' or 'assistant' or 'system'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(80), nullable=True)
