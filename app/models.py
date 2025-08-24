from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Index
import bcrypt
from datetime import datetime

# Import db from extensions to avoid circular imports
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False, index=True)
    email = db.Column(db.String(256), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    profile = db.Column(JSON, nullable=True, default=dict)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    command_audits = db.relationship('CommandAudit', backref='user', lazy='dynamic',
                                   cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic',
                             cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash using bcrypt"""
        salt = bcrypt.gensalt(rounds=13)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        """Check password against hash using bcrypt"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }
        if include_sensitive:
            data['profile'] = self.profile
            data['is_admin'] = self.is_admin
        return data

class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(256), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

class CommandAudit(db.Model):
    __tablename__ = 'command_audits'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    username = db.Column(db.String(128), nullable=True)
    command = db.Column(db.Text, nullable=False)
    args = db.Column(JSON, nullable=True)
    return_code = db.Column(db.Integer, nullable=True)
    stdout = db.Column(db.Text, nullable=True)
    stderr = db.Column(db.Text, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)  # in seconds
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_command_user_time', user_id, created_at),
        Index('idx_command_time', created_at),
    )

    def __repr__(self):
        return f'<CommandAudit {self.command[:50]}...>'

    def to_dict(self, include_output=True):
        data = {
            'id': self.id,
            'username': self.username,
            'command': self.command,
            'return_code': self.return_code,
            'execution_time': self.execution_time,
            'created_at': self.created_at.isoformat()
        }
        if include_output:
            data.update({
                'stdout': self.stdout[:2000] if self.stdout else '',
                'stderr': self.stderr[:2000] if self.stderr else ''
            })
        return data

class AIInteraction(db.Model):
    __tablename__ = 'ai_interactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    interaction_type = db.Column(db.String(50), nullable=False)  # 'chat', 'summarize'
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text, nullable=True)
    model_used = db.Column(db.String(100), nullable=True)
    response_time = db.Column(db.Float, nullable=True)
    tokens_used = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Boolean, default=True, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_ai_user_type_time', user_id, interaction_type, created_at),
    )