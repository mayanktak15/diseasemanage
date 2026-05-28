import logging
from datetime import datetime
from sqlalchemy import event

from .extensions import db

logger = logging.getLogger("docify.audit")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Consultation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    doctor_notes = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(10), default='normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('consultations', lazy=True))


# SQLAlchemy Audit Hook Event Listeners
@event.listens_for(db.Session, "after_flush")
def audit_session_changes(session, flush_context):
    for obj in session.new:
        if isinstance(obj, (User, Consultation)):
            logger.info(f"[AUDIT] INSERT: Created {obj.__class__.__name__} with values: {repr(obj)}")
            
    for obj in session.dirty:
        if isinstance(obj, (User, Consultation)):
            state = db.inspect(obj)
            attrs = []
            for attr in state.attrs:
                hist = attr.load_history()
                if hist.has_changes():
                    attrs.append(attr.key)
            # Log specifically if it was a soft-delete update
            if "is_deleted" in attrs and getattr(obj, "is_deleted") is True:
                logger.info(f"[AUDIT] SOFT-DELETE: Soft deleted {obj.__class__.__name__} ID={obj.id}")
            else:
                logger.info(f"[AUDIT] UPDATE: Modified {obj.__class__.__name__} ID={obj.id} fields={attrs}")
                
    for obj in session.deleted:
        if isinstance(obj, (User, Consultation)):
            logger.info(f"[AUDIT] HARD-DELETE: Hard deleted {obj.__class__.__name__} ID={obj.id}")
